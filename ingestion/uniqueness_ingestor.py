import json
import requests
import uuid
from pathlib import Path
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy import select
from app.db.session import SessionLocal
from app.models.place import CanonicalPlace, PlaceRanking

OLLAMA_URL = "http://localhost:11434/api/generate"

# Point directly to your prompt file in the root folder
BASE_DIR = Path(__file__).resolve().parent.parent
PROMPT_PATH = BASE_DIR / "seed_list_skill.md"

def get_llm_prompt(source: str, destination: str) -> str:
    """Reads the saved skill file and appends the specific route request."""
    if not PROMPT_PATH.exists():
        raise FileNotFoundError(f"Missing prompt file at: {PROMPT_PATH}")
        
    with open(PROMPT_PATH, "r", encoding="utf-8") as f:
        base_prompt = f.read()
        
    execution_command = (
        f"\n\nExecute the road-trip-seed-list workflow for the route from {source} to {destination}. "
        "Respond STRICTLY in JSON format with a 'seed_stops' array containing objects with keys: "
        "name, location, worth_it_score, ideal_meal."
    )
    return base_prompt + execution_command

def generate_and_merge_unique_stops(source: str, destination: str) -> dict:
    """Calls local Llama 3.1 and merges results with the OSM database."""
    try:
        full_prompt = get_llm_prompt(source, destination)
    except Exception as e:
        return {"error": str(e)}
    
    payload = {
        "model": "llama3.1",
        "prompt": full_prompt,
        "format": "json",
        "stream": False,
        "options": {"temperature": 0.2}
    }
    
    try:
        response = requests.post(OLLAMA_URL, json=payload, timeout=300)
        response.raise_for_status()
        
        data = json.loads(response.json().get("response", "{}"))
        stops = data.get("seed_stops", [])
    except Exception as e:
        return {"error": str(e)}

    db = SessionLocal()
    stats = {"updated_osm": 0, "created_new": 0, "total_processed": len(stops)}
    
    try:
        for stop in stops:
            name = stop.get("name")
            if not name:
                continue
            
            stmt = select(CanonicalPlace).where(CanonicalPlace.name.ilike(f"%{name}%")).limit(1)
            existing_place = db.execute(stmt).scalar_one_or_none()
            
            if existing_place:
                place_id = existing_place.id
                stats["updated_osm"] += 1
            else:
                place_id = f"llm_{uuid.uuid4().hex[:8]}"
                geom_wkt = "SRID=4326;POINT(0 0)"
                
                new_place = insert(CanonicalPlace).values(
                    id=place_id,
                    name=name,
                    category="restaurant",
                    geom=geom_wkt,
                    latitude=0.0,
                    longitude=0.0,
                    source_provider="LLM_CURATED"
                ).on_conflict_do_nothing()
                db.execute(new_place)
                stats["created_new"] += 1
            
            ranking_stmt = insert(PlaceRanking).values(
                place_id=place_id,
                is_curated_seed=True,
                uniqueness_score=stop.get("worth_it_score", 0),
                ideal_meal=stop.get("ideal_meal", "")
            ).on_conflict_do_update(
                index_elements=['place_id'],
                set_={
                    "is_curated_seed": True,
                    "uniqueness_score": stop.get("worth_it_score", 0),
                    "ideal_meal": stop.get("ideal_meal", "")
                }
            )
            db.execute(ranking_stmt)
            
        db.commit()
        return stats
    finally:
        db.close()