
import asyncio

from app.database.base import Base
from app.database.engine import engine
import app.models  # noqa: F401


async def main() -> None:
    try:
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)

        print("Таблицы созданы")
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
