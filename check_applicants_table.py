import mysql.connector

# Connect to database
conn = mysql.connector.connect(
    host='localhost',
    user='root',
    password='',
    database='klsb_test'
)

cursor = conn.cursor()

# Check row count
cursor.execute('SELECT COUNT(*) FROM applicants')
count = cursor.fetchone()[0]
print(f'📊 Total applicants in DB: {count}')

# Show table structure
cursor.execute('DESCRIBE applicants')
print('\n🔍 Applicants table structure:')
print(f"{'Column':<25} {'Type':<25} {'Null':<8} {'Key':<8} {'Default':<15}")
print('-' * 90)
for row in cursor.fetchall():
    col_name, col_type, null, key, default, extra = row
    print(f"{col_name:<25} {col_type:<25} {null:<8} {key or '':<8} {str(default) or '':<15}")

# Check if phone column exists
cursor.execute("SHOW COLUMNS FROM applicants LIKE 'phone'")
phone_exists = cursor.fetchone()

if phone_exists:
    print('\n✅ phone column EXISTS')
else:
    print('\n❌ phone column MISSING')

cursor.close()
conn.close()
