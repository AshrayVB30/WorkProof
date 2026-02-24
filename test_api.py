import requests
import json
url = "http://localhost:8000/api/scrape"
payload = {"url": "http://109.199.108.38:2069/?q=QUNUQVNUeHg4MGltZzAwMTAuanBlZzs1NzU7d1NkZjN0N24"}
headers = {"Content-Type": "application/json"}
try:
    print(f"Sending POST request to {url}...")
    response = requests.post(url, json=payload, headers=headers, timeout=300)
    print(f"Status Code: {response.status_code}")
    print("Response JSON:")
    print(json.dumps(response.json(), indent=2))
except Exception as e:
    print(f"Error: {e}")
