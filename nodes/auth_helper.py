import os
from azure.identity import ClientSecretCredential, DefaultAzureCredential
from azure.keyvault.secrets import SecretClient
from langchain_openai import AzureChatOpenAI
from dotenv import load_dotenv

load_dotenv()

def get_azure_credentials():
    # 1. Load Config
    vault_url = os.getenv("KEYVAULTURL")
    tenant_id = os.getenv("TENANT_ID")
    client_id = os.getenv("CLIENT_ID")
    client_secret = os.getenv("CLIENT_SECRET")
    
    target_secret_name = os.getenv("AZURE_SECRET_NAME", "gpt-4-turbo-key1")

    if not vault_url:
        raise ValueError("❌ Missing KEYVAULTURL in .env")

    # 2. Authenticate
    if client_id and client_secret and tenant_id:
        print(f"🔐 Authenticating as Service Principal...")
        credential = ClientSecretCredential(
            tenant_id=tenant_id,
            client_id=client_id,
            client_secret=client_secret
        )
    else:
        credential = DefaultAzureCredential()

    # 3. Connect to Vault
    client = SecretClient(vault_url=vault_url, credential=credential)
    
    # 4. Fetch the Secret
    try:
        print(f"🔑 Fetching secret: '{target_secret_name}' from Vault...")
        retrieved_secret = client.get_secret(target_secret_name)
        return retrieved_secret.value
    except Exception as e:
        print(f"❌ ERROR: Secret '{target_secret_name}' not found in {vault_url}")
        raise e

def get_llm(deployment_name="gpt-4-turbo", temperature=0):
    api_key = get_azure_credentials()
    
    endpoint = os.getenv("APIBASE_o")
    api_version = os.getenv("VERSION_o", "2024-02-15-preview")
    
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
