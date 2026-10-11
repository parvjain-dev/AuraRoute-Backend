from sqladmin import ModelView
from app.models.place import CanonicalPlace, PlaceRanking
from ingestion.uniqueness_ingestor import generate_and_merge_unique_stops
from sqladmin import BaseView, expose
from starlette.responses import RedirectResponse
from starlette.requests import Request
from ingestion.osm_ingestor import fetch_osm_restaurants, ingest_osm_data
import json
from sqlalchemy import select
from app.db.session import SessionLocal
from app.models.place import CanonicalPlace
class PlaceAdmin(ModelView, model=CanonicalPlace):
    name = "Canonical Place"
    name_plural = "Canonical Places"
    icon = "fa-solid fa-map-pin"
    
    # Columns to display in the UI table
    column_list = [
        CanonicalPlace.id, 
        CanonicalPlace.name, 
        CanonicalPlace.category, 
        CanonicalPlace.source_provider
    ]
    # Adds a search bar for these specific fields
    column_searchable_list = [CanonicalPlace.name, CanonicalPlace.id]
    column_sortable_list = [CanonicalPlace.name, CanonicalPlace.created_at]

class RankingAdmin(ModelView, model=PlaceRanking):
    name = "Place Ranking"
    name_plural = "Place Rankings"
    icon = "fa-solid fa-star"
    
    column_list = [
        PlaceRanking.place_id, 
        PlaceRanking.is_curated_seed, 
        PlaceRanking.uniqueness_score, 
        PlaceRanking.base_rating,
        PlaceRanking.ideal_meal
    ]
    column_sortable_list = [PlaceRanking.uniqueness_score, PlaceRanking.base_rating]



class PipelineView(BaseView):
    name = "Data Pipelines"
    icon = "fa-solid fa-network-wired"

    @expose("/pipelines", methods=["GET"])
    async def pipelines_page(self, request: Request):
        message = request.query_params.get("message")
        # Ensure 'await' is here and 'request' is the first parameter
        return await self.templates.TemplateResponse(
            request,
            "pipelines.html",
            context={"request": request, "message": message},
        )

    @expose("/run-osm", methods=["POST"])
    async def run_osm_pipeline(self, request: Request):
        test_bbox = "12.9000,77.5500,12.9500,77.6500"
        
        osm_data = fetch_osm_restaurants(test_bbox)
        if osm_data:
            inserted = ingest_osm_data(osm_data)
            msg = f"Success! Fetched {len(osm_data)} raw nodes. Inserted {inserted} new restaurants."
        else:
            msg = "No data found or pipeline failed."
            
        return RedirectResponse(url=f"/admin/pipelines?message={msg}", status_code=303)
    @expose("/run-llm", methods=["POST"])
    async def run_llm_pipeline(self, request: Request):
        stats = generate_and_merge_unique_stops("Bengaluru", "Gokarna")
        
        if "error" in stats:
            msg = f"LLM Pipeline Failed: {stats['error']}"
        else:
            msg = (f"LLM Success! Processed {stats.get('total_processed', 0)} curated stops.\n"
                   f"Matched & Updated {stats.get('updated_osm', 0)} existing OSM places.\n"
                   f"Created {stats.get('created_new', 0)} new LLM-only places.")
            
        return RedirectResponse(url=f"/admin/pipelines?message={msg}", status_code=303)

class MapView(BaseView):
    name = "Spatial Map"
    icon = "fa-solid fa-map-location-dot"

    @expose("/map", methods=["GET"])
    async def map_page(self, request: Request):
        db = SessionLocal()
        try:
            # Fetch all places and their coordinates
            stmt = select(CanonicalPlace.name, CanonicalPlace.latitude, CanonicalPlace.longitude, CanonicalPlace.source_provider)
            results = db.execute(stmt).all()
            
            # Format as a list of dictionaries for JSON
            places_data = [
                {
                    "name": row.name, 
                    "lat": row.latitude, 
                    "lon": row.longitude, 
                    "source": row.source_provider
                }
                for row in results if row.latitude and row.longitude
            ]
        finally:
            db.close()

        return await self.templates.TemplateResponse(
            request,
            "map.html",
            {"request": request, "places_json": json.dumps(places_data)},
        )