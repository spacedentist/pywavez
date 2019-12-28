"""
This module implements the serial ZWave protocol as described in
https://web.archive.org/web/20181103092326/https://www.silabs.com/documents/\
login/user-guides/INS12350-Serial-API-Host-Appl.-Prg.-Guide.pdf
"""

import asyncio
import enum
import logging
import time
import typing

from .SerialDeviceBase import SerialDeviceBase
from .util import waitForOne, spawnTask


class FrameType(enum.Enum):
    SOF = 0x01
    ACK = 0x06
    NAK = 0x15
    CAN = 0x18


FrameType.values = frozenset(e.value for e in FrameType)


def calcChecksum(data: typing.ByteString) -> int:
    if len(data) > 255:
        raise Exception("bytearray too large")
    val = 0xFF ^ ((len(data) + 1) & 0xFF)
    for b in data:
        val ^= b
    return val


def frameMessage(payload: typing.ByteString) -> bytearray:
    return (
        bytearray((FrameType.SOF.value, len(payload) + 1))
        + payload
        + bytearray((calcChecksum(payload),))
    )


class SerialProtocol:
    def __init__(self, device: SerialDeviceBase) -> None:
        self.__dev = device
        self.__receivedMsgs = []
        self.__readerFinished = False
        self.__readerEvent = asyncio.Event()
        self.__sendMsgQueue = []
        self.__sendMsgEvent = asyncio.Event()
        self.__idleEvent = asyncio.Event()
        self.__task = spawnTask(self.__taskImpl())
        self.__task.add_done_callback(self.__setReaderFinished)

    def send(self, msg):
        fut = asyncio.Future()
        self.__sendMsgQueue.append((msg, fut))
        self.__sendMsgEvent.set()
        return fut

    def messageReady(self):
        return self.__receivedMsgs or self.__readerFinished

    async def waitForMessage(self):
        while not self.messageReady():
            await self.__readerEvent.wait()

    @property
    def idle(self):
        return self.__idleEvent.is_set()

    def waitForIdleState(self):
        return self.__idleEvent.wait()

    async def getMessage(
        self, timeout: typing.Optional[float] = None
    ) -> typing.Optional[bytearray]:
        if self.__receivedMsgs:
            msg = self.__receivedMsgs.pop(0)
            if not self.__receivedMsgs and not self.__readerFinished:
                self.__readerEvent.clear()
            return msg
        if timeout is not None:
            expire = time.monotonic() + timeout
        while not self.__readerFinished:
            try:
                await asyncio.wait_for(
                    self.__readerEvent.wait(),
                    None if timeout is None else expire - time.monotonic(),
                )
            except asyncio.TimeoutError:
                return
            if self.__receivedMsgs:
                msg = self.__receivedMsgs.pop(0)
                if not self.__receivedMsgs and not self.__readerFinished:
                    self.__readerEvent.clear()
                return msg
        else:
            raise StopIteration

    def __iter__(self):
        return self

    async def __next__(self) -> bytearray:
        while True:
            if self.__receivedMsgs:
                msg = self.__receivedMsgs.pop(0)
                if not self.__receivedMsgs and not self.__readerFinished:
                    self.__readerEvent.clear()
                return msg
            if self.__readerFinished:
                raise StopIteration
            await self.__readerEvent.wait()

    async def __taskImpl(self):
        await self.__dev.sendBreak()
        await asyncio.sleep(0.5)
        await self.__sendNak()

        while True:
            # idling about
            self.__idleEvent.set()
            await waitForOne(
                self.__dev.waitForData(), self.__sendMsgEvent.wait()
            )
            self.__idleEvent.clear()
            await self.__doStuff()

    async def __doStuff(self):
        if self.__dev.hasData():
            c = self.__dev.takeByte()
            if c != FrameType.SOF.value:
                if c not in FrameType.values:
                    return logging.warning(
                        f"Skipped byte 0x{c:02x} while expecting SOF"
                    )
                else:
                    return logging.warning(
                        f"Skipped {FrameType(c)} while expecting SOF"
                    )
                    return
            return await self.__receiveMsg()
        if self.__sendMsgQueue:
            await self.__sendMsg()

    async def __receiveMsg(self, *, cancel=False):
        expires = time.monotonic() + 1.5
        try:
            await asyncio.wait_for(self.__dev.waitForData(), 1.5)
        except asyncio.TimeoutError:
            logging.warning("Timeout while receiving message (1)")
            return
        length = self.__dev.takeByte() or 256
        try:
            await asyncio.wait_for(
                self.__dev.waitForData(length), expires - time.monotonic()
            )
        except asyncio.TimeoutError:
            return logging.warning("Timeout while receiving message (1)")
        payload = self.__dev.takeSomeData(length)
        chksum = payload.pop()
        if cancel:
            await self.__sendCan()
        elif calcChecksum(payload) == chksum:
            await self.__sendAck()
            self.__receivedMsgs.append(payload)
            self.__readerEvent.set()
        else:
            logging.warning("Checksum mismatch")
            await self.__sendNak()

    async def __sendMsg(self):
        while self.__sendMsgQueue:
            msg, fut = self.__sendMsgQueue.pop(0)
            if not fut.cancelled():
                break
        else:
            return self.__sendMsgEvent.clear()
        try:
            await self.__send(msg)
            expires = time.monotonic() + 1.6
            while True:
                timeout = expires - time.monotonic()
                if timeout <= 0:
                    raise asyncio.TimeoutError()
                await asyncio.wait_for(self.__dev.waitForData(), timeout)
                c = self.__dev.takeByte()
                if c == FrameType.ACK.value:
                    return fut.set_result(None)
                elif c in (FrameType.NAK.value, FrameType.CAN.value):
                    raise Exception(str(FrameType(c)))
                elif c == FrameType.SOF.value:
                    await self.__receiveMsg(cancel=True)
                    raise Exception(str(FrameType(c)))
                else:
                    logging.warning(
                        f"Skipped byte 0x{c:02x} while expecting ACK"
                    )
        except Exception as ex:
            fut.set_exception(ex)
        finally:
            if not self.__sendMsgQueue:
                self.__sendMsgEvent.clear()

    def __sendAck(self) -> typing.Awaitable[None]:
        return self.__dev.send(bytearray((FrameType.ACK.value,)))

    def __sendNak(self) -> typing.Awaitable[None]:
        return self.__dev.send(bytearray((FrameType.NAK.value,)))

    def __sendCan(self) -> typing.Awaitable[None]:
        return self.__dev.send(bytearray((FrameType.CAN.value,)))

    def __send(self, payload: typing.ByteString) -> typing.Awaitable[None]:
        return self.__dev.send(frameMessage(payload))

    def __setReaderFinished(self, *args):
        self.__readerFinished = True

    def close(self) -> typing.Awaitable[None]:
        return self.__dev.close()
