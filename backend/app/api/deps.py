from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from uuid import UUID

from app.db.session import SessionLocal
from app.core.security import decode_access_token
from app.models.user import User, UserRole
from app.services.user_service import get_user_by_id


# Tells FastAPI where the login endpoint is
# When a route uses this, FastAPI automatically reads
# the Authorization: Bearer <token> header
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_db():
  """
    Opens a DB session before the request.
    Guarantees it closes after the request — even if an error occurs.
    Every route that touches the DB gets this injected via Depends(get_db).
    """
  
  db= SessionLocal()
  try:
    yield db
  finally:
    db.close()




def get_current_user(token:str=Depends(oauth2_scheme),db:Session=Depends(get_db))->User:
  """
    Decodes the JWT token from the request header.
    Fetches the matching user from DB.
    Returns the User object to the route.
    Raises 401 if token is missing, expired, or invalid.
    """
  
  credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials.",
        headers={"WWW-Authenticate": "Bearer"},
    )
  
  payload=decode_access_token(token)
  if payload is None:
    raise credentials_exception
  
  user_id:str=payload.get("sub")
  if user_id is None:
    raise credentials_exception
  

  user=get_user_by_id(db, UUID(user_id))
  if user is None:
    raise credentials_exception
  

  if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This account has been deactivated."
        )

  return user


def require_admin(current_user:User=Depends(get_current_user)) -> User:
   """
    Use this dependency on any route that only admins can access.
    Raises 403 if the logged-in user is not an admin or superadmin.
    """
   
   if current_user.role not in [UserRole.ADMIN, UserRole.SUPERADMIN]:
      raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required."
        )
   
   return current_user




def require_candidate(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Use this dependency on any route that only candidates can access.
    Raises 403 if the logged-in user is not a candidate.
    """
    if current_user.role != UserRole.CANDIDATE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Candidate access required."
        )
    return current_user


def require_superadmin(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Use this on routes only the superadmin can access.
    Example — creating new admin accounts, configuring org settings.
    """
    if current_user.role != UserRole.SUPERADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Superadmin access required."
        )
    return current_user


   