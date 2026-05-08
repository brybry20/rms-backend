import requests

endpoints = [
    '/api/approver/all-rma',
    '/api/approver/stats',
    '/api/authorizer/all-rma',
    '/api/authorizer/stats'
]

for ep in endpoints:
    try:
        r = requests.get(f'http://localhost:10000{ep}')
        print(f"Endpoint {ep} - Status: {r.status_code}")
        # print(f"Response: {r.text[:100]}")
    except Exception as e:
        print(f"Endpoint {ep} - Error: {e}")

