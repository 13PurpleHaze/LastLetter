from datetime import datetime
from sqlalchemy import String, func, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base
from .user import User
from .content import Content


class Capsule(Base):
    __tablename__ = "capsules"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(20))
    text: Mapped[str | None]
    creator_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), onupdate=func.now()
    )
    users: Mapped[list["User"]] = relationship(
        secondary="user_capsule", back_populates="capsules"
    )
    contents: Mapped[list["Content"]] = relationship(back_populates="capsule")
