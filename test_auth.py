from dotenv import load_dotenv
load_dotenv()
from src.utils.auth_helper import get_llm

def test_auth():
    print("Testing Google Gemini LLM Authentication...")
    try:
        # Try gemini-pro
        llm = get_llm(model_name="gemini-2.0-flash")
        response = llm.invoke("Hello, are you working?")
        print(f" Success! Response: {response.content}")
    except Exception as e:
        print(f" Failed: {e}")

if __name__ == "__main__":
    test_auth()
