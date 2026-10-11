from app.db.base import Base
from app.db.session import engine
from app.models.place import CanonicalPlace, PlaceRanking

def init_db():
    print("Creating PostGIS spatial tables in PostgreSQL...")
    Base.metadata.create_all(bind=engine)
    print("Database tables initialized successfully!")

if __name__ == "__main__":
    init_db()