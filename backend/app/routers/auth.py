from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.models.user import User
from app.schemas.user import UserCreate, UserLogin, UserResponse, Token
from app.auth import (
    get_password_hash, 
    authenticate_user, 
    create_access_token,
    get_current_active_user,
    ACCESS_TOKEN_EXPIRE_MINUTES
)
from app.db.database import get_db
import uuid

router = APIRouter(prefix="/api/auth", tags=["authentication"])

@router.post("/register", response_model=UserResponse)
async def register_user(user: UserCreate, db: Session = Depends(get_db)):
    """注册新用户"""
    # 检查用户名是否已存在
    db_user = db.query(User).filter(User.username == user.username).first()
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    # 创建新用户
    hashed_password = get_password_hash(user.password)
    invite_code = generate_invite_code(user.role) if user.role == "admin" else None
    db_user = User(
        username=user.username,
        password_hash=hashed_password,
        role=user.role,
        invite_code=invite_code if user.role == "admin" else None
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    return db_user

@router.post("/login", response_model=Token)
async def login_user(user_credentials: UserLogin, db: Session = Depends(get_db)):
    """用户登录"""
    user = authenticate_user(db, user_credentials.username, user_credentials.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=UserResponse)
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    """获取当前用户信息"""
    return current_user

@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """根据ID获取用户信息"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

def generate_invite_code(role):
    """为当前用户生成邀请码（仅限admin用户）"""
    if role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admin users can generate invite codes"
        )
    
    # 生成新的邀请码
    invite_code = str(uuid.uuid4())
    
    return invite_code

@router.get("/invite-code")
async def get_my_invite_code(
    current_user: User = Depends(get_current_active_user)
):
    """获取当前用户的邀请码"""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admin users can access invite codes"
        )
    
    if not current_user.invite_code:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No invite code generated yet"
        )
    
    return {"invite_code": current_user.invite_code}

@router.delete("/invite-code")
async def revoke_invite_code(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """撤销当前用户的邀请码"""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admin users can revoke invite codes"
        )
    
    current_user.invite_code = None
    db.commit()
    
    return {"message": "Invite code revoked successfully"}
