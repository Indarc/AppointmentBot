from typing import TYPE_CHECKING

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.models.specialist_service import specialist_services

if TYPE_CHECKING:
    from app.models import Service


class Specialist(Base):
    __tablename__ = "specialists"

    id: Mapped[int] = mapped_column(primary_key=True)

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    services: Mapped[list["Service"]] = relationship(
        secondary=specialist_services,
        back_populates="specialists",
    )