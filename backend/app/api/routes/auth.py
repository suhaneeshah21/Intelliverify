from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user
from app.core.security import create_access_token
from app.models.user import User
from app.schemas.schemas import UserCreate, UserOut, LoginRequest, TokenResponse
from app.services.user_service import create_user, authenticate_user


router=APIRouter()

@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)


def register(user_data:UserCreate, db:Session=Depends(get_db)):

  """
    Registers a new user.
    - Validates the request body shape using UserCreate schema
    - Calls create_user service which checks duplicates + hashes password
    - Returns the created user as UserOut (no password)
    """
  try:
      new_user = create_user(db, user_data)
  except ValueError as e:
      # create_user raises ValueError if email already exists
      raise HTTPException(
          status_code=status.HTTP_400_BAD_REQUEST,
          detail=str(e)
      )

  return new_user


@router.post("/login", response_model=TokenResponse)

def login(login_data:LoginRequest,db:Session=Depends(get_db)):
    try:

        user=authenticate_user(db,login_data.email,login_data.password)
        if not user:
                # same error whether email is wrong OR password is wrong
                # never tell the caller which one failed
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid email or password.",
                    headers={"WWW-Authenticate": "Bearer"},
                )
        
        access_token=create_access_token(subject=str(user.id),role=user.role.value)

        return TokenResponse(access_token=access_token, token_type="bearer",role=user.role,user=UserOut.model_validate(user))
    except HTTPException:
        raise

    except Exception as e:
        print(f"LOGIN ERROR: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        raise


@router.get(
    "/me",
    response_model=UserOut
)
def get_me(
    current_user: User = Depends(get_current_user)  # JWT decoded + user fetched automatically
):
    """
    Returns the profile of whoever is currently logged in.
    No logic needed here — get_current_user dependency does all the work.
    Frontend calls this on app load to check if the session is still valid.
    """
    return current_user
