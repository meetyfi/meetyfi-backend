from fastapi import HTTPException, status

class CustomException(HTTPException):
    """Base class for custom exceptions"""
    def __init__(self, status_code: int, detail: str):
        super().__init__(status_code=status_code, detail=detail)

class CredentialsException(CustomException):
    """Exception raised for authentication errors"""
    def __init__(self, detail: str = "Could not validate credentials"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail
        )
        self.headers = {"WWW-Authenticate": "Bearer"}

class PermissionDeniedException(CustomException):
    """Exception raised for authorization errors"""
    def __init__(self, detail: str = "Not enough permissions"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail
        )

class UserNotFoundException(CustomException):
    """Exception raised when a resource is not found"""
    def __init__(self, resource_name: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{resource_name} not found"
        )

class NotFoundException(CustomException):
    """Exception raised when a resource is not found"""
    def __init__(self, resource_name: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{resource_name} not found"
        )

class ResourceExistsException(CustomException):
    """Exception raised when a resource already exists"""
    def __init__(self, resource_name: str):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"{resource_name} already exists"
        )

class OTPVerificationException(CustomException):
    """Exception raised when OTP is invalid"""
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired OTP"
        )

class VerificationTokenException(CustomException):
    """Exception raised when verification token is invalid"""
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification token"
        )

class AccountNotVerifiedException(CustomException):
    """Exception raised when account is not verified"""
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account not verified"
        )

class AccountNotApprovedException(CustomException):
    """Exception raised when manager account is not approved"""
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account not approved by admin"
        )

class InvalidMeetingStatusException(CustomException):
    """Exception raised when meeting status transition is invalid"""
    def __init__(self, detail: str = "Invalid meeting status transition"):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail
        )

class ValidationException(CustomException):
    """Exception raised for validation errors"""
    def __init__(self, detail: str):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=detail
        )