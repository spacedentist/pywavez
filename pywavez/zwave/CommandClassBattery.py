import enum

from pywavez.serialization.ZWaveSerialization import (
    ZWaveSerialization,
    ZWaveCommandClassBase,
)
from pywavez.zwave.Constants import CommandClass

fct = ZWaveSerialization.functionsModule()


class CommandClassBattery(ZWaveCommandClassBase):
    code = CommandClass.BATTERY
    name = "Battery"

    class BatteryLevel(enum.IntEnum):
        BATTERY_LOW_WARNING = 255


class CommandClassBatteryV1(CommandClassBattery):
    version = 1

    Get = ZWaveSerialization.createClass(
        "Get", [fct.zwaveCommand(_class=0x80, cmd=0x02)]
    )
    Report = ZWaveSerialization.createClass(
        "Report",
        [
            fct.zwaveCommand(_class=0x80, cmd=0x03),
            fct.uint8(
                field="batteryLevel", enum=CommandClassBattery.BatteryLevel
            ),
        ],
    )

    commands = {0x02: Get, 0x03: Report}


CommandClassBattery.versions = {1: CommandClassBatteryV1}
