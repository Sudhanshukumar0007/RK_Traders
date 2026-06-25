import asyncio
from sqlalchemy import text
from app.core.database import AsyncSessionLocal

async def f():
    async with AsyncSessionLocal() as db:
        r = await db.execute(text("select * from brands"))
        print("Brands:")
        for row in r.all():
            print(" ", row)
        r2 = await db.execute(text("select * from categories"))
        print("Categories:")
        for row in r2.all():
            print(" ", row)

asyncio.run(f())
