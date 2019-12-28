import asyncio
import typing
import re


class SerialDeviceBase:
    def __init__(self):
        self._receivedData = bytearray()
        self._receivedDataNotifications = []
        self._readEOF = False

    def hasData(self) -> bool:
        return bool(self._receivedData)

    def atEOF(self) -> bool:
        return self._readEOF

    def takeAllData(self) -> bytearray:
        data = self._receivedData
        self._receivedData = bytearray()
        return data

    def takeSomeData(self, bytes: int) -> bytearray:
        if bytes > len(self._receivedData):
            raise Exception("not enough data available")
        res = self._receivedData[0:bytes]
        self._receivedData = self._receivedData[bytes:]
        return res

    def takeByte(self) -> int:
        return self._receivedData.pop(0)

    def waitForData(self, bytes=1):
        fut = asyncio.Future()
        if len(self._receivedData) >= bytes:
            fut.set_result(None)
        else:
            self._receivedDataNotifications.append((bytes, fut))
        return fut

    def _notify(self):
        if not self._receivedData:
            return
        notifications = self._receivedDataNotifications
        self._receivedDataNotifications = []
        for b, fut in notifications:
            if not fut.cancelled():
                if len(self._receivedData) >= b:
                    fut.set_result(None)
                elif self._readEOF:
                    fut.set_exception(EOFError())
                else:
                    self._receivedDataNotifications.append((b, fut))

    def __iter__(self):
        return self

    async def __next__(self) -> bytearray:
        while True:
            await self.waitForData()
            if self.hasData():
                return self.takeAllData()
            if self._readEOF:
                raise StopIteration


def makeSerialDevice(dev) -> typing.Awaitable[SerialDeviceBase]:
    match = re.match(r"^([\w\-\.:]+):(\d+)$", dev)
    if match:
        host, port = match.groups()
        port = int(port)
        from pywavez.RemoteSerialDevice import RemoteSerialDevice

        return RemoteSerialDevice(host, port)
    else:
        from pywavez.SerialDevice import SerialDevice

        return SerialDevice(dev)
