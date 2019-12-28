import asyncio
import bisect
import collections
import enum
import time

from pywavez.util import waitForOne


class Priority(enum.IntEnum):
    POLLING = -100
    INITALIZATION = -10
    DEFAULT = 0
    INTERACTIVE = 100
    WAKE_UP = 99999


class TransmissionBase(asyncio.Future):
    def __init__(
        self,
        message,
        *,
        nodeId=None,
        endpoint=0,
        priority=Priority.DEFAULT,
        response_handler=None,
    ):
        super().__init__()
        self.message = message
        self.nodeId = nodeId
        self.endpoint = endpoint
        self.priority = priority
        self.responseHandler = response_handler
        self.transmitting = False
        self.retransmission = 0
        self.maxRetransmissions = 3
        self.pauseUntil = None

    def __lt__(self, other):
        return other.priority < self.priority


class MessageTransmission(TransmissionBase):
    ...


class CommandTransmission(TransmissionBase):
    ...


class SimpleQueue:
    def __init__(self):
        self.__messages = collections.deque()
        self.__event = asyncio.Event()

    def append(self, message):
        self.__messages.append(message)
        self.__event.set()

    def hasMessage(self):
        return bool(self.__messages)

    async def waitForMessage(self):
        while not self.__messages:
            self.__event.clear()
            await self.__event.wait()

    def takeMessage(self):
        message = self.__messages.popleft()
        return message

    async def getMessage(self):
        await self.waitForMessage()
        return self.takeMessage()


class MessageQueue:
    def __init__(self):
        self.__messages = []
        self.__event = asyncio.Event()

    def add(self, message):
        bisect.insort_right(self.__messages, message)
        self.__event.set()

    def addFirst(self, message):
        bisect.insort_left(self.__messages, message)
        self.__event.set()

    def hasMessage(self):
        now = time.monotonic()
        for m in self.__messages:
            if m.pauseUntil is None or m.pauseUntil < now:
                if not m.cancelled():
                    return True
        return False

    async def waitForMessage(self, timeout=None):
        if timeout is not None:
            expires = time.monotonic() + timeout
        else:
            expires = None
        while True:
            now = time.monotonic()
            if expires is not None and now >= expires:
                return
            pause_until = expires
            for m in self.__messages:
                if m.cancelled():
                    continue
                if m.pauseUntil is None or m.pauseUntil < now:
                    return
                elif pause_until is None or pause_until > m.pauseUntil:
                    pause_until = m.pauseUntil
            self.__event.clear()
            if pause_until is None:
                await self.__event.wait()
            else:
                await waitForOne(
                    self.__event.wait(), timeout=pause_until - now
                )

    def takeMessage(self):
        now = time.monotonic()
        idx = 0
        while idx < len(self.__messages):
            m = self.__messages[idx]
            if m.cancelled():
                self.__messages.pop(idx)
                continue
            if m.pauseUntil is None or m.pauseUntil < now:
                return self.__messages.pop(idx)
            idx += 1
        raise IndexError("no message available")

    async def getMessage(self):
        await self.waitForMessage()
        return self.takeMessage()
