from database import run_query

print("=" * 60)
print("PanelIQ — View Structure Inspector")
print("=" * 60)

# List ALL Views in the database
print("\n📋 All Views in KpiReports Database:")
result = run_query("""
    SELECT TABLE_NAME
    FROM INFORMATION_SCHEMA.VIEWS
    ORDER BY TABLE_NAME
""")
if result["success"]:
    for row in result["rows"]:
        print(f"   {row[0]}")
else:
    print(f"❌ Error: {result['error']}")

print("\n" + "=" * 60)