async def makeController(device="/dev/ttyACM0"):
    from pywavez.SerialDeviceBase import makeSerialDevice
    from pywavez.SerialProtocol import SerialProtocol
    from pywavez.Controller import Controller

    sd = await makeSerialDevice(device)
    sp = SerialProtocol(sd)
    return await Controller(sp)
