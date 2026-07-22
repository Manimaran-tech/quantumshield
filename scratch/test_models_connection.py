import requests
import json

api_key = "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"
headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}

def test_model(model_name):
    payload = {
        "model": model_name,
        "messages": [{"role": "user", "content": "Hello. Identify your model name."}],
        "temperature": 0.1,
        "max_tokens": 50
    }
    try:
        response = requests.post(
            "https://integrate.api.nvidia.com/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=10
        )
        if response.status_code == 200:
            print(f"SUCCESS: {model_name} works! Response: {response.json()['choices'][0]['message']['content'].strip()}")
            return True
        else:
            print(f"FAILED: {model_name} failed with status {response.status_code}: {response.text}")
            return False
    except Exception as e:
        print(f"FAILED: {model_name} error: {e}")
        return False

models_to_test = [
    "writer/palmyra-med-70b",
    "writer/palmyra-med-70b-32k",
    "meta/llama-3.1-70b-instruct",
    "meta/llama-3.1-8b-instruct",
    "nvidia/llama-3.1-nemotron-70b-instruct"
]

for m in models_to_test:
    test_model(m)
