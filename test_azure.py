from src.utils.auth_helper import get_llm
import os
from dotenv import load_dotenv

# Force reload of .env file
load_dotenv(override=True)

print("--- Testing Azure OpenAI Integration ---")
print("Environment Variables Check:")
for var in ["KEYVAULTURL", "TENANT_ID", "CLIENT_ID", "CLIENT_SECRET", "APIBASE_o", "VERSION_o"]:
    val = os.getenv(var)
    status = "OK" if val else "MISSING"
    # Mask secrets
    if val and var in ["CLIENT_SECRET"]:
        val = "***"
    elif val and len(val) > 10:
        val = val[:5] + "..."
    print(f"{var}: {status} ({val})")

try:
    print("\nInitializing LLM...")
    llm = get_llm(deployment_name="gpt-4", temperature=0)
    print("LLM Initialized. Sending request...")
    response = llm.invoke("Hello, Azure! Are you working?")
    print("\nSuccess! Response:")
    print(response.content)
except Exception as e:
    print("\nText Generation Failed:")
    print(e)
