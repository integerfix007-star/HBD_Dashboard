from sqlalchemy import text, create_engine
import os
from dotenv import load_dotenv
load_dotenv()
engine = create_engine(f'mysql+mysqlconnector://{os.getenv("DB_USER")}:{os.getenv("DB_PASSWORD")}@{os.getenv("DB_HOST")}/{os.getenv("DB_NAME")}')
tables = engine.connect().execute(text('SHOW TABLES')).fetchall()
for t in tables:
    print(t[0])
