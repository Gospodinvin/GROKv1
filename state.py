import time
import asyncio

class TTLState:
    def __init__(self, ttl):
        self.ttl = ttl
        self.data = {}
        self.lock = asyncio.Lock()

    async def set(self, uid, key, val):
        async with self.lock:
            self.data[uid] = {"_exp": time.time()+self.ttl, key: val}

    async def get(self, uid, key):
        async with self.lock:
            d = self.data.get(uid)
            if not d or d["_exp"] < time.time():
                self.data.pop(uid, None)
                return None
            return d.get(key)

    async def clear(self, uid):
        async with self.lock:
            self.data.pop(uid, None)