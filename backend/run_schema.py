import os
import pymysql
from dotenv import load_dotenv

load_dotenv()

DB_USER = os.getenv('DB_USER')
DB_PASS = os.getenv('DB_PASSWORD_PLAIN')
DB_HOST = os.getenv('DB_HOST')
DB_NAME = os.getenv('DB_NAME')
DB_PORT = int(os.getenv('DB_PORT', '3306'))

sql_file = os.path.join('sql', 'architect_schema.sql')

conn = pymysql.connect(
    host=DB_HOST,
    user=DB_USER,
    password=DB_PASS,
    database=DB_NAME,
    port=DB_PORT,
    client_flag=pymysql.constants.CLIENT.MULTI_STATEMENTS
)

try:
    with open(sql_file, 'r', encoding='utf-8') as f:
        sql_content = f.read()
    
    with conn.cursor() as cursor:
        print(f"Executing {sql_file}...")
        cursor.execute(sql_content)
    conn.commit()
    print("✅ Schema applied successfully.")
finally:
    conn.close()
