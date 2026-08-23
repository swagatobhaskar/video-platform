from app.exceptions.base import AppException

# 401 Unauthorized actually means "you aren't successfully authenticated."
# 403 Forbidden means "I know who you are, but you're not allowed to do this."

class AuthenticationRequired(AppException):
    status_code = 401
    error_code = "AUTHENTICATION_REQUIRED"
    message = "Authentication is required."


class InvalidToken(AppException):
    status_code = 401
    error_code = "INVALID_TOKEN"
    message = "Invalid authentication token."


class TokenExpired(AppException):
    status_code = 401
    error_code = "TOKEN_EXPIRED"
    message = "Authentication token has expired."


class InvalidCredentials(AppException):
    status_code = 401
    error_code = "INVALID_CREDENTIALS"
    message = "Invalid email or password."


class UserNotFound(AppException):
    status_code = 404
    error_code = "USER_NOT_FOUND"
    message = "User not found."


class UserInactive(AppException):
    status_code = 403
    error_code = "USER_INACTIVE"
    message = "User account is inactive."


class InvalidRefreshToken(AppException):
    status_code = 401
    error_code = "INVALID_REFRESH_TOKEN"
    message = "Invalid refresh token."


class RefreshTokenExpired(AppException):
    status_code = 401
    error_code = "REFRESH_TOKEN_EXPIRED"
    message = "Refresh token has expired."


class PermissionDenied(AppException):
    status_code = 403
    error_code = "PERMISSION_DENIED"
    message = "You do not have permission to perform this action."


"""
One thing I'd change for JWTs. You don't necessarily need separate InvalidToken and TokenExpired exceptions.
From a security perspective, many applications deliberately return the same external response for both:

{
  "success": false,
  "error": "AUTHENTICATION_REQUIRED",
  "message": "Authentication is required."
}

while logging the actual reason internally.

That's especially useful because you generally don't want authentication endpoints leaking unnecessary information.
For example:

try:
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
except ExpiredSignatureError:
    raise TokenExpired()
except JWTError:
    raise InvalidToken()

Your frontend can then decide:

401 → attempt refresh
refresh succeeds → retry request
refresh fails → clear auth state / redirect to login

So for your architecture, I'd probably have authentication exceptions at the application layer,
exactly like your video/upload/series exceptions, rather than raising FastAPI HTTPException directly from your authentication service.
"""
