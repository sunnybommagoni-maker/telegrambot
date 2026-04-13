import os
from huggingface_hub import InferenceClient

token = os.getenv("HF_TOKEN")
client = InferenceClient(token=token)

models = [
    "Qwen/Qwen2.5-72B-Instruct",
    "mistralai/Mistral-Nemo-Instruct-2407",
    "microsoft/Phi-3.5-mini-instruct"
]

for model in models:
    try:
        print(f"Testing {model}...")
        res = client.chat_completion(
            messages=[{"role": "user", "content": "Hello"}],
            model=model,
            max_tokens=10
        )
        print("Success:", res.choices[0].message.content)
    except Exception as e:
        print(f"Error: {e}")
