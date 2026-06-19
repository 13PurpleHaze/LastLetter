from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import String, func, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .capsule import Capsule


class Content(Base):
    __tablename__ = "contents"

    id: Mapped[int] = mapped_column(primary_key=True)
    object_key: Mapped[str] = mapped_column(String(255))
    content_type: Mapped[str] = mapped_column(String(100))
    size_bytes: Mapped[int]
    order_index: Mapped[int]
    capsule_id: Mapped[int] = mapped_column(ForeignKey("capsules.id"))
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), onupdate=func.now()
    )
    capsule: Mapped["Capsule"] = relationship(back_populates="contents")
