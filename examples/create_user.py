
import asyncio

from app.database.engine import async_session_factory
from app.models import User


async def main() -> None:
    async with async_session_factory() as session:
        async with session.begin():
            user = User(
                platform="telegram",
                platform_user_id="123456",
                name="Alex",
            )

            session.add(user)

        print(f"Пользователь создан: {user.id}")


if __name__ == "__main__":
    asyncio.run(main())
