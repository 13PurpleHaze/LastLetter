from datetime import datetime
from sqlalchemy import func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .role import Role
from .base import Base
from .capsule import Capsule


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
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), onupdate=func.now()
    )

    capsules: Mapped[list["Capsule"]] = relationship(
        secondary="user_capsule", back_populates="users"
    )
    roles: Mapped[list["Role"]] = relationship(secondary="user_role")
