from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    aws_region: str = "ap-south-1"
    app_env: str = "development"
    log_level: str = "info"
    db_host: str = "localhost"
    db_port: int = 5432
    db_name: str = "cloudpulse"
    db_user: str = "cloudpulse_admin"
    db_password: str = ""

    class Config:
        env_file = ".env"

settings = Settings()
