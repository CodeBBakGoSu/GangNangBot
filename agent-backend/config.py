"""
환경 변수 설정
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# .env 파일 로드 (루트 디렉토리의 .env 파일 우선)
root_env = Path(__file__).parent.parent / ".env"
if root_env.exists():
    load_dotenv(root_env)
else:
    load_dotenv()

# Agent Engine 설정
AGENT_RESOURCE_ID = os.getenv(
    "AGENT_RESOURCE_ID",
    "projects/88199591627/locations/us-east4/reasoningEngines/1183144880231153664"
)

# Google Cloud 설정
GOOGLE_CLOUD_PROJECT = os.getenv("GOOGLE_CLOUD_PROJECT", "kangnam-backend")
VERTEX_AI_LOCATION = os.getenv("VERTEX_AI_LOCATION", "us-east4")

# Database 설정
DATABASE_URL = os.getenv("DATABASE_URL")

# OAuth 설정
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
OAUTH_REDIRECT_URI = os.getenv("OAUTH_REDIRECT_URI", "http://localhost:8080/auth/google/callback")

# JWT 설정
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_EXPIRATION_HOURS = int(os.getenv("JWT_EXPIRATION_HOURS", "24"))

# 환경 확인
def check_config():
    """환경 변수 확인"""
    required_vars = {
        "AGENT_RESOURCE_ID": AGENT_RESOURCE_ID,
        "GOOGLE_CLOUD_PROJECT": GOOGLE_CLOUD_PROJECT,
        "VERTEX_AI_LOCATION": VERTEX_AI_LOCATION,
    }
    
    missing = [k for k, v in required_vars.items() if not v]
    
    if missing:
        raise ValueError(f"Missing required environment variables: {', '.join(missing)}")
    
    return required_vars

