from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from src.database import get_db
from src.models import TeamMember, User
from src.security import ALGORITHM, SECRET_KEY


security = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    token = credentials.credentials

    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM],
        )

        user_id = payload.get("sub")

        if user_id is None:
            raise credentials_exception

        user_id = int(user_id)

    except (JWTError, ValueError):
        raise credentials_exception

    user = db.query(User).filter(User.id == user_id).first()

    if user is None:
        raise credentials_exception

    return user

def require_manager(
    current_user: User = Depends(get_current_user),
):
    if current_user.role != "manager":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Manager access required",
        )

    return current_user
def require_team_manager(
    team_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current_user.role == "manager":
        return current_user

    membership = (
        db.query(
            TeamMember
        )
        .filter(
            TeamMember.team_id == team_id,
            TeamMember.user_id == current_user.id,
        )
        .first()
    )

    if membership is None or membership.role not in ("admin", "team_head"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Team manager access required",
        )

    return current_user


