from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.enum import BookingStatus, BookingDeleteReason
from app.models.booking import Booking
from app.models.service import Service
from app.models.specialist import Specialist
from app.models.specialist_service import specialist_services


class BookingService:
    @staticmethod
    async def create_booking(
        session: AsyncSession,
        user_id: int,
        service_id: int,
        specialist_id: int,
        starts_at: datetime,
    ) -> Booking:
        # Check if the specialist offers the service
        service = await session.get(Service, service_id)

        if service is None:
            raise ValueError(f"Service with id {service_id} not found")

        # Validate the booking time
        if starts_at.tzinfo is None or starts_at.utcoffset() is None:
            raise ValueError("Booking time must include a timezone")

        if starts_at <= datetime.now(timezone.utc):
            raise ValueError("Booking time must be in the future")

        # Check if the specialist offers the service
        specialist = await session.get(Specialist, specialist_id)

        if specialist is None:
            raise ValueError(f"Specialist with id {specialist_id} not found")

        ends_at = starts_at + timedelta(
            minutes=service.duration_minutes
        )

        # Check if the specialist offers the service
        query = select(specialist_services).where(
            specialist_services.c.specialist_id == specialist_id,
            specialist_services.c.service_id == service_id,
        )
        result = await session.execute(query)

        if result.first() is None:
            raise ValueError(
                f"Specialist with id {specialist_id} does not offer service with id {service_id}"
            )

        query = select(Booking).where(
            Booking.specialist_id == specialist_id,
            Booking.starts_at < ends_at,
            Booking.ends_at > starts_at,
            Booking.status != BookingStatus.CANCELLED,
        )

        result = await session.execute(query)
        if result.first() is not None:
            raise ValueError(
                f"Specialist with id {specialist_id} is not available at the requested time"
            )

        booking = Booking(
            user_id=user_id,
            service_id=service_id,
            specialist_id=specialist_id,
            status=BookingStatus.PENDING,
            price=service.price,
            duration_minutes=service.duration_minutes,
            starts_at=starts_at,
            ends_at=ends_at,
        )

        session.add(booking)
        await session.flush()
        
        return booking

    async def get_booking_by_id(
        self, session: AsyncSession, booking_id: int
    ) -> Booking | None:
        return await session.get(Booking, booking_id)

    async def delete_booking(self, session: AsyncSession, booking_id: int, reason: BookingDeleteReason) -> None:
        booking = await self.get_booking_by_id(session, booking_id)
        if booking is None:
            raise ValueError(f"Booking with id {booking_id} not found")

        await session.delete(booking)
        await session.flush()

    