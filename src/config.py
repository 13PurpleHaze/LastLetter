from pydantic import field_validator, PostgresDsn, Field
from pydantic_core.core_schema import ValidationInfo
from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        extra="allow",
        case_sensitive=True,  ## Чувствительность к регистру
        env_file=str(Path.cwd().parent / ".env"),
    )
    BASE_DIR: str = str(Path.cwd().parent)

    # PG
    POSTGRES_DB_NAME: str
    POSTGRES_DB_USER: str
    POSTGRES_DB_PASSWORD: str
    POSTGRES_DB_HOST: str
    POSTGRES_DB_PORT: int
    POSTGRES_POOL_MIN_SIZE: int = 5
    POSTGRES_POOL_MAX_SIZE: int = 50
    POSTGRES_DSN: str = Field(default=None)  # type: ignore[assignment]

    # JWT
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    @field_validator("POSTGRES_DSN", mode="before")
    @classmethod
    def assemble_async_postgres_dsn(cls, v: str | None, values: ValidationInfo):
        if isinstance(v, str):
            return v

        if all(
            [
                values.data["POSTGRES_DB_NAME"],
                values.data["POSTGRES_DB_USER"],
                values.data["POSTGRES_DB_PASSWORD"],
                values.data["POSTGRES_DB_HOST"],
                values.data["POSTGRES_DB_PORT"],
            ]
        ):
            return str(
                PostgresDsn.build(
                    scheme="postgresql+asyncpg",
                    username=values.data["POSTGRES_DB_USER"],
                    password=values.data["POSTGRES_DB_PASSWORD"],
                    host=values.data["POSTGRES_DB_HOST"],
                    port=values.data["POSTGRES_DB_PORT"],
                    path=f"{values.data['POSTGRES_DB_NAME']}",
                )
            )

        raise ValueError(v)


settings = Settings()
