from backend.app.db.session import engine, Base
import backend.app.models  # Ensure all models are registered

def init_db():
    print("Creating all database tables...")
    Base.metadata.create_all(bind=engine)
    print("Database tables initialized successfully.")

if __name__ == "__main__":
    init_db()

