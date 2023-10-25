from fastapi import HTTPException, status


class CredentialsException(HTTPException):
    """UNAUTHORIZED 401"""

    def __init__(self, *args, **kwargs):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )


class ForbiddenException(HTTPException):
    """FORBIDDEN 403"""

    def __init__(self, *args, **kwargs):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access rights",
        )


class AlreadyExistsException(HTTPException):
    """BAD_REQUEST 400"""

    def __init__(self, *args, **kwargs):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Already Exists",
        )


class NotFoundException(HTTPException):
    """NOT_FOUND 404"""

    def __init__(self, *args, **kwargs):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Not Found",
        )
