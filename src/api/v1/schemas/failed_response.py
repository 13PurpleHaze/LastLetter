from pydantic import BaseModel


class FailedDetailSchema(BaseModel):
    code: str
    message: str


class FailedResponseSchema(BaseModel):
    success: bool = False
    error: FailedDetailSchema
