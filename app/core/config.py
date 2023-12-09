from typing import List, Union

from pydantic import AnyHttpUrl, validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PROJECT_NAME: str = "apex"
    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = []
    API_PRIVATE_KEY_FILE: str = "<none>.json"
    ZITADEL_DOMAIN: str = "http://localhost:8080"
    ZITADEL_INTROSPECTION_URL: str = "http://localhost:8080/oauth/v2/introspect"
    API_BASE_URL: str = "http://localhost:8000"
    DATABASE_URL: str = "mongodb://localhost:27017"
    DATABASE_NAME: str = "apexlikeproject"

    @validator("BACKEND_CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    class Config:
        case_sensitive = True
        env_file = ".env"


settings = Settings()
