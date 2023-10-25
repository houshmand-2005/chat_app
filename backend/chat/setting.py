from enum import auto


class Settings(auto):
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 43800
    SECRET_KEY: str = "SeCretKey_CHaNgeMe"
    ALGORITHM: str = "HS256"
    VERSION: int = 1


setting = Settings()
