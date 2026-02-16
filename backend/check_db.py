from sqlalchemy import create_engine, text
import os
from urllib.parse import quote_plus
from dotenv import load_dotenv

load_dotenv()
db_user = os.getenv('DB_USER')
db_pass = quote_plus(os.getenv('DB_PASSWORD_PLAIN') or '')
db_host = os.getenv('DB_HOST')
db_name = os.getenv('DB_NAME')
db_port = os.getenv('DB_PORT')

engine = create_engine(f'mysql+pymysql://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}')

with engine.connect() as conn:
    print('Threads connected:', conn.execute(text('SHOW STATUS LIKE "Threads_connected"')).fetchone())
    processes = conn.execute(text('SHOW FULL PROCESSLIST')).fetchall()
    print('Total processes:', len(processes))
    for p in processes:
        if p[4] != 'Sleep':
            print(f"ID: {p[0]}, User: {p[1]}, Host: {p[2]}, DB: {p[3]}, Command: {p[4]}, Time: {p[5]}, State: {p[6]}, Info: {p[7]}")
