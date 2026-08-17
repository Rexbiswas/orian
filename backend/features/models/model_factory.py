import logging
from typing import Optional
from models.base_provider import LLMProvider
from models.openai_provider import OpenAIProvider
from models.huggingface_provider import HuggingFaceProvider
from models.local_provider import LocalProvider
from config import settings

logger = logging.getLogger("orian.model_factory")

def get_llm_provider(provider_name: Optional[str] = None) -> LLMProvider:
    name = (provider_name or settings.DEFAULT_PROVIDER).lower()

    if name == "openai":
        try:
            return OpenAIProvider()
        except Exception as e:
            logger.warning(f"Failed to initialize OpenAIProvider ({e}). Falling back to LocalProvider.")
            return LocalProvider()
    elif name == "huggingface":
        try:
            return HuggingFaceProvider()
        except Exception as e:
            logger.warning(f"Failed to initialize HuggingFaceProvider ({e}). Falling back to LocalProvider.")
            return LocalProvider()
    else:
        return LocalProvider()
