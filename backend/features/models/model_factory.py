import sys
import os

for site_pkg in [
    r"C:\Users\Rishi\AppData\Local\Programs\Python\Python314\Lib\site-packages",
    r"C:\Users\Rishi\AppData\Roaming\Python\Python314\site-packages"
]:
    if os.path.exists(site_pkg) and site_pkg not in sys.path:
        sys.path.insert(0, site_pkg)

_curr_dir = os.path.dirname(os.path.abspath(__file__))
_back_dir = os.path.abspath(os.path.join(_curr_dir, "..", "..")) if "features" in _curr_dir else os.path.abspath(_curr_dir)
_feat_dir = os.path.join(_back_dir, "features")

if _back_dir not in sys.path:
    sys.path.insert(0, _back_dir)
if _feat_dir not in sys.path:
    sys.path.insert(0, _feat_dir)

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
