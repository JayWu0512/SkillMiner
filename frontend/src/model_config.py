"""
Model configuration for SkillMiner Agent
Configure different AI models for enhanced skill analysis
"""

import os
from typing import Dict, Any, Optional


class ModelConfig:
    """Configuration for AI models used in SkillMiner Agent."""
    
    def __init__(self):
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load model configuration from environment variables."""
        return {
            # Enable/disable AI models
            "use_ai_models": os.getenv("SKILLMINER_USE_AI", "false").lower() == "true",
            
            # OpenAI Configuration
            "openai": {
                "enabled": os.getenv("OPENAI_API_KEY") is not None,
                "api_key": os.getenv("OPENAI_API_KEY"),
                "model": os.getenv("OPENAI_MODEL", "gpt-3.5-turbo"),
                "max_tokens": int(os.getenv("OPENAI_MAX_TOKENS", "200")),
                "temperature": float(os.getenv("OPENAI_TEMPERATURE", "0.1"))
            },
            
            # Local LLM Configuration (Ollama, etc.)
            "local_llm": {
                "enabled": os.getenv("LOCAL_LLM_ENABLED", "false").lower() == "true",
                "endpoint": os.getenv("LOCAL_LLM_ENDPOINT", "http://localhost:11434/api/generate"),
                "model": os.getenv("LOCAL_LLM_MODEL", "llama2"),
                "timeout": int(os.getenv("LOCAL_LLM_TIMEOUT", "30"))
            },
            
            # Hugging Face Transformers
            "transformers": {
                "enabled": os.getenv("TRANSFORMERS_ENABLED", "false").lower() == "true",
                "ner_model": os.getenv("NER_MODEL", "dbmdz/bert-large-cased-finetuned-conll03-english"),
                "device": os.getenv("TRANSFORMERS_DEVICE", "cpu")  # or "cuda"
            },
            
            # spaCy Configuration
            "spacy": {
                "enabled": os.getenv("SPACY_ENABLED", "true").lower() == "true",
                "model": os.getenv("SPACY_MODEL", "en_core_web_sm")
            },
            
            # Azure OpenAI
            "azure_openai": {
                "enabled": os.getenv("AZURE_OPENAI_ENDPOINT") is not None,
                "endpoint": os.getenv("AZURE_OPENAI_ENDPOINT"),
                "api_key": os.getenv("AZURE_OPENAI_API_KEY"),
                "deployment": os.getenv("AZURE_OPENAI_DEPLOYMENT"),
                "api_version": os.getenv("AZURE_OPENAI_API_VERSION", "2023-05-15")
            }
        }
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value."""
        keys = key.split(".")
        value = self.config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def is_enabled(self, model_type: str) -> bool:
        """Check if a model type is enabled."""
        return self.get(f"{model_type}.enabled", False)


# Global configuration instance
model_config = ModelConfig()


def get_available_models() -> Dict[str, bool]:
    """Get status of all available models."""
    return {
        "spacy": model_config.is_enabled("spacy"),
        "openai": model_config.is_enabled("openai"),
        "azure_openai": model_config.is_enabled("azure_openai"),
        "local_llm": model_config.is_enabled("local_llm"),
        "transformers": model_config.is_enabled("transformers")
    }


def setup_instructions() -> Dict[str, str]:
    """Get setup instructions for each model type."""
    return {
        "spacy": """
        # Install spaCy and download model
        pip install spacy
        python -m spacy download en_core_web_sm
        export SPACY_ENABLED=true
        """,
        
        "openai": """
        # Set OpenAI API key
        export OPENAI_API_KEY=your_api_key_here
        export OPENAI_MODEL=gpt-3.5-turbo  # or gpt-4
        """,
        
        "azure_openai": """
        # Set Azure OpenAI credentials
        export AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
        export AZURE_OPENAI_API_KEY=your_api_key_here
        export AZURE_OPENAI_DEPLOYMENT=your_deployment_name
        """,
        
        "local_llm": """
        # Install and run Ollama
        curl -fsSL https://ollama.ai/install.sh | sh
        ollama pull llama2  # or mistral, codellama, etc.
        ollama serve
        export LOCAL_LLM_ENABLED=true
        """,
        
        "transformers": """
        # Install transformers
        pip install transformers torch
        export TRANSFORMERS_ENABLED=true
        # For GPU: export TRANSFORMERS_DEVICE=cuda
        """
    }