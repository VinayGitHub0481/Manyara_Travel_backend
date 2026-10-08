from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.user import User, RoleEnum
from app.schemas.user import UserCreate, UserLogin
from app.core.security import hash_password, verify_password, create_access_token


def register_user(db: Session, payload: UserCreate) -> User:
    existing = (
        db.query(User)
        .filter(User.email == payload.email)
        .first()
    )

    if existing:
        raise HTTPException(
            status_code=400,
            detail="Email already registered",
        )

    # =========================================================
    # ADMIN REGISTRATION
    # An existing active admin must authorize creation
    # =========================================================
    if payload.role == RoleEnum.admin:
        if not payload.admin_verification_password:
            raise HTTPException(
                status_code=400,
                detail="Existing admin password is required",
            )

        existing_admin = (
            db.query(User)
            .filter(
                User.role == RoleEnum.admin,
                User.is_active == True,
            )
            .first()
        )

        if not existing_admin:
            raise HTTPException(
                status_code=400,
                detail="No existing admin account available for verification",
            )

        if not verify_password(
            payload.admin_verification_password,
            existing_admin.password_hash,
        ):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid existing admin password",
            )

    # =========================================================
    # CREATE USER
    # =========================================================
    user = User(
        name=payload.name,
        email=payload.email,
        password_hash=hash_password(payload.password),
        role=payload.role,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user

def authenticate_user(db: Session, payload: UserLogin) -> tuple[User, str]:
    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password"
        )
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account is disabled")

    token = create_access_token({"sub": str(user.id), "role": user.role.value})
    return user, token


def list_creators(db: Session) -> list[User]:
    return db.query(User).filter(User.role == RoleEnum.creator).all()


def set_user_active_status(db: Session, user_id: int, is_active: bool) -> User:
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.is_active = is_active
    db.commit()
    db.refresh(user)
    return user


def delete_user(db: Session, user_id: int) -> None:
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    db.delete(user)
    db.commit()
