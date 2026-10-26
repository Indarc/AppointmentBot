import asyncio

from app.database.engine import async_session_factory
from app.models import User


async def main() -> None:
    async with async_session_factory() as session:
        async with session.begin():
            obj = await session.get(User, 3)

            if obj is None:
                print("Пользователь не найден")
                return

            await session.delete(obj)

        print("Пользователь удален")


if __name__ == "__main__":
    asyncio.run(main())