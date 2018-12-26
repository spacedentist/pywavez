import enum

from pywavez.serialization.Serialization import Expr as _Expr, Value as _Value
from pywavez.serialization.ZWaveSerialization import (
    ZWaveSerialization,
    ZWaveCommandClassBase,
)
from pywavez.zwave.Constants import CommandClass

fct = ZWaveSerialization.functionsModule()


class CommandClassThermostatSetpoint(ZWaveCommandClassBase):
    code = CommandClass.THERMOSTAT_SETPOINT
    name = "ThermostatSetpoint"

    class SetpointType(enum.IntEnum):
        NOT_SUPPORTED = 0
        HEATING = 1
        COOLING = 2
        RESERVED_1 = 3
        RESERVED_2 = 4
        RESERVED_3 = 5
        RESERVED_4 = 6
        FURNACE = 7
        DRY_AIR = 8
        MOIST_AIR = 9
        AUTO_CHANGEOVER = 10
        ENERGY_SAVE_HEATING = 11
        ENERGY_SAVE_COOLING = 12
        AWAY_HEATING = 13
        AWAY_COOLING = 14
        FULL_POWER = 15

    class Scale(enum.IntEnum):
        CELSIUS = 0
        FAHRENHEIT = 1
        UNKNOWN_2 = 2
        UNKNOWN_3 = 3


class CommandClassThermostatSetpointV1(CommandClassThermostatSetpoint):
    version = 1

    Set = ZWaveSerialization.createClass(
        "Set",
        [
            fct.zwaveCommand(_class=0x43, cmd=0x01),
            fct.uintbits(
                field="setpointType",
                mask=0x0F,
                shift=0,
                enum=CommandClassThermostatSetpoint.SetpointType,
            ),
            fct.uintbits(
                virtualfield="size",
                mask=0x07,
                shift=0,
                value=_Expr("intsize(value)"),
            ),
            fct.uintbits(
                field="scale",
                prevbyte=True,
                mask=0x03,
                shift=3,
                enum=CommandClassThermostatSetpoint.Scale,
            ),
            fct.uintbits(field="precision", prevbyte=True, mask=0x07, shift=5),
            fct.int(field="value", bytes=_Value("size")),
        ],
    )
    Get = ZWaveSerialization.createClass(
        "Get",
        [
            fct.zwaveCommand(_class=0x43, cmd=0x02),
            fct.uintbits(
                field="setpointType",
                mask=0x0F,
                shift=0,
                enum=CommandClassThermostatSetpoint.SetpointType,
            ),
        ],
    )
    Report = ZWaveSerialization.createClass(
        "Report",
        [
            fct.zwaveCommand(_class=0x43, cmd=0x03),
            fct.uintbits(
                field="setpointType",
                mask=0x0F,
                shift=0,
                enum=CommandClassThermostatSetpoint.SetpointType,
            ),
            fct.uintbits(
                virtualfield="size",
                mask=0x07,
                shift=0,
                value=_Expr("intsize(value)"),
            ),
            fct.uintbits(
                field="scale",
                prevbyte=True,
                mask=0x03,
                shift=3,
                enum=CommandClassThermostatSetpoint.Scale,
            ),
            fct.uintbits(field="precision", prevbyte=True, mask=0x07, shift=5),
            fct.int(field="value", bytes=_Value("size")),
        ],
    )
    SupportedGet = ZWaveSerialization.createClass(
        "SupportedGet", [fct.zwaveCommand(_class=0x43, cmd=0x04)]
    )
    SupportedReport = ZWaveSerialization.createClass(
        "SupportedReport",
        [
            fct.zwaveCommand(_class=0x43, cmd=0x05),
            fct.bitset(
                field="types",
                bytes=None,
                enum=CommandClassThermostatSetpoint.SetpointType,
            ),
        ],
    )

    commands = {
        0x01: Set,
        0x02: Get,
        0x03: Report,
        0x04: SupportedGet,
        0x05: SupportedReport,
    }


class CommandClassThermostatSetpointV2(CommandClassThermostatSetpointV1):
    version = 2

    commands = {
        0x01: CommandClassThermostatSetpointV1.Set,
        0x02: CommandClassThermostatSetpointV1.Get,
        0x03: CommandClassThermostatSetpointV1.Report,
        0x04: CommandClassThermostatSetpointV1.SupportedGet,
        0x05: CommandClassThermostatSetpointV1.SupportedReport,
    }


class CommandClassThermostatSetpointV3(CommandClassThermostatSetpointV2):
    version = 3

    CapabilitiesGet = ZWaveSerialization.createClass(
        "CapabilitiesGet",
        [
            fct.zwaveCommand(_class=0x43, cmd=0x09),
            fct.uintbits(
                field="setpointType",
                mask=0x0F,
                shift=0,
                enum=CommandClassThermostatSetpoint.SetpointType,
            ),
        ],
    )
    CapabilitiesReport = ZWaveSerialization.createClass(
        "CapabilitiesReport",
        [
            fct.zwaveCommand(_class=0x43, cmd=0x0A),
            fct.uintbits(
                field="setpointType",
                mask=0x0F,
                shift=0,
                enum=CommandClassThermostatSetpoint.SetpointType,
            ),
            fct.uintbits(
                virtualfield="minValueSize",
                mask=0x07,
                shift=0,
                value=_Expr("intsize(minValue)"),
            ),
            fct.uintbits(
                field="minValueScale", prevbyte=True, mask=0x03, shift=3
            ),
            fct.uintbits(
                field="minValuePrecision", prevbyte=True, mask=0x07, shift=5
            ),
            fct.int(field="minValue", bytes=_Value("minValueSize")),
            fct.uintbits(
                virtualfield="maxValueSize",
                mask=0x07,
                shift=0,
                value=_Expr("intsize(maxvalue)"),
            ),
            fct.uintbits(
                field="maxValueScale", prevbyte=True, mask=0x03, shift=3
            ),
            fct.uintbits(
                field="maxValuePrecision", prevbyte=True, mask=0x07, shift=5
            ),
            fct.int(field="maxvalue", bytes=_Value("maxValueSize")),
        ],
    )

    commands = {
        0x01: CommandClassThermostatSetpointV1.Set,
        0x02: CommandClassThermostatSetpointV1.Get,
        0x03: CommandClassThermostatSetpointV1.Report,
        0x04: CommandClassThermostatSetpointV1.SupportedGet,
        0x05: CommandClassThermostatSetpointV1.SupportedReport,
        0x09: CapabilitiesGet,
        0x0A: CapabilitiesReport,
    }


CommandClassThermostatSetpoint.versions = {
    1: CommandClassThermostatSetpointV1,
    2: CommandClassThermostatSetpointV2,
    3: CommandClassThermostatSetpointV3,
}
