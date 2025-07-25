"""
Module for managing different LLM and embedding model providers.
This allows easy swapping between different model providers (OpenAI, Vertex AI, etc.)
"""
import os
import json
from typing import Dict, Any, Optional, List
from dotenv import load_dotenv

from langchain.schema import Document
from langchain.embeddings.base import Embeddings
from langchain.chat_models.base import BaseChatModel

# Providers
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_google_vertexai import VertexAI, VertexAIEmbeddings
import google.auth
from google.oauth2 import service_account

# Import config manager
from config_manager import config

# Explicitly reload config to ensure latest values are used
config.load_config()

# Load environment variables (only for .env file, not for config.yaml)
load_dotenv()

# Dictionary of available LLM providers
LLM_PROVIDERS = {
    "openai": {
        "name": "OpenAI",
        "description": "OpenAI GPT models (requires API key)"
    },
    "vertexai": {
        "name": "Vertex AI",
        "description": "Google Cloud Vertex AI models (requires service account)"
    }
}

# Dictionary of available embedding providers
EMBEDDING_PROVIDERS = {
    "openai": {
        "name": "OpenAI",
        "description": "OpenAI embedding models (requires API key)"
    },
    "vertexai": {
        "name": "Vertex AI",
        "description": "Google Cloud Vertex AI embedding models (requires service account)"
    }
}

def get_embeddings_model(provider: str = "openai", model_name: Optional[str] = None) -> Embeddings:
    """
    Get an embeddings model based on the specified provider.
    
    Args:
        provider: The provider to use ("openai", "vertexai")
        model_name: Optional model name for the specified provider
        
    Returns:
        An initialized embeddings model
    """
    provider = provider.lower()

    print(f"Provider: {provider}")
    print(f"Model name: {model_name}")
    
    if provider == "openai":
        model = model_name or config.get_provider_default_model("openai", "embedding") or "text-embedding-3-large"
        openai_api_key = config.get_openai_api_key() or os.getenv("OPENAI_API_KEY")
        if not openai_api_key:
            raise ValueError("OpenAI API key not found. Please set it in config.yaml or as an environment variable.")
        
        try:
            return OpenAIEmbeddings(model=model, openai_api_key=openai_api_key)
        except Exception as e:
            raise ConnectionError(f"Failed to initialize OpenAI embeddings: {str(e)}")
        
    elif provider == "vertexai":
        # Get Vertex AI configuration
        model = model_name or config.get_provider_default_model("vertexai", "embedding") or "textembedding-gecko@latest"
        project = config.get("models.provider_defaults.vertexai.project")
        region = config.get("models.provider_defaults.vertexai.region") or "us-central1"
        
        # Get service account path
        service_account_path = config.get("models.defaults.google_service_account_path")
        
        # Authenticate with Google Cloud
        if service_account_path:
            credentials = service_account.Credentials.from_service_account_file(
                service_account_path,
                scopes=["https://www.googleapis.com/auth/cloud-platform"]
            )
        else:
            # Use default credentials if no service account file is provided
            credentials, _ = google.auth.default()
        
        # Initialize Vertex AI embeddings
        return VertexAIEmbeddings(
            model_name=model,
            project=project,
            location=region,
            credentials=credentials
        )
            
    else:
        raise ValueError(f"Unsupported embedding provider: {provider}. Available providers: {list(EMBEDDING_PROVIDERS.keys())}")

def get_llm_model(provider: str = "openai", model_name: Optional[str] = None, temperature: float = 0) -> BaseChatModel:
    """
    Get a language model based on the specified provider.
    
    Args:
        provider: The provider to use ("openai", "vertexai")
        model_name: Optional model name for the specified provider
        temperature: Temperature parameter for text generation
        
    Returns:
        An initialized language model
    """
    provider = provider.lower()
    
    if provider == "openai":
        model = model_name or config.get_provider_default_model("openai", "llm") or "gpt-4o-mini"
        openai_api_key = config.get_openai_api_key() or os.getenv("OPENAI_API_KEY")
        if not openai_api_key:
            raise ValueError("OpenAI API key not found. Please set it in config.yaml or as an environment variable.")
        return ChatOpenAI(model=model, temperature=temperature, openai_api_key=openai_api_key)
        
    elif provider == "vertexai":
        # Get Vertex AI configuration
        model = model_name or config.get_provider_default_model("vertexai", "llm") or "gemini-pro"
        project = config.get("models.provider_defaults.vertexai.project")
        region = config.get("models.provider_defaults.vertexai.region") or "us-central1"
        
        # Get service account path
        service_account_path = config.get("models.defaults.google_service_account_path")
        
        # Authenticate with Google Cloud
        if service_account_path:
            credentials = service_account.Credentials.from_service_account_file(
                service_account_path,
                scopes=["https://www.googleapis.com/auth/cloud-platform"]
            )
        else:
            # Use default credentials if no service account file is provided
            credentials, _ = google.auth.default()
        
        # Initialize Vertex AI model
        return VertexAI(
            model_name=model,
            project=project,
            location=region,
            credentials=credentials,
            temperature=temperature
        )
            
    else:
        raise ValueError(f"Unsupported LLM provider: {provider}. Available providers: {list(LLM_PROVIDERS.keys())}")

def list_available_providers() -> Dict[str, Dict[str, List[str]]]:
    """
    List all available model providers for LLMs and embeddings.
    
    Returns:
        Dictionary with available providers
    """
    return {
        "llm_providers": LLM_PROVIDERS,
        "embedding_providers": EMBEDDING_PROVIDERS
    } 