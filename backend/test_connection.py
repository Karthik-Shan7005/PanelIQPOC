from database import get_connection, run_query

print("=" * 50)
print("PanelIQ — SQL Server Connection Test")
print("=" * 50)

# Test 1 — Basic connection
print("\n🔄 Test 1: Connecting to SQL Server...")
try:
    conn = get_connection()
    print("✅ Connection successful!")
    conn.close()
except Exception as e:
    print(f"❌ Connection failed!")
    print(f"   Error: {e}")
    print("\n💡 Things to check:")
    print("   1. DB_SERVER in .env — should be 10.20.30.12,1433")
    print("   2. DB_NAME — exact database name")
    print("   3. DB_USER and DB_PASSWORD — same as SSMS login")
    exit()

# Test 2 — List available databases
print("\n🔄 Test 2: Checking database access...")
result = run_query("SELECT DB_NAME() AS CurrentDatabase")
if result["success"]:
    print(f"✅ Connected to database: {result['rows'][0][0]}")
else:
    print(f"❌ Failed: {result['error']}")

# Test 3 — Check Survey table exists
print("\n🔄 Test 3: Checking Survey table...")
result = run_query("""
    SELECT TOP (5) panelistid, pointbalance from KPIPanelist
    """)
if result["success"]:
    print(f"✅ Survey table found! Sample rows:")
    print(f"   Columns: {result['columns']}")
    for row in result["rows"]:
        print(f"   {row}")
else:
    print(f"❌ Survey table error: {result['error']}")

# Test 4 — Check Projects table
print("\n🔄 Test 4: Checking Projects table...")
result = run_query("""
    SELECT TOP (5)
        ProjectId,
        ProjectName,
        CountryName,
        ClientName,
        StatusName
    FROM KPIReportProjectData
""")
if result["success"]:
    print(f"✅ Projects table found! Sample rows:")
    for row in result["rows"]:
        print(f"   {row}")
else:
    print(f"❌ Projects table error: {result['error']}")

# Test 5 — Check Vendor table
print("\n🔄 Test 5: Checking Vendor table...")
result = run_query("""
    SELECT TOP (5) sampleid, vendorname FROM kpiexternalsample
""")
if result["success"]:
    print(f"✅ Vendor table found! Sample rows:")
    for row in result["rows"]:
        print(f"   {row}")
else:
    print(f"❌ Vendor table error: {result['error']}")

print("\n" + "=" * 50)
print("Connection test complete!")
print("=" * 50)