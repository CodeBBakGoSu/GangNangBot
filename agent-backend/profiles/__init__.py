"""
프로필 관련 라우터 모듈
"""
from fastapi import APIRouter
from .save_profile import router as save_profile_router

# 메인 라우터에 서브 라우터 통합
router = APIRouter(prefix="/profiles", tags=["profiles"])
router.include_router(save_profile_router)

__all__ = ['router']
