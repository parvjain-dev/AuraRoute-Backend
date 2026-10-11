from fastapi import FastAPI
from sqladmin import Admin
from app.db.session import engine
from app.admin import PlaceAdmin, RankingAdmin,PipelineView,MapView
from app.core.config import settings

# Initialize core FastAPI application
app = FastAPI(title=settings.PROJECT_NAME, version="1.0.0")

# Initialize Admin Console and bind it to our PostgreSQL engine
admin = Admin(app, engine, title="Aura Route Admin Console")

# Register our database views
admin.add_view(PlaceAdmin)
admin.add_view(RankingAdmin)
admin.add_view(PipelineView)  
admin.add_view(MapView)

@app.get("/")
def health_check():
    return {
        "status": "online",
        "message": "Aura Route API is running.",
        "admin_console": "/admin"
    }