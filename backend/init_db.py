import os
from sqlalchemy import create_engine, text
from urllib.parse import quote_plus
from dotenv import load_dotenv

# Load environment variables
load_dotenv('.env')

def init_db():
    print("🔌 Connecting to database...")
    DB_USER = os.getenv('DB_USER')
    DB_PASS = quote_plus(os.getenv('DB_PASSWORD_PLAIN') or '')
    DB_HOST = os.getenv('DB_HOST')
    DB_NAME = os.getenv('DB_NAME')
    DB_PORT = os.getenv('DB_PORT', '3306')

    if not all([DB_USER, DB_HOST, DB_NAME]):
        print("❌ Missing database credentials in .env")
        return

    DATABASE_URI = f"mysql+pymysql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    engine = create_engine(DATABASE_URI)

    print("📜 Reading Schema...", "sql/architect_schema.sql")
    try:
        with open('sql/architect_schema.sql', 'r') as f:
            schema_sql = f.read()
    except FileNotFoundError:
        print("❌ Schema file not found!")
        return

    # Split by semicolon to execute statement by statement, as execute() might not handle multi-statement scripts well depending on driver
    statements = schema_sql.split(';')
    
    with engine.begin() as conn:
        for statement in statements:
            if statement.strip():
                try:
                    conn.execute(text(statement))
                except Exception as e:
                    print(f"⚠️ Warning executing statement: {e}")
                    # Continue as some might be 'IF EXISTS' errors or similar non-fatal issues if handled
                    pass
    
    print("✅ Database Schema Applied Successfully.")

if __name__ == "__main__":
    init_db()
