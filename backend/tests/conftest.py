import sys
import asyncio
import pytest

# On Windows, using the default ProactorEventLoop can cause "Event loop is closed"
# errors during asyncpg connection termination. Switching to SelectorEventLoop fixes this.
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


