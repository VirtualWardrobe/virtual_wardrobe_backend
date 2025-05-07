import os
from dotenv import load_dotenv

load_dotenv()

class Environment:
    DATABASE_URL:str=os.getenv("MC_DATABASE_URL")
    RESEND_API_KEY:str=os.getenv("VW_RESEND_API_KEY")
    JWT_SECRET_KEY:str=os.getenv("VW_JWT_SECRET_KEY")
    GOOGLE_CLIENT_ID:str=os.getenv("VW_GOOGLE_CLIENT_ID")
    GOOGLE_CLIENT_SECRET:str=os.getenv("VW_GOOGLE_CLIENT_SECRET")
    GOOGLE_REDIRECT_URI:str=os.getenv("VW_GOOGLE_REDIRECT_URI")
    FRONT_END_RESPONSE_URI:str=os.getenv("VW_FRONT_END_RESPONSE_URI")
    GOOGLE_STORAGE_MEDIA_BUCKET:str=os.getenv("VW_GOOGLE_STORAGE_MEDIA_BUCKET")
    GCP_PROJECT_ID:str=os.getenv("VW_GCP_PROJECT_ID")
    GCP_PRIVATE_KEY_ID:str=os.getenv("VW_GCP_PRIVATE_KEY_ID")
    GCP_PRIVATE_KEY:str=os.getenv("VW_GCP_PRIVATE_KEY")
    GCP_CLIENT_EMAIL:str=os.getenv("VW_GCP_CLIENT_EMAIL")
    GCP_CLIENT_ID:str=os.getenv("VW_GCP_CLIENT_ID")
    GCP_CLIENT_X509_CERT_URL:str=os.getenv("VW_GCP_CLIENT_X509_CERT_URL")
    REDIS_HOST:str=os.getenv("VW_REDIS_HOST")
    REDIS_PORT:str=os.getenv("VW_REDIS_PORT")
    REDIS_PASSWORD:str=os.getenv("VW_REDIS_PASSWORD")

    @classmethod
    def to_dict(cls):
        return {key: value for key, value in cls.__dict__.items() if not key.startswith('__')}

env = Environment()
