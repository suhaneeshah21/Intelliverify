from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings


# Tells passlib to use bcrypt as the hashing algorithm
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plain_password:str)->str:
  """
    Takes a plain text password like 'mypassword123'
    Returns a bcrypt hash like '$2b$12$eImiTXuWVxfM37uY4JANjQ...'
    This hash is what gets saved to the database.
    """
  truncated = plain_password[:72]
  return pwd_context.hash(truncated)


def verify_password(plain_password:str, hashed_password:str)->bool:
  """
    Takes the plain password the user typed at login
    and the hash stored in the DB.
    Returns True if they match, False if not.
    """
  return pwd_context.verify(plain_password, hashed_password)






def create_access_token(subject:str,role:str,expires_delta: Optional[timedelta] = None)->str:
  """
    Creates a JWT token.
    The token contains: who the user is (subject), their role, and when it expires.
    This token is sent to the frontend after login.
    The frontend sends it back with every request in the Authorization header.
  """
  if expires_delta:
      expire = datetime.now(timezone.utc) + expires_delta
  else:
      expire = datetime.now(timezone.utc) + timedelta(
          minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
      )

  payload={
     "sub":subject,
     "role":role,
      "exp":expire,
      "iat":datetime.now(timezone.utc),
  }


  token=jwt.encode(payload,settings.JWT_SECRET_KEY,algorithm=settings.JWT_ALGORITHM)
  return token



def decode_access_token(token:str)->Optional[dict]:
  """
    Takes a JWT token string.
    Returns the payload dict (with sub, role, exp) if valid.
    Returns None if the token is expired or tampered with.
    """
  try:
     payload=jwt.decode(token,settings.JWT_SECRET_KEY,algorithms=[settings.JWT_ALGORITHM])
     return payload

  except JWTError:
    return None
     