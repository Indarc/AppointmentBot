
import asyncio

from sqlalchemy import select

from app.database.engine import async_session_factory
from app.models import User


async def main() -> None:
    async with async_session_factory() as session:
        statement = select(User).where(
            User.platform == "telegram",
            User.platform_user_id == "123456",
        )

        result = await session.execute(statement)
        user = result.scalar_one_or_none()

        if user is None:
            print("Пользователь не найден")
        else:
            print(user.id, user.name)


if __name__ == "__main__":
    asyncio.run(main())
