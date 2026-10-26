
import asyncio

from sqlalchemy import text

from app.database.engine import engine


async def main() -> None:
    try:
        async with engine.connect() as connection:
            result = await connection.execute(text("SELECT 1"))
            print(f"Подключение успешно: {result.scalar_one()}")
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())