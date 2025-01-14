import asyncio

from graia.broadcast import Broadcast
from loguru import logger

from graia.ariadne.adapter import CombinedAdapter
from graia.ariadne.model import MiraiSession

if __name__ == "__main__":
    url = input()
    account = input()
    verify_key = input()

    loop = asyncio.new_event_loop()
    bcc = Broadcast(loop=loop)
    adapter = CombinedAdapter(bcc, MiraiSession(url, account, verify_key))

    try:
        loop.run_until_complete(adapter.fetch_cycle())
    except KeyboardInterrupt:
        loop.run_until_complete(adapter.fetch_task)
