#!/usr/bin/env python3
"""
Script to create a super admin user for Ekumen platform
"""

import asyncio
import sys
import os
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import AsyncSessionLocal
from app.models.user import User, UserRole, UserStatus
from app.services.shared.auth_service import AuthService
import bcrypt


async def create_superadmin():
    """Create a super admin user"""
    
    # Super admin credentials
    SUPERADMIN_EMAIL = "admin@ekumen.com"
    SUPERADMIN_PASSWORD = "EkumenAdmin2024!"
    SUPERADMIN_NAME = "Ekumen Super Admin"
    
    print("🔧 Creating Ekumen Super Admin...")
    print(f"📧 Email: {SUPERADMIN_EMAIL}")
    print(f"🔑 Password: {SUPERADMIN_PASSWORD}")
    print(f"👤 Name: {SUPERADMIN_NAME}")
    print()
    
    async with AsyncSessionLocal() as db:
        try:
            # Check if super admin already exists
            auth_service = AuthService()
            existing_user = await auth_service.get_user_by_email(db, SUPERADMIN_EMAIL)
            
            if existing_user:
                if existing_user.is_superuser:
                    print("✅ Super admin already exists!")
                    print(f"   User ID: {existing_user.id}")
                    print(f"   Email: {existing_user.email}")
                    print(f"   Is Superuser: {existing_user.is_superuser}")
                    return existing_user
                else:
                    # Update existing user to super admin using raw SQL
                    print("🔄 Updating existing user to super admin...")
                    from sqlalchemy import text, select
                    
                    await db.execute(text("""
                        UPDATE users SET 
                            is_superuser = :is_superuser,
                            role = :role,
                            status = :status,
                            is_active = :is_active,
                            is_verified = :is_verified,
                            hashed_password = :hashed_password
                        WHERE id = :user_id
                    """), {
                        "is_superuser": True,
                        "role": "admin",
                        "status": "active",
                        "is_active": True,
                        "is_verified": True,
                        "hashed_password": auth_service.get_password_hash(SUPERADMIN_PASSWORD),
                        "user_id": existing_user.id
                    })
                    
                    await db.commit()
                    
                    # Fetch the updated user
                    result = await db.execute(
                        select(User).where(User.id == existing_user.id)
                    )
                    existing_user = result.scalar_one()
                    
                    print("✅ Existing user updated to super admin!")
                    print(f"   User ID: {existing_user.id}")
                    print(f"   Email: {existing_user.email}")
                    print(f"   Is Superuser: {existing_user.is_superuser}")
                    return existing_user
            
            # Create new super admin user
            print("🆕 Creating new super admin user...")
            
            # Hash password
            hashed_password = auth_service.get_password_hash(SUPERADMIN_PASSWORD)
            
            # Create user using raw SQL to handle enum types
            from sqlalchemy import text, select
            import uuid
            
            user_id = uuid.uuid4()
            
            await db.execute(text("""
                INSERT INTO users (
                    id, email, hashed_password, full_name, role, status,
                    is_active, is_verified, is_superuser, language_preference, timezone
                ) VALUES (
                    :id, :email, :hashed_password, :full_name, :role, :status,
                    :is_active, :is_verified, :is_superuser, :language_preference, :timezone
                )
            """), {
                "id": user_id,
                "email": SUPERADMIN_EMAIL,
                "hashed_password": hashed_password,
                "full_name": SUPERADMIN_NAME,
                "role": "admin",
                "status": "active",
                "is_active": True,
                "is_verified": True,
                "is_superuser": True,
                "language_preference": "fr",
                "timezone": "Europe/Paris"
            })
            
            await db.commit()
            
            # Fetch the created user
            result = await db.execute(
                select(User).where(User.id == user_id)
            )
            superadmin = result.scalar_one()
            
            print("✅ Super admin created successfully!")
            print(f"   User ID: {superadmin.id}")
            print(f"   Email: {superadmin.email}")
            print(f"   Name: {superadmin.full_name}")
            print(f"   Role: {superadmin.role}")
            print(f"   Is Superuser: {superadmin.is_superuser}")
            print(f"   Status: {superadmin.status}")
            print()
            
            return superadmin
            
        except Exception as e:
            print(f"❌ Error creating super admin: {e}")
            await db.rollback()
            raise


async def test_superadmin_login():
    """Test super admin login"""
    print("🧪 Testing super admin login...")
    
    SUPERADMIN_EMAIL = "admin@ekumen.com"
    SUPERADMIN_PASSWORD = "EkumenAdmin2024!"
    
    async with AsyncSessionLocal() as db:
        try:
            auth_service = AuthService()
            
            # Test authentication
            user = await auth_service.authenticate_user(db, SUPERADMIN_EMAIL, SUPERADMIN_PASSWORD)
            
            if user and user.is_superuser:
                print("✅ Super admin login test successful!")
                print(f"   User ID: {user.id}")
                print(f"   Email: {user.email}")
                print(f"   Is Superuser: {user.is_superuser}")
                
                # Test JWT token creation
                token = auth_service.create_access_token(data={"sub": str(user.id)})
                print(f"   JWT Token: {token[:50]}...")
                
                return True
            else:
                print("❌ Super admin login test failed!")
                return False
                
        except Exception as e:
            print(f"❌ Error testing super admin login: {e}")
            return False


async def main():
    """Main function"""
    print("🚀 Ekumen Super Admin Setup")
    print("=" * 50)
    
    try:
        # Create super admin
        superadmin = await create_superadmin()
        
        # Test login
        login_success = await test_superadmin_login()
        
        print()
        print("📋 Super Admin Credentials:")
        print("=" * 30)
        print(f"Email: admin@ekumen.com")
        print(f"Password: EkumenAdmin2024!")
        print()
        
        print("🔗 API Endpoints:")
        print("=" * 20)
        print("POST /api/v1/auth/login")
        print("GET  /api/v1/admin/organizations")
        print("GET  /api/v1/admin/users")
        print("GET  /api/v1/admin/analytics")
        print("GET  /api/v1/admin/health")
        print()
        
        if login_success:
            print("✅ Super admin setup completed successfully!")
        else:
            print("⚠️  Super admin created but login test failed!")
            
    except Exception as e:
        print(f"❌ Super admin setup failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
