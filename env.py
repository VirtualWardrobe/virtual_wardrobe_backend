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

    @classmethod
    def to_dict(cls):
        return {key: value for key, value in cls.__dict__.items() if not key.startswith('__')}

env = Environment()
