from typing import Annotated

from fastapi import APIRouter, Depends, status

from api.v1.schemas.failed_response import FailedResponseSchema
from api.v1.schemas.pagination import ListResponseSchema, PaginationParams
from api.v1.schemas.success_response import SuccessResponseSchema
from core.constants import RoleSlug
from modules.auth.dependencies import (
    get_current_user_with_roles,
)
from modules.capsules.dependencies import get_capsule_service, get_capsule_filter
from modules.capsules.schemas import (
    CapsuleCreateSchema,
    CapsuleUserAttachSchema,
    UploadUrlRequestSchema,
    ContentCreateSchema,
    ContentSchema,
    CapsuleUpdateSchema,
    CapsuleSchema,
    CapsuleFilterSchema,
    UploadUrlResponseSchema,
    CapsuleLightSchema,
    UserCapsuleSchema,
)
from modules.capsules.service import CapsuleService
from modules.user.schemas import CurrentUserSchema
from services.s3.client import S3Client
from services.s3.dependency import get_s3_client

router = APIRouter(prefix="/capsules", tags=["Capsules"])


@router.get(
    path="/extensions",
    description="Получить список доступных расширений для контента",
    response_model=SuccessResponseSchema,
    responses={
        status.HTTP_200_OK: {"model": SuccessResponseSchema[list[str]]},
    },
)
def get_allowed_extensions():
    extensions = CapsuleService.get_allowed_extensions()
    return SuccessResponseSchema(result=extensions)


@router.get(
    path="/capsules/recipient",
    description="Получить список капсул, где текущий пользователь является получателем (ребенком)",
    responses={
        status.HTTP_200_OK: {
            "model": SuccessResponseSchema[ListResponseSchema[CapsuleLightSchema]]
        },
        status.HTTP_401_UNAUTHORIZED: {"model": FailedResponseSchema},
        status.HTTP_403_FORBIDDEN: {"model": FailedResponseSchema},
        status.HTTP_422_UNPROCESSABLE_CONTENT: {"model": FailedResponseSchema},
    },
)
async def get_capsules_by_recipient(
    pagination: Annotated[PaginationParams, Depends()],
    capsule_filter: Annotated[CapsuleFilterSchema, Depends()],
    current_user: CurrentUserSchema = Depends(
        get_current_user_with_roles([RoleSlug.CHILD])
    ),
    capsule_service: CapsuleService = Depends(get_capsule_service),
):
    filter = get_capsule_filter(capsule_filter=capsule_filter)
    capsules, meta = await capsule_service.get_capsules_by_recipient(
        filter=filter,
        current_user=current_user,
        pagination=pagination,
    )
    return SuccessResponseSchema(result=ListResponseSchema(items=capsules, meta=meta))


@router.get(
    path="",
    description="Получить все капсулы текущего пользователя (родителя)",
    responses={
        status.HTTP_200_OK: {
            "model": SuccessResponseSchema[ListResponseSchema[CapsuleLightSchema]]
        },
        status.HTTP_401_UNAUTHORIZED: {"model": FailedResponseSchema},
        status.HTTP_403_FORBIDDEN: {"model": FailedResponseSchema},
        status.HTTP_422_UNPROCESSABLE_CONTENT: {"model": FailedResponseSchema},
    },
)
async def get_capsules_by_creator(
    pagination: Annotated[PaginationParams, Depends()],
    capsule_filter: Annotated[CapsuleFilterSchema, Depends()],
    current_user: CurrentUserSchema = Depends(
        get_current_user_with_roles([RoleSlug.PARENT])
    ),
    capsule_service: CapsuleService = Depends(get_capsule_service),
):
    filter = get_capsule_filter(capsule_filter=capsule_filter)
    capsules, meta = await capsule_service.get_capsules_by_creator(
        filter=filter,
        current_user=current_user,
        pagination=pagination,
    )
    return SuccessResponseSchema(result=ListResponseSchema(items=capsules, meta=meta))


@router.post(
    path="",
    description="Создать пустую капсулу без медиа, только название и текст",
    responses={
        status.HTTP_201_CREATED: {"model": SuccessResponseSchema[CapsuleLightSchema]},
        status.HTTP_401_UNAUTHORIZED: {"model": FailedResponseSchema},
        status.HTTP_403_FORBIDDEN: {"model": FailedResponseSchema},
        status.HTTP_422_UNPROCESSABLE_CONTENT: {"model": FailedResponseSchema},
    },
)
async def create_capsule(
    capsule: CapsuleCreateSchema,
    current_user: CurrentUserSchema = Depends(
        get_current_user_with_roles([RoleSlug.PARENT])
    ),
    capsule_service: CapsuleService = Depends(get_capsule_service),
):
    created_capsule = await capsule_service.create_capsule(
        capsule_create=capsule, creator_id=current_user.id
    )
    return SuccessResponseSchema(result=created_capsule)


@router.get(
    path="/{capsule_id}",
    description="Получить капсулу по id",
    responses={
        status.HTTP_200_OK: {"model": SuccessResponseSchema[CapsuleSchema]},
        status.HTTP_401_UNAUTHORIZED: {"model": FailedResponseSchema},
        status.HTTP_403_FORBIDDEN: {"model": FailedResponseSchema},
        status.HTTP_422_UNPROCESSABLE_CONTENT: {"model": FailedResponseSchema},
    },
)
async def get_capsule(
    capsule_id: int,
    current_user: CurrentUserSchema = Depends(
        get_current_user_with_roles([RoleSlug.PARENT, RoleSlug.CHILD])
    ),
    capsule_service: CapsuleService = Depends(get_capsule_service),
):
    capsule = await capsule_service.get_capsule_by_id(
        capsule_id=capsule_id, current_user=current_user
    )
    return SuccessResponseSchema(result=capsule)


@router.patch(
    path="/{capsule_id}",
    description="Обновить капсулу по id для текущего пользователя",
    responses={
        status.HTTP_200_OK: {"model": SuccessResponseSchema[CapsuleSchema]},
        status.HTTP_401_UNAUTHORIZED: {"model": FailedResponseSchema},
        status.HTTP_403_FORBIDDEN: {"model": FailedResponseSchema},
        status.HTTP_422_UNPROCESSABLE_CONTENT: {"model": FailedResponseSchema},
    },
)
async def update_capsule(
    capsule_id: int,
    capsule_update: CapsuleUpdateSchema,
    current_user: CurrentUserSchema = Depends(
        get_current_user_with_roles([RoleSlug.PARENT])
    ),
    capsule_service: CapsuleService = Depends(get_capsule_service),
):
    capsule = await capsule_service.update_capsule(
        capsule_id=capsule_id,
        capsule_update=capsule_update,
        current_user=current_user,
    )
    return SuccessResponseSchema(result=capsule)


@router.delete(
    path="/{capsule_id}",
    description="Удалить капсулу",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        status.HTTP_401_UNAUTHORIZED: {"model": FailedResponseSchema},
        status.HTTP_403_FORBIDDEN: {"model": FailedResponseSchema},
        status.HTTP_422_UNPROCESSABLE_CONTENT: {"model": FailedResponseSchema},
    },
)
async def delete_capsule(
    capsule_id: int,
    current_user: CurrentUserSchema = Depends(
        get_current_user_with_roles([RoleSlug.PARENT])
    ),
    capsule_service: CapsuleService = Depends(get_capsule_service),
):
    await capsule_service.delete_capsule(
        capsule_id=capsule_id, current_user=current_user
    )
    return SuccessResponseSchema(result={})


@router.post(
    path="/{capsule_id}/users",
    description="Привязать пользователя как ребенка (получателя) к капсуле",
    response_model=SuccessResponseSchema,
    responses={
        status.HTTP_201_CREATED: {"model": SuccessResponseSchema[UserCapsuleSchema]},
        status.HTTP_401_UNAUTHORIZED: {"model": FailedResponseSchema},
        status.HTTP_403_FORBIDDEN: {"model": FailedResponseSchema},
        status.HTTP_422_UNPROCESSABLE_CONTENT: {"model": FailedResponseSchema},
    },
)
async def attach_user(
    capsule_id: int,
    user: CapsuleUserAttachSchema,
    current_user: CurrentUserSchema = Depends(
        get_current_user_with_roles([RoleSlug.PARENT])
    ),
    capsule_service: CapsuleService = Depends(get_capsule_service),
):
    user_capsule = await capsule_service.attach_user(
        capsule_id=capsule_id,
        user_attach=user,
        current_user=current_user,
    )
    return SuccessResponseSchema(result=user_capsule)


@router.delete(
    path="/{capsule_id}/users/{user_id}/",
    description="Отвязать пользователя как ребенка (получателя) от капсулы",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        status.HTTP_401_UNAUTHORIZED: {"model": FailedResponseSchema},
        status.HTTP_403_FORBIDDEN: {"model": FailedResponseSchema},
        status.HTTP_422_UNPROCESSABLE_CONTENT: {"model": FailedResponseSchema},
    },
)
async def detach_user(
    capsule_id: int,
    user_id: int,
    current_user: CurrentUserSchema = Depends(
        get_current_user_with_roles([RoleSlug.PARENT, RoleSlug.ADMIN])
    ),
    capsule_service: CapsuleService = Depends(get_capsule_service),
):
    await capsule_service.detach_user(
        capsule_id=capsule_id,
        user_id=user_id,
        current_user=current_user,
    )
    return SuccessResponseSchema(result={})


@router.post(
    path="/{capsule_id}/media/upload-url",
    description="Получить ссылку на загрузку контента",
    response_model=SuccessResponseSchema,
    responses={
        status.HTTP_200_OK: {"model": SuccessResponseSchema[UploadUrlResponseSchema]},
        status.HTTP_401_UNAUTHORIZED: {"model": FailedResponseSchema},
        status.HTTP_422_UNPROCESSABLE_CONTENT: {"model": FailedResponseSchema},
    },
)
async def get_upload_url(
    capsule_id: int,
    request: UploadUrlRequestSchema,
    current_user: CurrentUserSchema = Depends(
        get_current_user_with_roles([RoleSlug.PARENT])
    ),
    capsule_service: CapsuleService = Depends(get_capsule_service),
    s3_client: S3Client = Depends(get_s3_client),
):
    url = await capsule_service.get_upload_url(
        capsule_id=capsule_id,
        request=request,
        current_user=current_user,
        s3_client=s3_client,
    )
    return SuccessResponseSchema(result=url)


@router.post(
    path="/{capsule_id}/media/confirm-upload",
    description="Подтвердить загрузку контента в хранилище",
    response_model=SuccessResponseSchema,
    responses={
        status.HTTP_201_CREATED: {"model": SuccessResponseSchema[ContentSchema]},
        status.HTTP_401_UNAUTHORIZED: {"model": FailedResponseSchema},
        status.HTTP_422_UNPROCESSABLE_CONTENT: {"model": FailedResponseSchema},
    },
)
async def confirm_upload_content(
    capsule_id: int,
    content: ContentCreateSchema,
    current_user: CurrentUserSchema = Depends(
        get_current_user_with_roles([RoleSlug.PARENT])
    ),
    capsule_service: CapsuleService = Depends(get_capsule_service),
    s3_client: S3Client = Depends(get_s3_client),
):
    created_content = await capsule_service.confirm_upload_content(
        capsule_id=capsule_id,
        content_create=content,
        current_user=current_user,
        s3_client=s3_client,
    )
    return SuccessResponseSchema(result=created_content)


@router.get(
    path="/{capsule_id}/media/{content_id}/",
    description="Получить ссылку на скачивание контента для родителей и для детей",
    response_model=SuccessResponseSchema,
    responses={
        status.HTTP_200_OK: {"model": SuccessResponseSchema[UploadUrlResponseSchema]},
        status.HTTP_401_UNAUTHORIZED: {"model": FailedResponseSchema},
        status.HTTP_422_UNPROCESSABLE_CONTENT: {"model": FailedResponseSchema},
    },
)
async def get_download_url(
    capsule_id: int,
    content_id: int,
    current_user: CurrentUserSchema = Depends(
        get_current_user_with_roles([RoleSlug.PARENT, RoleSlug.CHILD])
    ),
    capsule_service: CapsuleService = Depends(get_capsule_service),
    s3_client: S3Client = Depends(get_s3_client),
):
    url = await capsule_service.get_download_url(
        capsule_id=capsule_id,
        content_id=content_id,
        current_user=current_user,
        s3_client=s3_client,
    )
    return SuccessResponseSchema(result=url)


@router.delete(
    path="/{capsule_id}/media/{content_id}/",
    description="Удалить контент из капсулы",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        status.HTTP_401_UNAUTHORIZED: {"model": FailedResponseSchema},
        status.HTTP_403_FORBIDDEN: {"model": FailedResponseSchema},
        status.HTTP_422_UNPROCESSABLE_CONTENT: {"model": FailedResponseSchema},
    },
)
async def delete_object(
    capsule_id: int,
    content_id: int,
    current_user: CurrentUserSchema = Depends(
        get_current_user_with_roles([RoleSlug.PARENT])
    ),
    capsule_service: CapsuleService = Depends(get_capsule_service),
    s3_client: S3Client = Depends(get_s3_client),
):
    await capsule_service.delete_content(
        capsule_id=capsule_id,
        content_id=content_id,
        current_user=current_user,
        s3_client=s3_client,
    )
    return SuccessResponseSchema(result={})
