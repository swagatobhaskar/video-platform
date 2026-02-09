from fastapi.routing import APIRouter
from fastapi.responses import JSONResponse
from fastapi import HTTPException, status, Depends
from sqlalchemy import select
from typing import cast

from app.schemas import user_schema
from app.database.session import AsyncSession
from app.utils.dependencies import get_current_user, get_db
from app.utils import security
from app.database.models import User

router = APIRouter(prefix="/api/user", tags=["user"])

@router.get("/", response_model=user_schema.UserOut, status_code=status.HTTP_200_OK)
async def get_user_profile(current_user: User = Depends(get_current_user)):
    # print("Headers at /api/user : ", request.headers)
    # query_params = request.query_params
    # print("COOKIES at /api/user :", request.cookies)
    # body = await request.json() if request.method == "POST" else None
    # return {
    #     "current_user": current_user,
    #     "headers": headers,
    #     "query_params": query_params,
    #     "cookies": cookies,
    #     "body": body,
    # }
    return current_user


@router.patch("/", response_model=user_schema.UpdateProfileResponse, status_code=status.HTTP_200_OK)
async def update_profile(
    updated_user_data: user_schema.UserPatch,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        result = await session.execute(
            select(User).where(User.id == current_user.id)
        )
        fetched_user = result.scalar_one_or_none()
        
        if not fetched_user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found!")
        
        if updated_user_data.email:
            # Check if new email is already taken
            result = await session.execute(
                select(User).where(User.email == updated_user_data.email)
            )
            existing_user = result.scalar_one_or_none()
            # Make sure the email isn't used by a different user
            if existing_user:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email is already taken!")
            
            fetched_user.email = updated_user_data.email

        # Update password if old_password is provided
        if updated_user_data.old_password:
            # Verify old password
            if not security.verify_password(updated_user_data.old_password, fetched_user.hashed_password):
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Incorrect old password!")

            # Hash the new password before saving it
            # Use cast(str, ...) to tell the type checker "this is now a string."
            # And, not None, as is in the schema- Optional[str].
            # Since, hash_password() doesn't accept None.
            fetched_user.hashed_password = security.hash_password(cast(str, updated_user_data.new_password))

        await session.commit()
        await session.refresh(fetched_user)

        return {
            "message": "Profile updated successfully.",
            "status_code": status.HTTP_200_OK,
            "user": fetched_user
        }
    
    except Exception as e:
        await session.rollback()
        print("e:: ", e)
        raise HTTPException(status_code=500, detail="Failed to update user information")

