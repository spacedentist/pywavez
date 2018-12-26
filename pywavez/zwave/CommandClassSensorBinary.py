import enum

from pywavez.serialization.ZWaveSerialization import (
    ZWaveSerialization,
    ZWaveCommandClassBase,
)
from pywavez.zwave.Constants import CommandClass

fct = ZWaveSerialization.functionsModule()


class CommandClassSensorBinary(ZWaveCommandClassBase):
    code = CommandClass.SENSOR_BINARY
    name = "SensorBinary"

    class SensorValue(enum.IntEnum):
        IDLE = 0
        DETECTED_AN_EVENT = 255

    class SensorType(enum.IntEnum):
        RESERVED = 0
        GENERAL = 1
        SMOKE = 2
        CO = 3
        CO2 = 4
        HEAT = 5
        WATER = 6
        FREEZE = 7
        TAMPER = 8
        AUX = 9
        DOOR_WINDOW = 10
        TILT = 11
        MOTION = 12
        GLASS_BREAK = 13
        FIRST = 255


class CommandClassSensorBinaryV1(CommandClassSensorBinary):
    version = 1

    Get = ZWaveSerialization.createClass(
        "Get", [fct.zwaveCommand(_class=0x30, cmd=0x02)]
    )
    Report = ZWaveSerialization.createClass(
        "Report",
        [
            fct.zwaveCommand(_class=0x30, cmd=0x03),
            fct.uint8(
                field="sensorValue", enum=CommandClassSensorBinary.SensorValue
            ),
        ],
    )

    commands = {0x02: Get, 0x03: Report}


class CommandClassSensorBinaryV2(CommandClassSensorBinaryV1):
    version = 2

    SupportedGetSensor = ZWaveSerialization.createClass(
        "SupportedGetSensor", [fct.zwaveCommand(_class=0x30, cmd=0x01)]
    )
    Get = ZWaveSerialization.createClass(
        "Get",
        [
            fct.zwaveCommand(_class=0x30, cmd=0x02),
            fct.uint8(
                field="sensorType", enum=CommandClassSensorBinary.SensorType
            ),
        ],
    )
    Report = ZWaveSerialization.createClass(
        "Report",
        [
            fct.zwaveCommand(_class=0x30, cmd=0x03),
            fct.uint8(
                field="sensorValue", enum=CommandClassSensorBinary.SensorValue
            ),
            fct.uint8(
                field="sensorType", enum=CommandClassSensorBinary.SensorType
            ),
        ],
    )
    SupportedSensorReport = ZWaveSerialization.createClass(
        "SupportedSensorReport",
        [
            fct.zwaveCommand(_class=0x30, cmd=0x04),
            fct.bitset(field="bitMask", bytes=None),
        ],
    )

    commands = {
        0x01: SupportedGetSensor,
        0x02: Get,
        0x03: Report,
        0x04: SupportedSensorReport,
    }


CommandClassSensorBinary.versions = {
    1: CommandClassSensorBinaryV1,
    2: CommandClassSensorBinaryV2,
}
