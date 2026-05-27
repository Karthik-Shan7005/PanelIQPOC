import requests

BASE = "http://127.0.0.1:8000"

print("=" * 60)
print("PanelIQ — API Test")
print("=" * 60)

# Test 1 — Health check
print("\n🔄 Test 1: Health Check...")
res = requests.get(f"{BASE}/health")
print(f"✅ {res.json()}")

# Test 2 — Ask a question
print("\n🔄 Test 2: Asking a question...")
payload = {"question": "Show me completes by market for last 6 months"}
res = requests.post(f"{BASE}/ask", json=payload)
data = res.json()

print(f"\n✅ Success: {data['success']}")
print(f"📝 SQL Generated: {data['sql'][:120]}...")
print(f"📊 Columns: {data['columns']}")
print(f"📋 Row Count: {data['row_count']}")
print(f"\n📋 Top 5 Results:")
for row in data['rows'][:5]:
    print(f"   {row}")
print(f"\n💡 Summary: {data['summary']}")
print(f"❓ Follow-up: {data['followup']}")
print(f"📈 Chart Type: {data['chart_type']}")

# Test 3 — Suggestions
print("\n🔄 Test 3: Getting prompt suggestions...")
payload = {"partial": "india"}
res = requests.post(f"{BASE}/suggest", json=payload)
data = res.json()
print(f"✅ Suggestions:")
for s in data['suggestions']:
    print(f"   → {s}")

print("\n" + "=" * 60)
print("API Test Complete!")
print("=" * 60)