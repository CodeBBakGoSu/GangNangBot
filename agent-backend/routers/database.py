from fastapi import APIRouter, HTTPException
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
import config

router = APIRouter()

@router.get("/check-db")
async def check_db_connection():
    """
    데이터베이스 연결 상태를 확인합니다.
    """
    if not config.DATABASE_URL:
        raise HTTPException(status_code=500, detail="DATABASE_URL environment variable is not set")

    try:
        # SQLAlchemy 엔진 생성
        engine = create_engine(config.DATABASE_URL)
        
        # 간단한 쿼리 실행 (연결 테스트)
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            value = result.scalar()
            
        return {
            "status": "success",
            "message": "Database connection successful",
            "result": value
        }
        
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=f"Database connection failed: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")
