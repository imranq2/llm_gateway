import asyncio
import time
from typing import Optional
from uuid import uuid4, UUID


class ExpiringCache[T]:
    def __init__(self, *, ttl_seconds: float) -> None:
        self._cache: Optional[T] = None
        self._cache_timestamp: Optional[float] = None
        self._lock: asyncio.Lock = asyncio.Lock()
        self._ttl: float = ttl_seconds
        self._identifier: UUID = uuid4()

    def is_valid(self) -> bool:
        if self._cache is None or self._cache_timestamp is None:
            return False
        current_time: float = time.time()
        return current_time - self._cache_timestamp < self._ttl

    async def get(self) -> Optional[T]:
        if self.is_valid():
            return self._cache
        return None

    async def set(self, value: T) -> None:
        async with self._lock:
            self._cache = value
            self._cache_timestamp = time.time()

    async def clear(self) -> None:
        async with self._lock:
            self._cache = None
            self._cache_timestamp = None

    @property
    def lock(self) -> asyncio.Lock:
        return self._lock
