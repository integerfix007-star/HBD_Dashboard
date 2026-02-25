import pymysql

conn = pymysql.connect(host='127.0.0.1', user='root', password='darshit@1912', port=3306)
cursor = conn.cursor()

# Show databases
cursor.execute('SHOW DATABASES')
dbs = [r[0] for r in cursor.fetchall()]
print('Databases:', dbs)

# Create local_dashboard DB if not exists
cursor.execute('CREATE DATABASE IF NOT EXISTS local_dashboard')
print('Database local_dashboard ensured.')

# Create user if not exists
try:
    cursor.execute("CREATE USER 'local_dashboard'@'127.0.0.1' IDENTIFIED BY 'darshit@1912'")
    print('User created.')
except Exception as e:
    print(f'User may already exist: {e}')

try:
    cursor.execute("CREATE USER 'local_dashboard'@'localhost' IDENTIFIED BY 'darshit@1912'")
except Exception:
    pass

# Grant privileges
cursor.execute("GRANT ALL PRIVILEGES ON local_dashboard.* TO 'local_dashboard'@'127.0.0.1'")
cursor.execute("GRANT ALL PRIVILEGES ON local_dashboard.* TO 'local_dashboard'@'localhost'")
cursor.execute("FLUSH PRIVILEGES")
print('Privileges granted.')

conn.close()
print('Done!')
