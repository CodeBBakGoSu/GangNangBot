"""
Google OAuth 인증 라우터 (Authlib + Async DB)
"""

import uuid
from fastapi import APIRouter, HTTPException, Header, Request, Depends
from authlib.integrations.starlette_client import OAuth
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from typing import Optional

import config
from utils.jwt import create_access_token, verify_token
from routers.database import get_db

router = APIRouter()

# Authlib OAuth 설정
oauth = OAuth()
oauth.register(
    name='google',
    client_id=config.GOOGLE_CLIENT_ID,
    client_secret=config.GOOGLE_CLIENT_SECRET,
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={
        'scope': 'openid email profile'
    }
)

@router.get("/google/login")
async def google_login(request: Request):
    """
    Google OAuth 로그인 URL로 리다이렉트
    Authlib이 자동으로 State 생성 및 세션 저장을 처리함
    """
    if not config.GOOGLE_CLIENT_ID or not config.GOOGLE_CLIENT_SECRET:
        raise HTTPException(status_code=500, detail="OAuth credentials not configured")
        
    redirect_uri = config.OAUTH_REDIRECT_URI
    return await oauth.google.authorize_redirect(request, redirect_uri)


@router.get("/google/callback")
async def google_callback(request: Request, db: AsyncSession = Depends(get_db)):
    """
    Google OAuth 콜백 처리
    """
    try:
        # 토큰 교환 및 검증 (Authlib이 State 검증 자동 수행)
        token = await oauth.google.authorize_access_token(request)
        userinfo = token.get('userinfo')
        
        if not userinfo:
            # userinfo가 토큰에 없는 경우 별도 요청
            userinfo = await oauth.google.userinfo(token=token)

        google_id = userinfo.get("sub")
        email = userinfo.get("email")
        name = userinfo.get("name")

        if not google_id or not email:
            raise HTTPException(status_code=400, detail="Invalid user info from Google")

        # DB에 사용자 upsert (비동기)
        user_id = await upsert_user(db, google_id, email, name)

        # JWT 토큰 생성
        access_token = create_access_token(data={"user_id": str(user_id)})

        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": str(user_id),
                "email": email,
                "name": name
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OAuth callback failed: {str(e)}")


@router.get("/me")
async def get_current_user(
    authorization: str = Header(...),
    db: AsyncSession = Depends(get_db)
):
    """
    현재 로그인된 사용자 정보 조회
    """
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header")

    token = authorization.split(" ")[1]
    payload = verify_token(token)

    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    user_id = payload.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token payload")

    # DB에서 사용자 정보 조회
    user = await get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return user


async def upsert_user(db: AsyncSession, google_id: str, email: str, name: str) -> uuid.UUID:
    """
    사용자 정보를 DB에 upsert (비동기)
    """
    # google_id로 기존 사용자 조회
    result = await db.execute(
        text("SELECT id FROM profiles WHERE google_id = :google_id"),
        {"google_id": google_id}
    )
    existing_user = result.fetchone()

    if existing_user:
        # 기존 사용자 - 이메일, 이름 업데이트
        await db.execute(
            text("""
                UPDATE profiles
                SET email = :email, name = :name
                WHERE google_id = :google_id
            """),
            {"email": email, "name": name, "google_id": google_id}
        )
        await db.commit()
        return existing_user[0]
    else:
        # 신규 사용자 생성
        new_id = uuid.uuid4()
        await db.execute(
            text("""
                INSERT INTO profiles (id, google_id, email, name, created_at)
                VALUES (:id, :google_id, :email, :name, NOW())
            """),
            {"id": new_id, "google_id": google_id, "email": email, "name": name}
        )
        await db.commit()
        return new_id


async def get_user_by_id(db: AsyncSession, user_id: str) -> Optional[dict]:
    """
    UUID로 사용자 정보 조회 (비동기)
    """
    result = await db.execute(
        text("""
            SELECT id, google_id, email, name, student_id, college,
                   department, major, graduation_status, current_semester, 
                   created_at, updated_at
            FROM profiles
            WHERE id = :user_id
        """),
        {"user_id": user_id}
    )
    row = result.fetchone()

    if not row:
        return None

    return {
        "id": str(row[0]),
        "google_id": row[1],
        "email": row[2],
        "name": row[3],
        "student_id": row[4],
        "college": row[5],
        "department": row[6],
        "major": row[7],
        "graduation_status": row[8],
        "current_semester": row[9],
        "created_at": row[10].isoformat() if row[10] else None,
        "updated_at": row[11].isoformat() if row[11] else None
    }
