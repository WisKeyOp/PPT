import os
from functools import lru_cache
from azure.identity import ClientSecretCredential, DefaultAzureCredential
from azure.keyvault.secrets import SecretClient
from langchain_openai import AzureChatOpenAI, ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_google_genai import ChatGoogleGenerativeAI
from src.utils.vault_client import VaultClient

@lru_cache(maxsize=4)
def get_llm(deployment_name="gpt-4-turbo", temperature=0):
    """
    Get LLM instance based on available environment variables.
    Supports: OpenAI, Azure OpenAI, Anthropic Claude, Google Gemini
    """
    # Check for different LLM providers in order of preference
    
    # 1. Try OpenAI (direct API)
    if os.getenv("OPENAI_API_KEY"):
        print("🤖 Using OpenAI API")
        return ChatOpenAI(
            model=os.getenv("OPENAI_MODEL", "gpt-4-turbo-preview"),
            temperature=temperature,
            api_key=os.getenv("OPENAI_API_KEY")
        )
    
    # 2. Try Anthropic Claude
    if os.getenv("ANTHROPIC_API_KEY"):
        print("🤖 Using Anthropic Claude")
        return ChatAnthropic(
            model=os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-20241022"),
            temperature=temperature,
            api_key=os.getenv("ANTHROPIC_API_KEY")
        )
    
    # 3. Try Google Gemini
    if os.getenv("GOOGLE_API_KEY"):
        print("🤖 Using Google Gemini")
        return ChatGoogleGenerativeAI(
            model=os.getenv("GOOGLE_MODEL", "gemini-pro"),
            temperature=temperature,
            google_api_key=os.getenv("GOOGLE_API_KEY")
        )
    
    # 4. Try Azure OpenAI (with cached vault key)
    if os.getenv("KEYVAULTURL"):
        print("🤖 Using Azure OpenAI")
        api_key = VaultClient.get_api_key()  # ← USES SINGLETON CACHE
        
        endpoint = os.getenv("APIBASE_o")
        api_version = os.getenv("VERSION_o", "2024-02-15-preview")
        
        # Use the specific deployment name from your Azure setup
        real_deployment = os.getenv("AZURE_DEPLOYMENT_NAME", deployment_name)

        if not endpoint:
            raise ValueError("❌ Missing APIBASE_o in .env")

        return AzureChatOpenAI(
            azure_deployment=real_deployment,
            api_version=api_version,
            azure_endpoint=endpoint,
            api_key=api_key,
            temperature=temperature
        )
    
    # No API keys found
    raise ValueError(
        "❌ No LLM API keys found in .env file.\n"
        "Please set one of: OPENAI_API_KEY, ANTHROPIC_API_KEY, GOOGLE_API_KEY, or KEYVAULTURL (for Azure)"
    )