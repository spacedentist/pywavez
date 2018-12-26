import enum

from pywavez.serialization.ZWaveSerialization import (
    ZWaveSerialization,
    ZWaveCommandClassBase,
)
from pywavez.zwave.Constants import CommandClass

fct = ZWaveSerialization.functionsModule()


class CommandClassSwitchBinary(ZWaveCommandClassBase):
    code = CommandClass.SWITCH_BINARY
    name = "SwitchBinary"

    class SwitchValue(enum.IntEnum):
        OFF_DISABLE = 0
        ON_ENABLE = 255

    class Duration(enum.IntEnum):
        INSTANTLY = 0
        UNKNOWN_DURATION = 254
        DEFAULT = 255


class CommandClassSwitchBinaryV1(CommandClassSwitchBinary):
    version = 1

    Set = ZWaveSerialization.createClass(
        "Set",
        [
            fct.zwaveCommand(_class=0x25, cmd=0x01),
            fct.uint8(
                field="value", enum=CommandClassSwitchBinary.SwitchValue
            ),
        ],
    )
    Get = ZWaveSerialization.createClass(
        "Get", [fct.zwaveCommand(_class=0x25, cmd=0x02)]
    )
    Report = ZWaveSerialization.createClass(
        "Report",
        [
            fct.zwaveCommand(_class=0x25, cmd=0x03),
            fct.uint8(
                field="value", enum=CommandClassSwitchBinary.SwitchValue
            ),
        ],
    )

    commands = {0x01: Set, 0x02: Get, 0x03: Report}


class CommandClassSwitchBinaryV2(CommandClassSwitchBinaryV1):
    version = 2

    Set = ZWaveSerialization.createClass(
        "Set",
        [
            fct.zwaveCommand(_class=0x25, cmd=0x01),
            fct.uint8(
                field="value", enum=CommandClassSwitchBinary.SwitchValue
            ),
            fct.uint8(
                field="duration",
                enum=CommandClassSwitchBinary.Duration,
                defaultValue=CommandClassSwitchBinary.Duration.INSTANTLY,
            ),
        ],
    )
    Report = ZWaveSerialization.createClass(
        "Report",
        [
            fct.zwaveCommand(_class=0x25, cmd=0x03),
            fct.uint8(
                field="value", enum=CommandClassSwitchBinary.SwitchValue
            ),
            fct.uint8(
                field="targetValue", enum=CommandClassSwitchBinary.SwitchValue
            ),
            fct.uint8(
                field="duration", enum=CommandClassSwitchBinary.Duration
            ),
        ],
    )

    commands = {0x01: Set, 0x02: CommandClassSwitchBinaryV1.Get, 0x03: Report}


CommandClassSwitchBinary.versions = {
    1: CommandClassSwitchBinaryV1,
    2: CommandClassSwitchBinaryV2,
}
