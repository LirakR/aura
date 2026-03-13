from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "Aura"
    version: str = "0.1.0"
    debug: bool = False

    model_config = {"env_prefix": "AURA_"}


settings = Settings()
