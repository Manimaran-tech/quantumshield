import os
import requests

print("Environment proxy variables:")
for k, v in os.environ.items():
    if "proxy" in k.lower() or "http" in k.lower():
        print(f"  {k} = {v}")

try:
    print("Testing GET to httpbin.org/get...")
    res = requests.get("https://httpbin.org/get", timeout=10)
    print("GET Status code:", res.status_code)
except Exception as e:
    print("GET Error:", e)

try:
    print("Testing GET to google.com...")
    res = requests.get("https://www.google.com", timeout=10)
    print("Google GET Status code:", res.status_code)
except Exception as e:
    print("Google GET Error:", e)
