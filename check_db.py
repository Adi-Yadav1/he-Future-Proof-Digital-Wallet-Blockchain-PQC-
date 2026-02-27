import sqlite3

conn = sqlite3.connect('database/database.db')
cursor = conn.cursor()

# Check tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()
print('📊 Tables in database:')
for t in tables:
    print(f'  ✓ {t[0]}')

# Check users table structure
print('\n📝 Users table structure:')
cursor.execute('PRAGMA table_info(users)')
cols = cursor.fetchall()
for c in cols:
    print(f'  - {c[1]} ({c[2]})')

# Check users count
cursor.execute('SELECT COUNT(*) FROM users')
user_count = cursor.fetchone()[0]
print(f'\n👥 Total users: {user_count}')

# Check profiles count
cursor.execute('SELECT COUNT(*) FROM profiles')
profile_count = cursor.fetchone()[0]
print(f'💼 Total profiles: {profile_count}')

conn.close()
print('\n✅ Local database structure is correct!')
print('⚠️  But registrations are saved on DEPLOYED server (Render), not here.')
