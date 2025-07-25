"""
Configuration Manager for Ragify
Handles loading configuration from YAML file and environment variable overrides.
"""
import os
import yaml
from pathlib import Path
from typing import Any, Dict, Optional, Union
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class ConfigManager:
    """Singleton configuration manager for the Ragify application."""
    
    _instance = None
    _config = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ConfigManager, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._config is None:
            self.load_config()
    
    def load_config(self, config_path: Optional[str] = None):
        """Load configuration from YAML file."""
        if config_path is None:
            config_path = Path(__file__).parent / "config.yaml"
        
        with open(config_path, 'r') as f:
            self._config = yaml.safe_load(f)
        
        # Apply environment variable overrides
        self._apply_env_overrides()
    
    def _apply_env_overrides(self):
        """Apply environment variable overrides to configuration."""
        env_overrides = self._config.get('env_overrides', {})
        
        for env_var, config_path in env_overrides.items():
            env_value = os.getenv(env_var)
            if env_value is not None and config_path is not None:
                self._set_nested_value(config_path, env_value)
    
    def _set_nested_value(self, path: str, value: Any):
        """Set a nested configuration value using dot notation."""
        keys = path.split('.')
        current = self._config
        
        # Navigate to the parent of the target key
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        
        # Convert string values to appropriate types
        if value.lower() in ('true', 'false'):
            value = value.lower() == 'true'
        elif value.isdigit():
            value = int(value)
        elif value.replace('.', '').isdigit():
            value = float(value)
        
        # Set the final value
        current[keys[-1]] = value
    
    def get(self, path: str, default: Any = None) -> Any:
        """Get a configuration value using dot notation."""
        keys = path.split('.')
        current = self._config
        
        try:
            for key in keys:
                current = current[key]
            return current
        except (KeyError, TypeError):
            return default
    
    def get_server_config(self) -> Dict[str, Any]:
        """Get server configuration."""
        return self.get('server', {})
    
    def get_model_config(self) -> Dict[str, Any]:
        """Get model configuration."""
        return self.get('models', {})
    
    def get_default_llm_provider(self) -> str:
        """Get default LLM provider."""
        return self.get('models.defaults.llm_provider', 'openai')
    
    def get_default_llm_model(self) -> Optional[str]:
        """Get default LLM model."""
        return self.get('models.defaults.llm_model')
    
    def get_default_embedding_provider(self) -> str:
        """Get default embedding provider."""
        return self.get('models.defaults.embedding_provider', 'openai')
    
    def get_default_embedding_model(self) -> Optional[str]:
        """Get default embedding model."""
        return self.get('models.defaults.embedding_model')
    
    def get_provider_default_model(self, provider: str, model_type: str) -> Optional[str]:
        """Get provider-specific default model."""
        return self.get(f'models.provider_defaults.{provider}.{model_type}_model')
    
    def get_temperature(self) -> float:
        """Get default temperature for LLM."""
        return self.get('models.defaults.temperature', 0)
    
    def get_document_processing_config(self) -> Dict[str, Any]:
        """Get document processing configuration."""
        return self.get('document_processing', {})
    
    def get_chunk_size(self) -> int:
        """Get chunk size for document processing."""
        return self.get('document_processing.chunk_size', 1000)
    
    def get_chunk_overlap(self) -> int:
        """Get chunk overlap for document processing."""
        return self.get('document_processing.chunk_overlap', 200)
    
    def get_retrieval_config(self) -> Dict[str, Any]:
        """Get retrieval configuration."""
        return self.get('retrieval', {})
    
    def get_search_type(self) -> str:
        """Get search type for retriever."""
        return self.get('retrieval.search_type', 'similarity')
    
    def get_top_k_results(self) -> int:
        """Get top k results for retriever."""
        return self.get('retrieval.top_k_results', 4)
    
    def get_mmr_diversity_score(self) -> float:
        """Get MMR diversity score for retriever."""
        return self.get('retrieval.mmr_diversity_score', 0.5)
    
    def get_rag_prompt_template(self) -> str:
        """Get RAG prompt template."""
        return self.get('prompts.rag_template', '')
    
    def get_query_rewrite_template(self) -> str:
        """Get query rewrite prompt template."""
        return self.get('prompts.query_rewrite_template', '')
    
    def get_testing_config(self) -> Dict[str, Any]:
        """Get testing configuration."""
        return self.get('testing', {})
    
    def get_default_timeout(self) -> int:
        """Get default timeout for testing."""
        return self.get('testing.default_timeout', 60)
    
    def get_health_check_timeout(self) -> int:
        """Get health check timeout for testing."""
        return self.get('testing.health_check_timeout', 5)
    
    def get_default_api_url(self) -> str:
        """Get default API URL for testing."""
        return self.get('testing.default_api_url', 'http://localhost:5000')
    
    def get_default_questions(self) -> list:
        """Get default test questions."""
        return self.get('testing.default_questions', [])
    
    def get_paths_config(self) -> Dict[str, str]:
        """Get paths configuration."""
        return self.get('paths', {})
    
    def get_docs_dir(self) -> str:
        """Get documents directory path."""
        return self.get('paths.docs_dir', 'docs')
    
    def get_storage_dir(self) -> str:
        """Get storage directory path."""
        return self.get('paths.storage_dir', 'storage')
    
    def get_results_dir_prefix(self) -> str:
        """Get results directory prefix."""
        return self.get('paths.results_dir_prefix', 'results')
    
    def get_openai_api_key(self) -> Optional[str]:
        """Get OpenAI API key."""
        return self.get('models.defaults.openai_api_key')

    def get_huggingface_pipeline_max_length(self) -> int:
        """Get HuggingFace pipeline max length."""
        return self.get('models.provider_defaults.huggingface.pipeline_max_length', 512)
    
    def get_port(self) -> int:
        """Get server port."""
        return self.get('server.port', 5000)
    
    def get_debug(self) -> bool:
        """Get debug mode setting."""
        return self.get('server.debug', False)
    
    def get_host(self) -> str:
        """Get server host."""
        return self.get('server.host', '0.0.0.0')
    
    def get_chat_history_length(self) -> int:
        """Get chat history length."""
        return self.get('chat.history_length', 5)
    
    def get_max_context_tokens(self) -> int:
        """Get maximum context tokens for chat history."""
        return self.get('chat.max_context_tokens', 2000)

# Global configuration instance
config = ConfigManager()