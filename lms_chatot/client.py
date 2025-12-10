import requests

API_URL = "http://localhost:8000/inference"

def inference(model, messages, temperature=0.7, max_tokens=1000):
    response = requests.post(API_URL, json={
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens
    })
    response.raise_for_status()
    return response.json()

if __name__ == "__main__":
    result = inference(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": "Hello, how are you?"}]
    )
    print(f"Response: {result['content']}")
    print(f"Model: {result['model']}")
    print(f"Usage: {result['usage']}")
