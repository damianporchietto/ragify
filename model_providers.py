"""
Module for managing different LLM and embedding model providers.
This allows easy swapping between different model providers (OpenAI, local models, etc.)
"""
import os
from typing import Dict, Any, Optional, List
from dotenv import load_dotenv

from langchain.schema import Document
from langchain.embeddings.base import Embeddings
from langchain.chat_models.base import BaseChatModel

# Providers
from langchain_openai import OpenAIEmbeddings, ChatOpenAI

# Potentially add these with conditional imports
# from langchain_community.embeddings import OllamaEmbeddings
# from langchain_community.chat_models import ChatOllama
# from langchain_huggingface import HuggingFaceEmbeddings
# from langchain_community.llms import HuggingFacePipeline

load_dotenv()  # Load environment variables

# Import config manager
from config_manager import config

# Dictionary of available LLM providers
LLM_PROVIDERS = {
    "openai": {
        "name": "OpenAI",
        "description": "OpenAI GPT models (requires API key)"
    },
    "ollama": {
        "name": "Ollama",
        "description": "Local models through Ollama (requires Ollama installation)"
    },
    "huggingface": {
        "name": "HuggingFace",
        "description": "HuggingFace models (local or through API)"
    }
}

# Dictionary of available embedding providers
EMBEDDING_PROVIDERS = {
    "openai": {
        "name": "OpenAI",
        "description": "OpenAI embedding models (requires API key)"
    },
    "ollama": {
        "name": "Ollama",
        "description": "Local embedding models through Ollama"
    },
    "huggingface": {
        "name": "HuggingFace", 
        "description": "HuggingFace embedding models (local)"
    }
}

def get_embeddings_model(provider: str = "openai", model_name: Optional[str] = None) -> Embeddings:
    """
    Get an embeddings model based on the specified provider.
    
    Args:
        provider: The provider to use ("openai", "ollama", "huggingface")
        model_name: Optional model name for the specified provider
        
    Returns:
        An initialized embeddings model
    """
    provider = provider.lower()
    
    if provider == "openai":
        model = model_name or config.get_provider_default_model("openai", "embedding") or "text-embedding-3-large"
        return OpenAIEmbeddings(model=model)
        
    elif provider == "ollama":
        try:
            from langchain_community.embeddings import OllamaEmbeddings
            model = model_name or config.get_provider_default_model("ollama", "embedding") or "nomic-embed-text"
            return OllamaEmbeddings(model=model)
        except ImportError:
            raise ImportError("OllamaEmbeddings not available. Install with: pip install langchain_community")
            
    elif provider == "huggingface":
        try:
            from langchain_huggingface import HuggingFaceEmbeddings
            model = model_name or config.get_provider_default_model("huggingface", "embedding") or "BAAI/bge-large-en-v1.5"
            return HuggingFaceEmbeddings(model_name=model)
        except ImportError:
            raise ImportError("HuggingFaceEmbeddings not available. Install with: pip install langchain-huggingface")
            
    else:
        raise ValueError(f"Unsupported embedding provider: {provider}. Available providers: {list(EMBEDDING_PROVIDERS.keys())}")

def get_llm_model(provider: str = "openai", model_name: Optional[str] = None, temperature: float = 0) -> BaseChatModel:
    """
    Get a language model based on the specified provider.
    
    Args:
        provider: The provider to use ("openai", "ollama", "huggingface")
        model_name: Optional model name for the specified provider
        temperature: Temperature parameter for text generation
        
    Returns:
        An initialized language model
    """
    provider = provider.lower()
    
    if provider == "openai":
        model = model_name or config.get_provider_default_model("openai", "llm") or "gpt-4o-mini"
        return ChatOpenAI(model=model, temperature=temperature)
        
    elif provider == "ollama":
        try:
            from langchain_community.chat_models import ChatOllama
            model = model_name or config.get_provider_default_model("ollama", "llm") or "mistral"
            return ChatOllama(model=model, temperature=temperature)
        except ImportError:
            raise ImportError("ChatOllama not available. Install with: pip install langchain_community")
            
    elif provider == "huggingface":
        try:
            from langchain_community.llms import HuggingFacePipeline
            # This is more complex and usually requires more configuration
            # Simplified implementation for demonstration
            model = model_name or config.get_provider_default_model("huggingface", "llm") or "google/flan-t5-xxl"
            from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
            
            tokenizer = AutoTokenizer.from_pretrained(model)
            hf_model = AutoModelForCausalLM.from_pretrained(model)
            
            pipe = pipeline(
                "text-generation",
                model=hf_model, 
                tokenizer=tokenizer,
                max_length=config.get_huggingface_pipeline_max_length(),
                temperature=temperature
            )
            
            return HuggingFacePipeline(pipeline=pipe)
        except ImportError:
            raise ImportError("HuggingFace pipeline not available. Install with: pip install langchain-huggingface transformers")
            
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