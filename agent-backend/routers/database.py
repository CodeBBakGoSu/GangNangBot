from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
from typing import AsyncGenerator
import config

router = APIRouter()

# 비동기 엔진 생성
# postgresql:// -> postgresql+psycopg:// 로 변경 (PgBouncer 호환)
DATABASE_URL = config.DATABASE_URL
if DATABASE_URL and DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+psycopg://", 1)

engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    pool_size=20,
    max_overflow=10
)

# 비동기 세션 팩토리
AsyncSessionLocal = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    비동기 DB 세션 의존성 주입
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

@router.get("/check-db")
async def check_db_connection(db: AsyncSession = Depends(get_db)):
    """
    데이터베이스 연결 상태를 확인합니다.
    """
    try:
        # 간단한 쿼리 실행 (연결 테스트)
        result = await db.execute(text("SELECT 1"))
        value = result.scalar()
            
        return {
            "status": "success",
            "message": "Database connection successful (Async)",
            "result": value
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database connection failed: {str(e)}")
