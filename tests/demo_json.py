import asyncio
import httpx
import json

async def run_demo():
    url = "http://localhost:8002/intent"
    
    test_inputs=json.load(open("tests/tests.json"))["test_cases"]
    
    async with httpx.AsyncClient() as client:
        print(f"=== Testing API at {url} ===\n")
        
        for text in test_inputs:
            print(f"🔹 Input: '{text['input']}'")
            print(f"🔹 Expected Intent: '{text['expected_intent']}'")
            try:
                response = await client.post(url, json={"text": text['input']})
                if response.status_code == 200:
                    data = response.json()
                    print(json.dumps(data, indent=2))
                else:
                    print(f"❌ Error: {response.status_code} - {response.text}")
            except Exception as e:
                print(f"❌ Connection Failed: {e}")
            print("\n" + "-"*40 + "\n")

if __name__ == "__main__":
    asyncio.run(run_demo())
