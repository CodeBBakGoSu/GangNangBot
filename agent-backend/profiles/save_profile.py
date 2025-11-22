"""
POST /profiles - 프로필 저장
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from routers.database import get_db
import config

router = APIRouter()


class ProfileRequest(BaseModel):
    """프로필 저장 요청"""
    user_id: int = Field(..., description="users 테이블의 id")
    profile_name: str = Field(..., description="프로필 이름")
    student_id: str = Field(..., description="학번")
    college: str = Field(..., description="단과대학 정보")
    department: str = Field(..., description="학부/학과")
    major: str = Field(..., description="전공 정보")
    current_grade: int = Field(..., description="현재 학년")
    current_semester: int = Field(..., description="현재 학기")


class ProfileResponse(BaseModel):
    """프로필 저장 응답"""
    id: int
    user_id: int
    profile_name: str
    student_id: str
    college: str
    department: str
    major: str
    current_grade: int
    current_semester: int
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


@router.post("/", response_model=ProfileResponse)
async def save_profile(
    profile_data: ProfileRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    프로필 정보를 Supabase의 profiles 테이블에 저장합니다.
    
    user_id를 기준으로 기존 프로필이 있으면 업데이트하고, 없으면 새로 생성합니다.
    
    Request Body:
        user_id: 사용자 ID (bigint)
        profile_name: 프로필 이름 (varchar(255))
        student_id: 학번 (varchar(255))
        college: 단과대학 정보 (varchar(255))
        department: 학부/학과 (varchar(255))
        major: 전공 정보 (varchar(255))
        current_grade: 현재 학년 (integer)
        current_semester: 현재 학기 (integer)
    
    Returns:
        저장된 프로필 정보
    """
    try:
        # user_id로 기존 프로필 확인
        check_query = text("""
            SELECT id, user_id, profile_name, student_id, college, department, 
                   major, current_grade, current_semester, created_at, updated_at
            FROM profiles
            WHERE user_id = :user_id
            LIMIT 1
        """)
        
        result = await db.execute(check_query, {"user_id": profile_data.user_id})
        existing = result.fetchone()
        
        if existing:
            # 기존 프로필이 있으면 업데이트
            update_query = text("""
                UPDATE profiles
                SET profile_name = :profile_name,
                    student_id = :student_id,
                    college = :college,
                    department = :department,
                    major = :major,
                    current_grade = :current_grade,
                    current_semester = :current_semester,
                    updated_at = NOW()
                WHERE user_id = :user_id
                RETURNING id, user_id, profile_name, student_id, college, department,
                          major, current_grade, current_semester, created_at, updated_at
            """)
            
            result = await db.execute(update_query, {
                "user_id": profile_data.user_id,
                "profile_name": profile_data.profile_name,
                "student_id": profile_data.student_id,
                "college": profile_data.college,
                "department": profile_data.department,
                "major": profile_data.major,
                "current_grade": profile_data.current_grade,
                "current_semester": profile_data.current_semester,
            })
            await db.commit()
            
            updated = result.fetchone()
            if not updated:
                raise HTTPException(
                    status_code=500,
                    detail="Failed to update profile"
                )
            
            profile = updated
        else:
            # 기존 프로필이 없으면 새로 생성
            insert_query = text("""
                INSERT INTO profiles (user_id, profile_name, student_id, college, 
                                     department, major, current_grade, current_semester)
                VALUES (:user_id, :profile_name, :student_id, :college, 
                        :department, :major, :current_grade, :current_semester)
                RETURNING id, user_id, profile_name, student_id, college, department,
                          major, current_grade, current_semester, created_at, updated_at
            """)
            
            result = await db.execute(insert_query, {
                "user_id": profile_data.user_id,
                "profile_name": profile_data.profile_name,
                "student_id": profile_data.student_id,
                "college": profile_data.college,
                "department": profile_data.department,
                "major": profile_data.major,
                "current_grade": profile_data.current_grade,
                "current_semester": profile_data.current_semester,
            })
            await db.commit()
            
            created = result.fetchone()
            if not created:
                raise HTTPException(
                    status_code=500,
                    detail="Failed to create profile"
                )
            
            profile = created
        
        # 응답 반환
        return ProfileResponse(
            id=profile.id,
            user_id=profile.user_id,
            profile_name=profile.profile_name,
            student_id=profile.student_id,
            college=profile.college,
            department=profile.department,
            major=profile.major,
            current_grade=profile.current_grade,
            current_semester=profile.current_semester,
            created_at=profile.created_at.isoformat() if profile.created_at else None,
            updated_at=profile.updated_at.isoformat() if profile.updated_at else None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to save profile: {str(e)}"
        )
