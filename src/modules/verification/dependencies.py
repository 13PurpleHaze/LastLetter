from fastapi.params import Depends

from modules.user.dependencies import get_user_service
from modules.user.service import UserService
from modules.verification.service import VerificationService


def get_verification_service(user_service: UserService = Depends(get_user_service)):
    verification_service = VerificationService(user_service=user_service)
    return verification_service
