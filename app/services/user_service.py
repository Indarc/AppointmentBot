from unittest import result

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User


class UserService:
    @staticmethod
    async def create_user(
        session: AsyncSession,
        platform: str,
        platform_user_id: str,
        name: str
    ) -> None:
        """Создаёт нового пользователя"""

        # Проверка создан ли юзер с данныым id
        result = await session.execute(
            select(User)
            .where(
                User.platform == platform,
                User.platform_user_id == platform_user_id,
            )
        )
        user = result.scalars().first()
        if user is not None:
            raise ValueError(f"Пользователь с id :{platform_user_id} существует на плотформе {platform}.")

        user = User(
            platform=platform,
            platform_user_id=platform_user_id,
            name=name,
        )
        session.add(user)
        await session.flush()

    @staticmethod
    async def get_user(
        session: AsyncSession,
        user_id: int
    ) -> User:
        """Возвращает юзера"""
        user = await session.get(User, user_id)

        if user is None:
            raise ValueError(f"Пользователь с id {user_id} не найден.")

        return user