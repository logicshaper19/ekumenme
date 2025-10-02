"""
Authentication service for agricultural chatbot
Handles user authentication, JWT tokens, and security
"""

from datetime import datetime, timedelta
from typing import Optional, Union
from uuid import UUID
from jose import JWTError, jwt
import bcrypt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.config import settings
from app.core.database import get_async_db
from app.models.user import User
from app.schemas.auth import UserCreate, TokenData

# Password hashing using bcrypt directly

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


class AuthService:
    """Authentication service for user management and JWT tokens"""
    
    def __init__(self):
        self.secret_key = settings.SECRET_KEY
        self.algorithm = settings.ALGORITHM
        self.access_token_expire_minutes = settings.ACCESS_TOKEN_EXPIRE_MINUTES
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash"""
        # Truncate password to 72 bytes if needed (bcrypt limitation)
        password_bytes = plain_password.encode('utf-8')[:72]
        return bcrypt.checkpw(password_bytes, hashed_password.encode('utf-8'))

    def get_password_hash(self, password: str) -> str:
        """Hash a password"""
        # Truncate password to 72 bytes if needed (bcrypt limitation)
        password_bytes = password.encode('utf-8')[:72]
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password_bytes, salt)
        return hashed.decode('utf-8')
    
    async def get_user_by_email(self, db: AsyncSession, email: str) -> Optional[User]:
        """Get user by email address"""
        result = await db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()
    
    async def get_user_by_id(self, db: AsyncSession, user_id: Union[str, UUID]) -> Optional[User]:
        """Get user by ID"""
        if isinstance(user_id, str):
            user_id = UUID(user_id)
        result = await db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()
    
    async def authenticate_user(self, db: AsyncSession, email: str, password: str) -> Optional[User]:
        """Authenticate user with email and password"""
        user = await self.get_user_by_email(db, email)
        if not user:
            return None
        if not self.verify_password(password, user.hashed_password):
            return None
        return user
    
    async def create_user(self, db: AsyncSession, user_data: UserCreate) -> User:
        """Create a new user"""
        # Hash the password
        hashed_password = self.get_password_hash(user_data.password)
        
        # Create user object
        user = User(
            email=user_data.email,
            hashed_password=hashed_password,
            full_name=user_data.full_name,
            phone=user_data.phone,
            role=user_data.role,
            language_preference=user_data.language_preference,
            region_code=user_data.region_code,
            is_active=True,
            is_verified=False
        )
        
        # Add to database
        db.add(user)
        await db.commit()
        await db.refresh(user)
        
        return user
    
    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """Create JWT access token"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
        
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt
    
    def verify_token(self, token: str) -> Optional[TokenData]:
        """Verify JWT token and return token data"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            user_id_str: str = payload.get("sub")
            email: str = payload.get("email")
            org_id_str: Optional[str] = payload.get("org_id")

            if user_id_str is None or email is None:
                return None

            # Convert string UUID to UUID object
            user_id = UUID(user_id_str)
            org_id = UUID(org_id_str) if org_id_str else None
            return TokenData(user_id=user_id, email=email, org_id=org_id)
        except (JWTError, ValueError):
            return None
    
    async def get_current_user(
        self,
        token: str = Depends(oauth2_scheme),
        db: AsyncSession = Depends(get_async_db)
    ) -> User:
        """Get current authenticated user from JWT token"""
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
        # Verify token
        token_data = self.verify_token(token)
        if token_data is None:
            raise credentials_exception
        
        # Get user from database
        user = await self.get_user_by_id(db, token_data.user_id)
        if user is None:
            raise credentials_exception
        
        # Check if user is active
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Inactive user"
            )
        
        return user
    
    async def verify_websocket_token(self, token: str) -> Optional[User]:
        """Verify token for WebSocket connections"""
        try:
            # Remove "Bearer " prefix if present
            if token.startswith("Bearer "):
                token = token[7:]

            # Verify token
            token_data = self.verify_token(token)
            if token_data is None:
                return None

            # Get database session
            async for db in get_async_db():
                user = await self.get_user_by_id(db, token_data.user_id)
                if user and user.is_active:
                    return user
                return None

        except Exception:
            return None
    
    async def update_user_last_login(self, db: AsyncSession, user: User) -> None:
        """Update user's last login timestamp"""
        user.last_login = datetime.utcnow()
        await db.commit()
    
    async def change_password(
        self,
        db: AsyncSession,
        user: User,
        current_password: str,
        new_password: str
    ) -> bool:
        """Change user password"""
        # Verify current password
        if not self.verify_password(current_password, user.hashed_password):
            return False
        
        # Hash new password
        user.hashed_password = self.get_password_hash(new_password)
        await db.commit()
        
        return True
    
    async def reset_password(self, db: AsyncSession, user: User, new_password: str) -> None:
        """Reset user password (admin function)"""
        user.hashed_password = self.get_password_hash(new_password)
        await db.commit()
    
    def create_password_reset_token(self, email: str) -> str:
        """Create password reset token"""
        data = {"email": email, "type": "password_reset"}
        expire = datetime.utcnow() + timedelta(hours=1)  # 1 hour expiry
        data.update({"exp": expire})
        return jwt.encode(data, self.secret_key, algorithm=self.algorithm)
    
    def verify_password_reset_token(self, token: str) -> Optional[str]:
        """Verify password reset token and return email"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            email: str = payload.get("email")
            token_type: str = payload.get("type")
            
            if email is None or token_type != "password_reset":
                return None
            
            return email
        except JWTError:
            return None
