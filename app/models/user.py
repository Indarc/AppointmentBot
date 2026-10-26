from sqlalchemy import BigInteger, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class User(Base):
    __tablename__ = "users"

    __table_args__ = (
        UniqueConstraint(
            "platform",
            "platform_user_id",
            name="uq_users_platform_user",
        ),
    )

    id: Mapped[int] = mapped_column(
        primary_key=True,
    )

    platform: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    platform_user_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    name: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )