import uvicorn
from app.db.database import engine

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)

    try:
        conn = engine.connect()
        conn.close()
    except Exception as e:
        print(f"Error connecting to the database: {e}")
        exit(1)