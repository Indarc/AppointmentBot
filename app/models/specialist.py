from typing import TYPE_CHECKING

from datetime import time, date

from sqlalchemy import CheckConstraint, Date, Integer, String, ForeignKey, Time
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

    working_hours: Mapped[list["SpecialistWorkingHours"]] = relationship(
        back_populates="specialist",
        cascade="all, delete-orphan",
    )

    breaks: Mapped[list["SpecialistBreak"]] = relationship(
        back_populates="specialist",
        cascade="all, delete-orphan",
    )

    services: Mapped[list["Service"]] = relationship(
        secondary=specialist_services,
        back_populates="specialists",
    )

class SpecialistWorkingHours(Base):
    __tablename__ = "specialist_working_hours"

    __table_args__ = (
        CheckConstraint(
            "weekday >= 0 AND weekday <= 6",
            name="ck_working_hours_weekday",
        ),
        CheckConstraint(
            "start_time < end_time",
            name="ck_working_hours_time_range",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)

    specialist_id: Mapped[int] = mapped_column(
        ForeignKey("specialists.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )

    start_time: Mapped[time] = mapped_column(
        Time,
        nullable=False,
    )

    end_time: Mapped[time] = mapped_column(
        Time,
        nullable=False,
    )

    specialist: Mapped["Specialist"] = relationship(
        back_populates="working_hours",
    )

    breaks: Mapped[list["SpecialistBreak"]] = relationship(
        back_populates="working_hours",
        cascade="all, delete-orphan",
    )

class SpecialistBreak(Base):
    __tablename__ = "specialist_breaks"

    __table_args__ = (
        CheckConstraint(
            "start_time < end_time",
            name="ck_breaks_time_range",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)

    working_hours_id: Mapped[int] = mapped_column(
        ForeignKey("specialist_working_hours.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    start_time: Mapped[time] = mapped_column(
        Time,
        nullable=False,
    )

    end_time: Mapped[time] = mapped_column(
        Time,
        nullable=False,
    )

    working_hours: Mapped["SpecialistWorkingHours"] = relationship(
        back_populates="breaks",
    )