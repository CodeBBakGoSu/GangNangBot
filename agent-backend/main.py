"""
Agent Backend API

FastAPI 백엔드 - Agent Engine과 연동
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import chat, database, auth
import config

# FastAPI 앱 생성
app = FastAPI(
    title="Kangnam Agent API",
    description="강남대학교 Multi-Agent 챗봇 API",
    version="1.0.0"
)

from starlette.middleware.sessions import SessionMiddleware

# CORS 설정 (프론트엔드 연동용)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 프로덕션에서는 특정 도메인으로 제한
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 세션 미들웨어 (OAuth State 관리용)
app.add_middleware(SessionMiddleware, secret_key=config.JWT_SECRET_KEY or "secret-key")

# 라우터 등록
app.include_router(chat.router, prefix="/chat", tags=["chat"])
app.include_router(database.router, prefix="/db", tags=["database"])
app.include_router(auth.router, prefix="/auth", tags=["auth"])

# 헬스체크 (Cloud Run 필수)
@app.get("/health")
async def health_check():
    """헬스체크 엔드포인트"""
    return {"status": "ok", "service": "agent-backend-api"}

# 루트 엔드포인트
@app.get("/")
async def root():
    """API 정보"""
    return {
        "service": "Kangnam Agent API",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "new_chat": "POST /chat/new",
            "send_message": "POST /chat/message"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)

