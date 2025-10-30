import mysql.connector

try:
    conn = mysql.connector.connect(
        host='localhost',
        user='root',
        password='',
        database='klsb_test'
    )
    cursor = conn.cursor()
    
    # Check table structure
    cursor.execute('DESCRIBE job_listings')
    print('Job Listings Table Structure:')
    for row in cursor.fetchall():
        print(f'  {row[0]} - {row[1]}')
    
    # Check if we can insert
    print('\nAttempting test insert...')
    cursor.execute("""
        INSERT INTO job_listings (title, department, type, location, summary, points, posted_date, is_active)
        VALUES ('Test Job', 'Engineering', 'Full-time', 'Test Location', 'Test Summary', 'Test Points', 'Recently posted', 1)
    """)
    conn.commit()
    print('✅ Insert successful!')
    
    # Get the last inserted ID
    cursor.execute('SELECT LAST_INSERT_ID()')
    last_id = cursor.fetchone()[0]
    print(f'Last inserted ID: {last_id}')
    
    # Delete the test record
    cursor.execute(f'DELETE FROM job_listings WHERE id = {last_id}')
    conn.commit()
    print('✅ Test record deleted')
    
    cursor.close()
    conn.close()
    print('\n✅ Database test completed successfully!')
    
except Exception as e:
    print(f'❌ Error: {e}')
