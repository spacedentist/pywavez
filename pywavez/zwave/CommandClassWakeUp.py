from pywavez.serialization.ZWaveSerialization import (
    ZWaveSerialization,
    ZWaveCommandClassBase,
)
from pywavez.zwave.Constants import CommandClass

fct = ZWaveSerialization.functionsModule()


class CommandClassWakeUp(ZWaveCommandClassBase):
    code = CommandClass.WAKE_UP
    name = "WakeUp"


class CommandClassWakeUpV1(CommandClassWakeUp):
    version = 1

    IntervalSet = ZWaveSerialization.createClass(
        "IntervalSet",
        [
            fct.zwaveCommand(_class=0x84, cmd=0x04),
            fct.uint24(field="seconds"),
            fct.uint8(field="nodeid"),
        ],
    )
    IntervalGet = ZWaveSerialization.createClass(
        "IntervalGet", [fct.zwaveCommand(_class=0x84, cmd=0x05)]
    )
    IntervalReport = ZWaveSerialization.createClass(
        "IntervalReport",
        [
            fct.zwaveCommand(_class=0x84, cmd=0x06),
            fct.uint24(field="seconds"),
            fct.uint8(field="nodeid"),
        ],
    )
    Notification = ZWaveSerialization.createClass(
        "Notification", [fct.zwaveCommand(_class=0x84, cmd=0x07)]
    )
    NoMoreInformation = ZWaveSerialization.createClass(
        "NoMoreInformation", [fct.zwaveCommand(_class=0x84, cmd=0x08)]
    )

    commands = {
        0x04: IntervalSet,
        0x05: IntervalGet,
        0x06: IntervalReport,
        0x07: Notification,
        0x08: NoMoreInformation,
    }


class CommandClassWakeUpV2(CommandClassWakeUpV1):
    version = 2

    IntervalCapabilitiesGet = ZWaveSerialization.createClass(
        "IntervalCapabilitiesGet", [fct.zwaveCommand(_class=0x84, cmd=0x09)]
    )
    IntervalCapabilitiesReport = ZWaveSerialization.createClass(
        "IntervalCapabilitiesReport",
        [
            fct.zwaveCommand(_class=0x84, cmd=0x0A),
            fct.uint24(field="minimumWakeUpIntervalSeconds"),
            fct.uint24(field="maximumWakeUpIntervalSeconds"),
            fct.uint24(field="defaultWakeUpIntervalSeconds"),
            fct.uint24(field="wakeUpIntervalStepSeconds"),
        ],
    )

    commands = {
        0x04: CommandClassWakeUpV1.IntervalSet,
        0x05: CommandClassWakeUpV1.IntervalGet,
        0x06: CommandClassWakeUpV1.IntervalReport,
        0x07: CommandClassWakeUpV1.Notification,
        0x08: CommandClassWakeUpV1.NoMoreInformation,
        0x09: IntervalCapabilitiesGet,
        0x0A: IntervalCapabilitiesReport,
    }


CommandClassWakeUp.versions = {
    1: CommandClassWakeUpV1,
    2: CommandClassWakeUpV2,
}
