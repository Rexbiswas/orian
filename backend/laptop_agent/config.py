import os
from pydantic import BaseModel, Field

class LaptopAgentConfig(BaseModel):
    """Configuration settings for the Orian Windows Laptop Agent."""
    DEVICE_ID: str = Field(default_factory=lambda: os.getenv("ORIAN_DEVICE_ID", "laptop-main-001"))
    DEVICE_NAME: str = Field(default_factory=lambda: os.getenv("ORIAN_DEVICE_NAME", "Owner Windows Workstation"))
    AGENT_VERSION: str = "1.0.0"
    BACKEND_URL: str = Field(default_factory=lambda: os.getenv("ORIAN_BACKEND_URL", "http://127.0.0.1:8000"))
    CREDENTIALS_FILE: str = Field(default_factory=lambda: os.getenv("ORIAN_AGENT_CRED_PATH", os.path.join(os.path.dirname(__file__), "agent_credentials.json")))
    SAMPLE_INTERVAL_SECONDS: float = 2.0
    HEARTBEAT_INTERVAL_SECONDS: float = 10.0
    SIMULATE_SLEEP: bool = Field(default_factory=lambda: os.getenv("ORIAN_AGENT_SIMULATE_SLEEP", "0") in ["1", "true", "True"])

agent_config = LaptopAgentConfig()
