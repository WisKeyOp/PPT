"""
Singleton vault client with cached credentials.
Ensures vault key is fetched exactly once per pipeline run.
"""
import os
import threading
from typing import Optional
from azure.identity import ClientSecretCredential, DefaultAzureCredential
from azure.keyvault.secrets import SecretClient


class VaultClient:
    """Thread-safe singleton for vault credential caching."""
    
    _instance: Optional['VaultClient'] = None
    _lock = threading.Lock()
    _api_key: Optional[str] = None
    _fetch_count = 0  # For testing/debugging
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    @classmethod
    def get_api_key(cls) -> str:
        """Get cached API key, fetching from vault if not yet cached."""
        instance = cls()
        
        if instance._api_key is None:
            with cls._lock:
                if instance._api_key is None:  # Double-check
                    print("🔑 Fetching vault key (first call)...")
                    instance._api_key = instance._fetch_from_vault()
                    cls._fetch_count += 1
        else:
            print("♻️  Reusing cached vault key")
        
        return instance._api_key
    
    def _fetch_from_vault(self) -> str:
        """Fetch secret from Azure Key Vault."""
        vault_url = os.getenv("KEYVAULTURL")
        tenant_id = os.getenv("TENANT_ID")
        client_id = os.getenv("CLIENT_ID")
        client_secret = os.getenv("CLIENT_SECRET")
        target_secret_name = os.getenv("AZURE_SECRET_NAME", "gpt-4-turbo-key1")
        
        if not vault_url:
            raise ValueError("❌ Missing KEYVAULTURL in .env")
        
        # Authenticate
        if client_id and client_secret and tenant_id:
            credential = ClientSecretCredential(
                tenant_id=tenant_id,
                client_id=client_id,
                client_secret=client_secret
            )
        else:
            credential = DefaultAzureCredential()
        
        # Fetch secret
        vault_client = SecretClient(vault_url=vault_url, credential=credential)
        retrieved_secret = vault_client.get_secret(target_secret_name)
        
        return retrieved_secret.value
    
    @classmethod
    def reset(cls):
        """Reset singleton (for testing only)."""
        with cls._lock:
            cls._instance = None
            cls._api_key = None
            cls._fetch_count = 0
