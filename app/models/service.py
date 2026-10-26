from typing import TYPE_CHECKING

from sqlalchemy import Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.models import specialist_services

if TYPE_CHECKING:
    from app.models import Specialist


class Service(Base):
    __tablename__ = "services"

    id: Mapped[int] = mapped_column(primary_key=True)
    
    name: Mapped[str] = mapped_column(
        String(100), 
        nullable=False
    )

    specialists: Mapped[list["Specialist"]] = relationship(
        secondary=specialist_services,
        back_populates="services"
    )

    duration_minutes: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )

    price: Mapped[int] = mapped_column(
        Numeric(10, 2),
        nullable=False
    )