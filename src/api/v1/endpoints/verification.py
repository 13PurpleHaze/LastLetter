from typing import Annotated

from fastapi import APIRouter, status
from fastapi.params import Depends

from api.v1.schemas.failed_response import FailedResponseSchema
from api.v1.schemas.pagination import ListResponseSchema, PaginationParams
from api.v1.schemas.success_response import SuccessResponseSchema
from core.constants import RoleSlug
from modules.auth.dependencies import get_current_user_with_roles
from modules.user.schemas import CurrentUserSchema
from modules.verification.dependencies import get_verification_service
from modules.verification.service import VerificationService

router = APIRouter(prefix="/verification", tags=["Verification"])


@router.get(
    path="/users",
    description="Список пользователей(родителей) для верификации смерти для текущего пользователя(верификатора)",
    responses={
        status.HTTP_200_OK: {
            "model": SuccessResponseSchema[ListResponseSchema[CurrentUserSchema]]
        },
        status.HTTP_401_UNAUTHORIZED: {"model": FailedResponseSchema},
        status.HTTP_403_FORBIDDEN: {"model": FailedResponseSchema},
        status.HTTP_422_UNPROCESSABLE_CONTENT: {"model": FailedResponseSchema},
    },
)
async def get_users_for_verification(
    pagination: Annotated[PaginationParams, Depends()],
    verification_service: VerificationService = Depends(get_verification_service),
    current_user: CurrentUserSchema = Depends(
        get_current_user_with_roles([RoleSlug.VERIFIER, RoleSlug.ADMIN])
    ),
):
    users, meta = await verification_service.get_users(
        current_user=current_user, pagination=pagination
    )
    return SuccessResponseSchema(result=ListResponseSchema(items=users, meta=meta))


# TODO: мб сделать откат или email confirm этого действия
@router.post(
    path="/users/{user_id}",
    description="Подтвердить смерть пользователя(родителя)",
    responses={
        status.HTTP_200_OK: {"model": SuccessResponseSchema[CurrentUserSchema]},
        status.HTTP_401_UNAUTHORIZED: {"model": FailedResponseSchema},
        status.HTTP_403_FORBIDDEN: {"model": FailedResponseSchema},
        status.HTTP_422_UNPROCESSABLE_CONTENT: {"model": FailedResponseSchema},
    },
)
async def verify_death(
    user_id: int,
    verification_service: VerificationService = Depends(get_verification_service),
    current_user: CurrentUserSchema = Depends(
        get_current_user_with_roles([RoleSlug.VERIFIER, RoleSlug.ADMIN])
    ),
):
    updated_user = await verification_service.verify_death(
        user_id=user_id,
        current_user=current_user,
    )
    return SuccessResponseSchema(result=updated_user)
