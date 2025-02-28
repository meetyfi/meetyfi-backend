from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2AuthorizationCodeBearer
from jose import JWTError, jwt
from app.config import get_settings
from app.db.mongodb import get_database
from bson import ObjectId

settings = get_settings()

# Custom OAuth2 scheme that doesn't require password
class OAuth2BearerWithCookie(OAuth2AuthorizationCodeBearer):
    def __init__(
        self,
        tokenUrl: str,
        auto_error: bool = True,
    ):
        super().__init__(
            authorizationUrl="",  # Not used for OTP flow
            tokenUrl=tokenUrl,
            auto_error=auto_error,
        )

oauth2_scheme = OAuth2BearerWithCookie(tokenUrl="api/v1/auth/verify-login")

async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
        
    db = await get_database()
    user = await db.users.find_one({"email": email})
    
    if user is None:
        raise credentials_exception
    
    if not user.get("is_verified", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email not verified"
        )
        
    user["_id"] = str(user["_id"])
    return user

async def get_current_manager(current_user = Depends(get_current_user)):
    if not current_user.get("is_manager", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The user doesn't have enough privileges"
        )
    return current_user