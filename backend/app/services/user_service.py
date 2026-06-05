from sqlalchemy.orm import Session
from uuid import UUID

from app.models.user import User, UserRole
from app.schemas.schemas import UserCreate
from app.core.security import hash_password, verify_password


def get_user_by_email(db:Session,email:str)->User|None:
  """
    Looks up a user by email in the database.
    Returns the User object if found, None if not.
    Used during login and registration (to check duplicates).
  """

  return db.query(User).filter(User.email==email).first()

def get_user_by_id(db:Session,user_id:UUID)->User|None:
  """"
    Looks up a user by their UUID.
    Used in deps.py when decoding a JWT — we get the UUID from
    the token and fetch the full user object from DB.
  """

  return db.query(User).filter(User.id==user_id).first()


def create_user(db:Session,user_data:UserCreate)->User|None:
  """
    Registers a new user.
    Steps:
      1. Check if email already exists → raise error if yes
      2. Hash the plain text password
      3. Create a User model instance
      4. Save to DB and return the created user
    """
  

  existing_user=get_user_by_email(db,user_data.email)

  if existing_user:
    raise ValueError("Email already registered")
  
  hashed_password=hash_password(user_data.password)

  new_user=User(
    full_name=user_data.full_name,
    email=user_data.email,
    phone_number=user_data.phone_number,
    hashed_password=hashed_password,
    role=user_data.role
  )

  db.add(new_user)
  db.commit()
  db.refresh(new_user)  # refresh to get the generated ID and timestamps


  return new_user



def authenticate_user(db:Session,email:str,plain_password:str)->User|None:
  """
    Used at login.
    Steps:
      1. Find user by email → return None if not found
      2. Verify the plain password against the stored hash → return None if wrong
      3. Return the User object if everything matches
    The route will handle creating the JWT — this function only
    confirms the credentials are valid.
    """
  
  user=get_user_by_email(db,email)

  if not user:
    return None
  

  if not verify_password(plain_password,user.hashed_password):
    return None
  
  return user
  




  
