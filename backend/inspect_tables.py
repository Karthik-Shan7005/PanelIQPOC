from database import run_query

print("=" * 60)
print("PanelIQ — Core Views Inspector")
print("=" * 60)

views_to_inspect = [
    "KPISurveyData",
    "KPIsurveydataExternal",
    "KPIReportProjectData",
]

for view in views_to_inspect:
    print(f"\n{'=' * 60}")
    print(f"📋 View: {view}")
    print(f"{'=' * 60}")
    
    # Get column names and data types
    result = run_query(f"""
        SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_NAME = '{view}'
        ORDER BY ORDINAL_POSITION
    """)
    
    if result["success"] and result["row_count"] > 0:
        print(f"   Total Columns: {result['row_count']}")
        print(f"\n   {'Column Name':<40} {'Data Type':<15} {'Nullable'}")
        print(f"   {'-'*40} {'-'*15} {'-'*8}")
        for row in result["rows"]:
            print(f"   {str(row[0]):<40} {str(row[1]):<15} {row[2]}")
    else:
        print(f"   ⚠️ No columns found")

    # Get sample rows
    print(f"\n   📊 Sample Data (Top 3 rows):")
    sample = run_query(f"SELECT TOP 3 * FROM {view}")
    if sample["success"] and sample["row_count"] > 0:
        print(f"   Columns: {sample['columns']}")
        for row in sample["rows"]:
            print(f"   {row}")
    else:
        print(f"   ⚠️ No data: {sample.get('error','')}")

print("\n" + "=" * 60)
print("Inspection Complete!")
print("=" * 60)