import enum

from pywavez.serialization.ZWaveSerialization import (
    ZWaveSerialization,
    ZWaveCommandClassBase,
)
from pywavez.zwave.Constants import CommandClass

fct = ZWaveSerialization.functionsModule()


class CommandClassSwitchMultilevel(ZWaveCommandClassBase):
    code = CommandClass.SWITCH_MULTILEVEL
    name = "SwitchMultilevel"

    class Value(enum.IntEnum):
        OFF_DISABLE = 0
        ON_ENABLE = 255

    class Duration(enum.IntEnum):
        INSTANTLY = 0
        UNKNOWN_DURATION = 254
        DEFAULT = 255

    class IncDec(enum.IntEnum):
        INCREMENT = 0
        DECREMENT = 1
        RESERVED = 2
        NONE = 3

    class UpDown(enum.IntEnum):
        UP = 0
        DOWN = 1
        RESERVED = 2
        NONE = 3


class CommandClassSwitchMultilevelV1(CommandClassSwitchMultilevel):
    version = 1

    Set = ZWaveSerialization.createClass(
        "Set",
        [
            fct.zwaveCommand(_class=0x26, cmd=0x01),
            fct.uint8(field="value", enum=CommandClassSwitchMultilevel.Value),
        ],
    )
    Get = ZWaveSerialization.createClass(
        "Get", [fct.zwaveCommand(_class=0x26, cmd=0x02)]
    )
    Report = ZWaveSerialization.createClass(
        "Report",
        [
            fct.zwaveCommand(_class=0x26, cmd=0x03),
            fct.uint8(field="value", enum=CommandClassSwitchMultilevel.Value),
        ],
    )
    StartLevelChange = ZWaveSerialization.createClass(
        "StartLevelChange",
        [
            fct.zwaveCommand(_class=0x26, cmd=0x04),
            fct.boolean(field="ignoreStartLevel", mask=0x20),
            fct.boolean(field="upDown", prevbyte=True, mask=0x40),
            fct.uint8(field="startLevel"),
        ],
    )
    StopLevelChange = ZWaveSerialization.createClass(
        "StopLevelChange", [fct.zwaveCommand(_class=0x26, cmd=0x05)]
    )

    commands = {
        0x01: Set,
        0x02: Get,
        0x03: Report,
        0x04: StartLevelChange,
        0x05: StopLevelChange,
    }


class CommandClassSwitchMultilevelV2(CommandClassSwitchMultilevelV1):
    version = 2

    Set = ZWaveSerialization.createClass(
        "Set",
        [
            fct.zwaveCommand(_class=0x26, cmd=0x01),
            fct.uint8(field="value", enum=CommandClassSwitchMultilevel.Value),
            fct.uint8(
                field="dimmingDuration",
                enum=CommandClassSwitchMultilevel.Duration,
                defaultValue=CommandClassSwitchMultilevel.Duration.INSTANTLY,
            ),
        ],
    )

    StartLevelChange = ZWaveSerialization.createClass(
        "StartLevelChange",
        [
            fct.zwaveCommand(_class=0x26, cmd=0x04),
            fct.boolean(field="ignoreStartLevel", mask=0x20),
            fct.boolean(field="upDown", prevbyte=True, mask=0x40),
            fct.uint8(field="startLevel"),
            fct.uint8(field="dimmingDuration"),
        ],
    )

    commands = {
        0x01: Set,
        0x02: CommandClassSwitchMultilevelV1.Get,
        0x03: CommandClassSwitchMultilevelV1.Report,
        0x04: StartLevelChange,
        0x05: CommandClassSwitchMultilevelV1.StopLevelChange,
    }


class CommandClassSwitchMultilevelV3(CommandClassSwitchMultilevelV2):
    version = 3

    StartLevelChange = ZWaveSerialization.createClass(
        "StartLevelChange",
        [
            fct.zwaveCommand(_class=0x26, cmd=0x04),
            fct.uintbits(
                field="incDec",
                mask=0x03,
                shift=3,
                enum=CommandClassSwitchMultilevel.IncDec,
            ),
            fct.boolean(field="ignoreStartLevel", prevbyte=True, mask=0x20),
            fct.uintbits(
                field="upDown",
                prevbyte=True,
                mask=0x03,
                shift=6,
                enum=CommandClassSwitchMultilevel.UpDown,
            ),
            fct.uint8(field="startLevel"),
            fct.uint8(field="dimmingDuration"),
            fct.uint8(field="stepSize"),
        ],
    )
    SupportedGet = ZWaveSerialization.createClass(
        "SupportedGet", [fct.zwaveCommand(_class=0x26, cmd=0x06)]
    )
    SupportedReport = ZWaveSerialization.createClass(
        "SupportedReport",
        [
            fct.zwaveCommand(_class=0x26, cmd=0x07),
            fct.uintbits(field="primarySwitchType", mask=0x1F, shift=0),
            fct.uintbits(field="secondarySwitchType", mask=0x1F, shift=0),
        ],
    )

    commands = {
        0x01: CommandClassSwitchMultilevelV2.Set,
        0x02: CommandClassSwitchMultilevelV1.Get,
        0x03: CommandClassSwitchMultilevelV1.Report,
        0x04: StartLevelChange,
        0x05: CommandClassSwitchMultilevelV1.StopLevelChange,
        0x06: SupportedGet,
        0x07: SupportedReport,
    }


class CommandClassSwitchMultilevelV4(CommandClassSwitchMultilevelV3):
    version = 4

    Report = ZWaveSerialization.createClass(
        "Report",
        [
            fct.zwaveCommand(_class=0x26, cmd=0x03),
            fct.uint8(field="value", enum=CommandClassSwitchMultilevel.Value),
            fct.uint8(
                field="targetValue", enum=CommandClassSwitchMultilevel.Value
            ),
            fct.uint8(
                field="duration", enum=CommandClassSwitchMultilevel.Duration
            ),
        ],
    )

    commands = {
        0x01: CommandClassSwitchMultilevelV2.Set,
        0x02: CommandClassSwitchMultilevelV1.Get,
        0x03: Report,
        0x04: CommandClassSwitchMultilevelV3.StartLevelChange,
        0x05: CommandClassSwitchMultilevelV1.StopLevelChange,
        0x06: CommandClassSwitchMultilevelV3.SupportedGet,
        0x07: CommandClassSwitchMultilevelV3.SupportedReport,
    }


CommandClassSwitchMultilevel.versions = {
    1: CommandClassSwitchMultilevelV1,
    2: CommandClassSwitchMultilevelV2,
    3: CommandClassSwitchMultilevelV3,
    4: CommandClassSwitchMultilevelV4,
}
