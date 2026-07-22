import os
import requests

api_key = "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"
headers = {
    "Authorization": f"Bearer {api_key}",
}

try:
    response = requests.get("https://integrate.api.nvidia.com/v1/models", headers=headers)
    if response.status_code == 200:
        models = response.json().get("data", [])
        print("ALL AVAILABLE MODELS:")
        for model in sorted(models, key=lambda x: x.get("id", "")):
            print(model.get("id"))
    else:
        print(f"Error {response.status_code}: {response.text}")
except Exception as e:
    print(f"Exception: {e}")
