from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime

from .base import Base


class UserCapsule(Base):
    __tablename__ = "user_capsule"

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", onupdate="CASCADE", ondelete="CASCADE"), primary_key=True
    )
    capsule_id: Mapped[int] = mapped_column(
        ForeignKey("capsules.id", onupdate="CASCADE", ondelete="CASCADE"),
        primary_key=True,
    )

    send_at: Mapped[datetime | None]
    sent_at: Mapped[datetime | None]
    is_sent: Mapped[bool] = mapped_column(default=False)
