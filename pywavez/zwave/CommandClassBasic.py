from pywavez.serialization.ZWaveSerialization import (
    ZWaveSerialization,
    ZWaveCommandClassBase,
)
from pywavez.zwave.Constants import CommandClass

fct = ZWaveSerialization.functionsModule()


class CommandClassBasic(ZWaveCommandClassBase):
    code = CommandClass.BASIC
    name = "Basic"


class CommandClassBasicV1(CommandClassBasic):
    version = 1

    Set = ZWaveSerialization.createClass(
        "Set",
        [fct.zwaveCommand(_class=0x20, cmd=0x01), fct.uint8(field="value")],
    )
    Get = ZWaveSerialization.createClass(
        "Get", [fct.zwaveCommand(_class=0x20, cmd=0x02)]
    )
    Report = ZWaveSerialization.createClass(
        "Report",
        [fct.zwaveCommand(_class=0x20, cmd=0x03), fct.uint8(field="value")],
    )

    commands = {0x01: Set, 0x02: Get, 0x03: Report}


class CommandClassBasicV2(CommandClassBasicV1):
    version = 2

    Report = ZWaveSerialization.createClass(
        "Report",
        [
            fct.zwaveCommand(_class=0x20, cmd=0x03),
            fct.uint8(field="value"),
            fct.uint8(field="targetValue"),
            fct.uint8(field="duration"),
        ],
    )

    commands = {
        0x01: CommandClassBasicV1.Set,
        0x02: CommandClassBasicV1.Get,
        0x03: Report,
    }


CommandClassBasic.versions = {1: CommandClassBasicV1, 2: CommandClassBasicV2}
