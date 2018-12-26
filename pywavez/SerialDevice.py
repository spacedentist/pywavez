import asyncio
import typing

from asyncinit import asyncinit
import serial_asyncio

from pywavez.SerialDeviceBase import SerialDeviceBase


@asyncinit
class SerialDevice(SerialDeviceBase):
    async def __init__(self, device: str):
        super().__init__()

        loop = asyncio.get_event_loop()
        self.__reader = asyncio.StreamReader(loop=loop)
        transport, protocol = await serial_asyncio.create_serial_connection(
            loop=loop,
            protocol_factory=lambda: asyncio.StreamReaderProtocol(
                self.__reader, loop=loop
            ),
            url=device,
            baudrate=115200,
            rtscts=True,
        )
        self.__writer = asyncio.StreamWriter(
            transport, protocol, self.__reader, loop
        )
        self.__serial = transport.serial
        self.__writeLock = asyncio.Lock()
        self.__readerTask = asyncio.create_task(self.__readerImpl())

    async def sendBreak(self) -> bool:
        async with self.__writeLock:
            self.__serial.break_condition = True
            await asyncio.sleep(0.25)
            self.__serial.break_condition = False
        return True

    async def __readerImpl(self) -> None:
        while True:
            r = await self.__reader.read(1024)
            if not r:
                break
            self._receivedData += r
            self._notify()
        self._readEOF = True
        self._notify()

    async def send(self, data: typing.ByteString) -> None:
        async with self.__writeLock:
            self.__writer.write(data)
            await self.__writer.drain()

    async def close(self) -> None:
        self.__readerTask.cancel()
        self.__writer.close()
        await self.__writer.wait_closed()
