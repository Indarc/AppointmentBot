from datetime import date, datetime, time, timedelta
from typing import cast
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.enum import BookingStatus
from app.models.booking import Booking
from app.models.service import Service
from app.models.specialist import SpecialistBreak, SpecialistWorkingHours, Specialist
from app.models.specialist_service import specialist_services


class SchedulerService:

    @staticmethod
    async def create_schedule(
        session: AsyncSession,
        specialist_id: int,
        day: date,
        start_at: time,
        end_at: time,
    ) -> None:
        """Создаёт рабочий интервал специалиста."""

        if start_at >= end_at:
            raise ValueError(
                "Время начала должно быть раньше времени окончания."
            )

        specialist = await session.get(Specialist, specialist_id)
        if specialist is None:
            raise ValueError(
                f"Специалист с id={specialist_id} не найден."
            )

        # Проверяем пересечение с существующими рабочими интервалами.
        result = await session.execute(
            select(SpecialistWorkingHours).where(
                SpecialistWorkingHours.specialist_id == specialist_id,
                SpecialistWorkingHours.date == day,
                SpecialistWorkingHours.start_time < end_at,
                SpecialistWorkingHours.end_time > start_at,
            )
        )

        if result.scalars().first() is not None:
            raise ValueError(
                f"Рабочее время пересекается с существующим расписанием "
                f"на {day}: "
                f"{start_at.isoformat(timespec='minutes')} - "
                f"{end_at.isoformat(timespec='minutes')}."
            )

        working_period = SpecialistWorkingHours(
            specialist_id=specialist_id,
            date=day,
            start_time=start_at,
            end_time=end_at,
        )

        session.add(working_period)
        await session.flush()

    @staticmethod
    async def create_break(
        session: AsyncSession,
        specialist_id: int,
        day: date,
        start_at: time,
        end_at: time,
    ) -> None:
        """Создаёт перерыв внутри рабочего интервала."""

        if start_at >= end_at:
            raise ValueError(
                "Время начала перерыва должно быть раньше окончания."
            )

        specialist = await session.get(Specialist, specialist_id)
        if specialist is None:
            raise ValueError(
                f"Специалист с id={specialist_id} не найден."
            )

        # Находим рабочий интервал, содержащий перерыв.
        result = await session.execute(
            select(SpecialistWorkingHours).where(
                SpecialistWorkingHours.specialist_id == specialist_id,
                SpecialistWorkingHours.date == day,
                SpecialistWorkingHours.start_time <= start_at,
                SpecialistWorkingHours.end_time >= end_at,
            )
        )

        working_period = result.scalars().first()

        if working_period is None:
            raise ValueError(
                f"Не найден рабочий интервал для специалиста "
                f"id={specialist_id} на {day}, содержащий перерыв "
                f"{start_at.isoformat(timespec='minutes')} - "
                f"{end_at.isoformat(timespec='minutes')}."
            )

        # Проверяем пересечение с другими перерывами.
        result = await session.execute(
            select(SpecialistBreak).where(
                SpecialistBreak.working_hours_id == working_period.id,
                SpecialistBreak.start_time < end_at,
                SpecialistBreak.end_time > start_at,
            )
        )

        if result.scalars().first() is not None:
            raise ValueError(
                "Перерыв пересекается с уже существующим перерывом."
            )

        break_period = SpecialistBreak(
            working_hours_id=working_period.id,
            start_time=start_at,
            end_time=end_at,
        )

        session.add(break_period)
        await session.flush()

    @staticmethod
    async def get_available_slots(
        session: AsyncSession,
        specialist_id: int,
        service_id: int,
        day: date,
    ) -> list[datetime]:
        """Возвращает доступное время для записи."""

        specialist = await session.get(Specialist, specialist_id)
        if specialist is None:
            raise ValueError(f"Not found specialist with id {specialist_id}")
        
        service = await session.get(Service, service_id)
        if service is None:
            raise ValueError(f"Not found service with id {service_id}")

        BUSINESS_TZ = ZoneInfo("Europe/Moscow")

        # Проверка, оказывает ли специалист выбранную услугу.
        result = await session.execute(
            select(specialist_services.c.specialist_id).where(
                specialist_services.c.specialist_id == specialist_id,
                specialist_services.c.service_id == service_id,
            )
        )
        if result.first() is None:
            raise ValueError(
                f"Specialist with id {specialist_id} does not offer "
                f"service with id {service_id}"
            )

        # Получение рабочих интервалов по дате.
        result = await session.execute(
            select(SpecialistWorkingHours)
            .where(
                SpecialistWorkingHours.specialist_id == specialist_id,
                SpecialistWorkingHours.date == day,
            )
            .options(selectinload(SpecialistWorkingHours.breaks))
            .order_by(SpecialistWorkingHours.start_time)
        )
        working_periods = result.scalars().all()

        if not working_periods:
            return []

        day_start = datetime.combine(day, datetime.min.time(), tzinfo=BUSINESS_TZ)
        day_end = datetime.combine(
            day + timedelta(days=1),
            datetime.min.time(),
            tzinfo=BUSINESS_TZ,
        )

        # Загрузка записи, пересекающие этот день. Отменённые записи не занимают время.
        result = await session.execute(
            select(Booking).where(
                Booking.specialist_id == specialist_id,
                Booking.starts_at < day_end,
                Booking.ends_at > day_start,
                Booking.status != BookingStatus.CANCELLED,
            )
        )
        bookings = result.scalars().all()

        duration = timedelta(minutes=service.duration_minutes)
        step = timedelta(minutes=10)
        slots: set[datetime] = set()

        for period in working_periods:
            period_start = datetime.combine(day, period.start_time, tzinfo=BUSINESS_TZ)
            period_end = datetime.combine(day, period.end_time, tzinfo=BUSINESS_TZ)

            candidate = period_start
            while candidate + duration <= period_end:
                candidate_end = candidate + duration

                overlaps_break = any(
                    candidate < datetime.combine(day, pause.end_time, tzinfo=BUSINESS_TZ)
                    and candidate_end
                    > datetime.combine(day, pause.start_time, tzinfo=BUSINESS_TZ)
                    for pause in period.breaks
                )
                overlaps_booking = any(
                    candidate < cast(datetime, booking.ends_at)
                    and candidate_end > cast(datetime, booking.starts_at)
                    for booking in bookings
                )

                if not overlaps_break and not overlaps_booking:
                    slots.add(candidate)

                candidate += step

        return sorted(slots)


    @staticmethod
    async def get_working_hours(
        session: AsyncSession,
        specialist_id: int,
        day: date,
    ) -> list[tuple[time, time]]:
        """Возвращает рабочие часы специалиста на дату."""

        # Проверка наличия специалиста в базе-данных
        specialist = await session.get(Specialist, specialist_id)
        if specialist is None:
            raise ValueError(f"Not found specialist with id {specialist_id}")

        # Получаем рабочие часы по дню недели
        result = await session.execute(
            select(SpecialistWorkingHours)
            .where(
                SpecialistWorkingHours.specialist_id == specialist_id,
                SpecialistWorkingHours.date == day
            )
        )

        working_periods = result.scalars().all()

        if not working_periods:
            raise ValueError(f"Специалист не работает в данный день {day}")

        working_hours = []
        for period in working_periods:
            working_hours.append((period.start_time, period.end_time))
        working_hours.sort()
        return working_hours
        

    @staticmethod
    async def is_available(
        session: AsyncSession,
        specialist_id: int,
        service_id: int,
        starts_at: datetime,
    ) -> bool:
        """Проверяет доступность выбранного времени."""

        specialist = await session.get(Specialist, specialist_id)
        if specialist is None:
            raise ValueError(f"Not found specialist with id {specialist_id}")

        available_slots = await __class__.get_available_slots(session, specialist_id, service_id, day=starts_at.date())
        free_slots = []
        for slot in available_slots:
            if slot.time() >= starts_at.time():
                free_slots.append(slot)
        if not free_slots:
            return False
        return True
