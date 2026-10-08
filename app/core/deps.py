from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from datetime import datetime,timezone,timedelta 
from app.db.database import get_db
from app.core.security import decode_access_token
from app.models.user import User, RoleEnum

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")



# Admin session inactivity limit
ADMIN_INACTIVITY_LIMIT = timedelta(minutes=30)


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    payload = decode_access_token(token)

    if payload is None:
        raise credentials_exception

    user_id = payload.get("sub")

    if user_id is None:
        raise credentials_exception

    try:
        user_id = int(user_id)
    except (TypeError, ValueError):
        raise credentials_exception

    user = (
        db.query(User)
        .filter(User.id == user_id)
        .first()
    )

    if user is None or not user.is_active:
        raise credentials_exception

    # ---------------------------------------------------------
    # ADMIN INACTIVITY CHECK
    # ---------------------------------------------------------
    if user.role == RoleEnum.admin:

        now = datetime.now(timezone.utc)

        # If the admin has been inactive for 30 minutes,
        # reject the request.
        if user.last_activity_at is not None:

            last_activity = user.last_activity_at

            # Handle databases returning a naive datetime
            if last_activity.tzinfo is None:
                last_activity = last_activity.replace(
                    tzinfo=timezone.utc
                )

            if now - last_activity >= ADMIN_INACTIVITY_LIMIT:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Admin session expired due to inactivity",
                    headers={"WWW-Authenticate": "Bearer"},
                )

        # -----------------------------------------------------
        # Update last activity
        # -----------------------------------------------------
        user.last_activity_at = now
        db.commit()
        db.refresh(user)

    return user



def require_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != RoleEnum.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return current_user


def require_admin_or_creator(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role not in (RoleEnum.admin, RoleEnum.creator):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not permitted"
        )
    return current_user
