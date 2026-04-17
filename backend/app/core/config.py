from functools import lru_cache
from pathlib import Path
from urllib.parse import quote_plus

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(str(BASE_DIR / '.env'), '.env'),
        env_file_encoding='utf-8',
        extra='ignore',
        case_sensitive=True,
    )

    APP_NAME: str = Field(default='圈脉链后端服务')
    APP_ENV: str = Field(default='dev')
    APP_HOST: str = Field(default='0.0.0.0')
    APP_PORT: int = Field(default=8001)
    DEBUG: bool = Field(default=True)
    API_V1_PREFIX: str = Field(default='/api/v1')

    MYSQL_HOST: str = Field(default='127.0.0.1')
    MYSQL_PORT: int = Field(default=3306)
    MYSQL_USER: str = Field(default='root')
    MYSQL_PASSWORD: str = Field(default='root')
    MYSQL_DB: str = Field(default='quanmailian')

    REDIS_HOST: str = Field(default='127.0.0.1')
    REDIS_PORT: int = Field(default=6379)
    REDIS_DB: int = Field(default=0)
    REDIS_PASSWORD: str | None = Field(default=None)
    REDIS_ENABLED: bool = Field(default=True)

    JWT_SECRET_KEY: str = Field(default='replace-with-your-secret')
    JWT_ALGORITHM: str = Field(default='HS256')
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=60 * 24)

    OSS_ENDPOINT: str = Field(default='')
    OSS_BUCKET: str = Field(default='')
    OSS_ACCESS_KEY: str = Field(default='')
    OSS_SECRET_KEY: str = Field(default='')

    WECHAT_MINI_APP_ID: str = Field(default='')
    WECHAT_MINI_APP_SECRET: str = Field(default='')
    WECHAT_CODE2SESSION_URL: str = Field(
        default='https://api.weixin.qq.com/sns/jscode2session'
    )
    WECHAT_PAY_ENABLED: bool = Field(default=False)
    WECHAT_PAY_APP_ID: str = Field(default='')
    WECHAT_PAY_MCH_ID: str = Field(default='')
    WECHAT_PAY_API_V2_KEY: str = Field(default='')
    WECHAT_PAY_NOTIFY_URL: str = Field(default='')
    WECHAT_PAY_UNIFIEDORDER_URL: str = Field(default='https://api.mch.weixin.qq.com/pay/unifiedorder')
    DEFAULT_AVATAR_URL: str = Field(default='/static/logo.png')
    VERIFICATION_AUTO_APPROVE: bool = Field(default=False)
    VERIFICATION_DATA_SECRET: str = Field(default="")
    TENCENT_CLOUD_SECRET_ID: str = Field(default='')
    TENCENT_CLOUD_SECRET_KEY: str = Field(default='')
    TENCENT_CLOUD_REGION: str = Field(default='ap-guangzhou')
    TENCENT_CLOUD_FACEID_APP_ID: str = Field(default='')
    TENCENT_CLOUD_FACEID_RULE_ID: str = Field(default='')
    TENCENT_CLOUD_FACEID_REDIRECT_URL: str = Field(default='')
    TENCENT_CLOUD_FACEID_LIVENESS_TYPE: str = Field(default='SILENT')
    ADMIN_REVIEW_TOKEN: str = Field(default='change-this-admin-review-token')
    ADMIN_DEFAULT_USERNAME: str = Field(default='admin')
    ADMIN_DEFAULT_PASSWORD: str = Field(default='Admin@20260325')
    ADMIN_DEFAULT_DISPLAY_NAME: str = Field(default='系统管理员')

    @field_validator('DEBUG', 'REDIS_ENABLED', 'VERIFICATION_AUTO_APPROVE', 'WECHAT_PAY_ENABLED', mode='before')
    @classmethod
    def parse_bool_value(cls, value):  # noqa: ANN206
        if isinstance(value, bool):
            return value
        if isinstance(value, (int, float)):
            return bool(value)
        if isinstance(value, str):
            normalized = value.strip().lower()
            if normalized in {'1', 'true', 'yes', 'on', 'debug', 'dev'}:
                return True
            if normalized in {'0', 'false', 'no', 'off', 'release', 'prod', 'production'}:
                return False
        raise ValueError('Invalid boolean value')

    @property
    def DATABASE_URL(self) -> str:
        user = quote_plus(self.MYSQL_USER)
        password = quote_plus(self.MYSQL_PASSWORD)
        return (
            f'mysql+pymysql://{user}:{password}'
            f'@{self.MYSQL_HOST}:{self.MYSQL_PORT}/{self.MYSQL_DB}?charset=utf8mb4'
        )

    @property
    def REDIS_URL(self) -> str:
        if self.REDIS_PASSWORD:
            return (
                f'redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:'
                f'{self.REDIS_PORT}/{self.REDIS_DB}'
            )
        return f'redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}'


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()

