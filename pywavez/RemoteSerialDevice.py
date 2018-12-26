import asyncio
import traceback
import typing

from asyncinit import asyncinit

from pywavez.SerialDeviceBase import SerialDeviceBase


@asyncinit
class RemoteSerialDevice(SerialDeviceBase):
    async def __init__(self, host: str, port: int):
        super().__init__()
        self.__reader, self.__writer = await asyncio.open_connection(
            host, port
        )
        self.__readerTask = asyncio.create_task(self.__readerImpl())

    async def __readerImpl(self) -> None:
        while True:
            r = await self.__reader.read(1024)
            if not r:
                break
            self._receivedData += r
            self._notify()
        self._readEOF = True
        self._notify()

    async def sendBreak(self) -> bool:
        self.__writer.write(b"\x11")

    async def send(self, data: typing.ByteString) -> None:
        self.__writer.write(escape(data))

    async def close(self) -> None:
        self.__writer.write_eof()


def escape(data):
    return data.replace(b"\x10", b"\x10\x00").replace(b"\x11", b"\x10\x01")


def unescape(data):
    return data.replace(b"\x10\x01", b"\x11").replace(b"\x10\x00", b"\x10")


async def amain():
    import argparse
    from pywavez.SerialDevice import SerialDevice
    from pywavez.util import waitForOne

    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, required=True)
    parser.add_argument("--device", required=True)
    options = parser.parse_args()

    connection_open = {"_": False}

    async def read_task(sd, writer):
        while True:
            await sd.waitForData()
            data = sd.takeAllData()
            if data:
                writer.write(data)
                await writer.drain()
            elif sd.atEOF():
                break

    async def write_task(sd, reader):
        data = bytearray()
        while True:
            r = await reader.read(1024)
            if not r:
                break
            data += r
            if data[-1] == 0x10:
                send = data[0:-1]
                data = bytearray((0x10,))
            else:
                send = data
                data = bytearray()
            pos = 0
            while pos < len(send):
                dc1 = send.find(b"\x11", pos)
                if dc1 < 0:
                    await sd.send(unescape(send[pos:]))
                    break
                else:
                    if dc1 > pos:
                        await sd.send(unescape[pos:dc1])
                    pos = dc1 + 1
                    await sd.sendBreak()

    async def client_connected_cb(reader, writer):
        if connection_open["_"]:
            writer.write_eof()
            return
        connection_open["_"] = True
        sd = None
        try:
            sd = await SerialDevice(options.device)
            rt = asyncio.create_task(read_task(sd, writer))
            wt = asyncio.create_task(write_task(sd, reader))
            await waitForOne(rt, wt)
        except Exception:
            traceback.print_exc()
            raise
        finally:
            if sd is not None:
                await sd.close()
            connection_open["_"] = False

    server = await asyncio.start_server(client_connected_cb, port=options.port)
    async with server:
        await server.serve_forever()


def main():
    asyncio.run(amain())


if __name__ == "__main__":
    main()
