import os
import pymysql
from dotenv import load_dotenv

load_dotenv()

DB_USER = os.getenv('DB_USER')
DB_PASS = os.getenv('DB_PASSWORD_PLAIN')
DB_HOST = os.getenv('DB_HOST')
DB_NAME = os.getenv('DB_NAME')
DB_PORT = int(os.getenv('DB_PORT', '3306'))

conn = pymysql.connect(
    host=DB_HOST,
    user=DB_USER,
    password=DB_PASS,
    database=DB_NAME,
    port=DB_PORT
)

try:
    with conn.cursor() as cursor:
        print("Columns in raw_google_map_drive_data:")
        cursor.execute("DESCRIBE raw_google_map_drive_data")
        for row in cursor.fetchall():
            print(row)
finally:
    conn.close()
