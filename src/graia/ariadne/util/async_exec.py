"""本模块提供并行执行器, 及方便函数 `io_bound`, `cpu_bound`.
"""
import asyncio
import functools
import importlib
import multiprocessing
from asyncio.events import AbstractEventLoop
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from typing import Awaitable, Callable, ClassVar, Dict

from ..typing import P, R


def IS_MAIN_PROCESS():
    return multiprocessing.parent_process() is None


def _reg_sigint():
    import signal
    import sys

    signal.signal(signal.SIGINT, lambda *_, **__: sys.exit())


class ParallelExecutor:
    """并行执行器."""

    thread_exec: ThreadPoolExecutor
    proc_exec: ProcessPoolExecutor
    loop_ref_dict: ClassVar[Dict[AbstractEventLoop, "ParallelExecutor"]] = {}
    func_mapping: ClassVar[Dict[str, Callable[P, R]]] = {}

    def __init__(
        self,
        loop: AbstractEventLoop = None,
        max_thread: int = None,
        max_process: int = None,
    ):
        """初始化并行执行器.

        Args:
            loop (AbstractEventLoop, optional): 要绑定的事件循环, 会自动获取当前事件循环. Defaults to None.
            max_thread (int, optional): 最大线程数. Defaults to None.
            max_process (int, optional): 最大进程数. Defaults to None.

        `max_thread` 与 `max_process` 参数默认值请参阅 `concurrent.futures`.
        """
        self.thread_exec = ThreadPoolExecutor(max_workers=max_thread)
        self.proc_exec = ProcessPoolExecutor(
            max_workers=max_process, initializer=_reg_sigint
        )  # see issue #50
        self.bind_loop(loop or asyncio.get_running_loop())

    @classmethod
    def get(cls, loop: AbstractEventLoop = None):
        loop = loop or asyncio.get_running_loop()
        if loop not in cls.loop_ref_dict:
            cls.loop_ref_dict[loop] = ParallelExecutor()
        return cls.loop_ref_dict[loop]

    def bind_loop(self, loop: AbstractEventLoop):
        self.loop_ref_dict[loop] = self

    @classmethod
    def shutdown(cls):
        for exec in cls.loop_ref_dict.values():
            exec.close()

    def close(self):
        self.thread_exec.shutdown()
        self.proc_exec.shutdown()

    @classmethod
    def run_func(cls, name: str, module: str, args: tuple, kwargs: dict) -> R:
        importlib.import_module(module)
        return cls.func_mapping[name](*args, **kwargs)

    @classmethod
    def run_func_static(cls, func: Callable[P, R], args: tuple, kwargs: dict) -> R:
        if func.__qualname__ in cls.func_mapping:
            func = cls.func_mapping[func.__qualname__]
        return func(*args, **kwargs)

    def to_thread(self, func: Callable[P, R], *args: P.args, **kwargs: P.kwargs) -> Awaitable[R]:
        """在线程中异步运行 func 函数.

        Args:
            func (Callable[P, R]): 要调用的函数.
            *args (P.args): 附带的位置参数.
            **kwargs (P.kwargs): 附带的关键词参数.

        Returns:
            Future[R]: 返回结果. 需要被异步等待.
        """
        return asyncio.get_running_loop().run_in_executor(
            self.thread_exec,
            ParallelExecutor.run_func_static,
            func,
            args,
            kwargs,
        )

    def to_process(self, func: Callable[P, R], *args: P.args, **kwargs: P.kwargs) -> Awaitable[R]:
        """在进程中异步运行 func 函数. 需要先注册过才行.

        Args:
            func (Callable[P, R]): 要调用的函数.
            *args (P.args): 附带的位置参数.
            **kwargs (P.kwargs): 附带的关键词参数.

        Returns:
            Future[R]: 返回结果. 需要被异步等待.
        """
        return asyncio.get_running_loop().run_in_executor(
            self.proc_exec,
            ParallelExecutor.run_func_static,
            func,
            args,
            kwargs,
        )


def io_bound(func: Callable[P, R]) -> Callable[P, Awaitable[R]]:
    ParallelExecutor.func_mapping[func.__qualname__] = func

    @functools.wraps(func)
    async def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        loop = asyncio.get_running_loop()
        executor = ParallelExecutor.get(loop)
        return await loop.run_in_executor(
            executor.thread_exec,
            ParallelExecutor.run_func,
            func.__qualname__,
            func.__module__,
            args,
            kwargs,
        )

    return wrapper


def cpu_bound(func: Callable[P, R]) -> Callable[P, Awaitable[R]]:
    ParallelExecutor.func_mapping[func.__qualname__] = func

    @functools.wraps(func)
    async def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        loop = asyncio.get_running_loop()
        executor = ParallelExecutor.get(loop)
        return await loop.run_in_executor(
            executor.proc_exec,
            ParallelExecutor.run_func,
            func.__qualname__,
            func.__module__,
            args,
            kwargs,
        )

    return wrapper
