from __future__ import annotations

import asyncio
from concurrent.futures import ThreadPoolExecutor
from functools import partial
from typing import Any, Callable, TypeVar

T = TypeVar("T")


async def run_blocking(func: Callable[..., T], /, *args: Any, **kwargs: Any) -> T:
    """Run blocking work without leaving Python's default executor alive."""
    loop = asyncio.get_running_loop()
    call = partial(func, *args, **kwargs)
    with ThreadPoolExecutor(max_workers=1) as executor:
        return await loop.run_in_executor(executor, call)

