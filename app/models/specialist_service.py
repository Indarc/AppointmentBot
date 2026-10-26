from sqlalchemy import Column, ForeignKey, Table

from app.database.base import Base


specialist_services = Table(
    "specialist_services",
    Base.metadata,
    Column(
        "specialist_id",
        ForeignKey("specialists.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "service_id",
        ForeignKey("services.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)