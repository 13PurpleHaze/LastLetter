from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import func, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .capsule import Capsule
    from .role import Role


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    first_name: Mapped[str]
    email: Mapped[str]
    password: Mapped[str]
    date_of_birth: Mapped[datetime]
    is_deceased: Mapped[bool] = mapped_column(default=False)
    email_verified: Mapped[bool] = mapped_column(default=False)
    is_active: Mapped[bool] = mapped_column(default=True)
    verificator_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), onupdate=func.now()
    )

    capsules: Mapped[list["Capsule"]] = relationship(
        secondary="user_capsule", back_populates="users"
    )
    roles: Mapped[list["Role"]] = relationship(secondary="user_role")

    verificator: Mapped["User | None"] = relationship(
        foreign_keys=[verificator_id],
        remote_side=[id],
    )
    users_for_verify: Mapped[list["User"]] = relationship(
        foreign_keys=[verificator_id],
        back_populates="verificator",
    )

    children: Mapped[list["User"]] = relationship(
        secondary="parent_child",
        primaryjoin="User.id == ParentChild.parent_id",
        secondaryjoin="User.id == ParentChild.child_id",
        back_populates="parents",
        lazy="selectin",
    )

    parents: Mapped[list["User"]] = relationship(
        secondary="parent_child",
        primaryjoin="User.id == ParentChild.child_id",
        secondaryjoin="User.id == ParentChild.parent_id",
        back_populates="children",
        lazy="selectin",
    )
