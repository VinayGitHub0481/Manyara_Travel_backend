from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # Redis is optional. Leave CACHE_ENABLED on if you have Redis running -
    # it takes real load off the DB for the public homepage endpoints (most
    # heavily hit: packages, most-visited, blogs, happy-moments). If you'd
    # rather not run a Redis instance for a site at this traffic level, set
    # CACHE_ENABLED=false and every read just goes straight to the DB - the
    # app works identically either way. The client also auto-disables
    # itself if it can't reach Redis at startup, so a missing Redis server
    # never crashes the app even if this is left true.
    CACHE_ENABLED: bool = True
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    CACHE_TTL_SECONDS: int = 300

    # Images (packages, destinations, blog covers, happy moments,
    # testimonial photos) are stored on Cloudinary rather than local disk -
    # keeps the API server stateless and images on a proper CDN.
    # Get these three from your Cloudinary dashboard (cloudinary.com/console).
    CLOUDINARY_CLOUD_NAME: str = ""
    CLOUDINARY_API_KEY: str = ""
    CLOUDINARY_API_SECRET: str = ""
    # All uploads are organized under this folder in your Cloudinary media
    # library, so they're easy to find/manage separately from anything else
    # on the same account.
    CLOUDINARY_UPLOAD_FOLDER: str = "ManyaraPrive_Vacations"
    MAX_UPLOAD_MB: int = 5

    # Public-facing site info, used as defaults for /settings until an admin
    # edits them from the Website Settings admin page.
    WHATSAPP_NUMBER: str = ""
    SITE_URL: str = "https://manyaraprive.com"

    OTP_EXPIRY_MINUTES: int = 5
    RESET_SESSION_EXPIRY_MINUTES: int = 10

    # Email message settings
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USERNAME: str
    SMTP_PASSWORD: str
    #Manyara backend
    SMTP_USE_TLS: bool = True
    EMAIL_FROM: str

    class Config:
        env_file = ".env"


settings = Settings()
