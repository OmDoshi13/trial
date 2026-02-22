"""App settings — loaded from env vars / .env file."""

from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):

    # Ollama
    ollama_base_url: str = "http://localhost:11434"
    llm_model: str = "llama3.2"
    embedding_model: str = "nomic-embed-text"

    # Mock HR service
    mock_hr_base_url: str = "http://localhost:8001"

    # Paths
    chroma_persist_dir: str = "./data/chroma_db"
    documents_dir: str = "./documents"

    # App
    log_level: str = "INFO"

    # Derived
    @property
    def chroma_path(self) -> Path:
        return Path(self.chroma_persist_dir)

    @property
    def docs_path(self) -> Path:
        return Path(self.documents_dir)

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


# Singleton
settings = Settings()
