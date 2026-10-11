import requests
from sqlalchemy.dialects.postgresql import insert
from app.db.session import SessionLocal
from app.models.place import CanonicalPlace, PlaceRanking

OVERPASS_URL = "http://overpass-api.de/api/interpreter"

def fetch_osm_restaurants(bbox: str) -> list:
    """Fetches restaurant nodes from OSM for a given bounding box."""
    query = f"""
    [out:json][timeout:25];
    node["amenity"="restaurant"]({bbox});
    out body;
    """
    
    # Add a User-Agent to identify our app to the OSM servers
    headers = {
        "User-Agent": "AuraRouteEnterpriseBackend/1.0 (Contact: localdev@auraroute)",
        "Accept": "*/*"
    }
    
    response = requests.post(OVERPASS_URL, data={'data': query}, headers=headers)
    response.raise_for_status()
    return response.json().get("elements", [])

def ingest_osm_data(elements: list) -> int:
    """Inserts OSM elements into the database safely. Returns number inserted."""
    db = SessionLocal()
    inserted_count = 0
    
    try:
        for el in elements:
            name = el.get("tags", {}).get("name")
            if not name:
                continue # Skip unnamed places
                
            place_id = f"osm_{el['id']}"
            lat, lon = el["lat"], el["lon"]
            geom_wkt = f"SRID=4326;POINT({lon} {lat})"
            
            # UPSERT: Insert or update if it exists
            stmt = insert(CanonicalPlace).values(
                id=place_id,
                name=name,
                category="restaurant",
                geom=geom_wkt,
                latitude=lat,
                longitude=lon,
                source_provider="OSM"
            ).on_conflict_do_nothing(index_elements=['id'])
            
            result = db.execute(stmt)
            
            if result.rowcount > 0:
                # Create a default blank ranking entry
                ranking_stmt = insert(PlaceRanking).values(
                    place_id=place_id,
                    base_rating=0.0,
                    is_curated_seed=False
                ).on_conflict_do_nothing(index_elements=['place_id'])
                db.execute(ranking_stmt)
                inserted_count += 1
                
        db.commit()
        return inserted_count
        
    except Exception as e:
        db.rollback()
        print(f"Database error: {e}")
        return 0
    finally:
        db.close()