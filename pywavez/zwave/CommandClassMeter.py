import enum

from pywavez.serialization.Serialization import Expr as _Expr, Value as _Value
from pywavez.serialization.ZWaveSerialization import (
    ZWaveSerialization,
    ZWaveCommandClassBase,
)
from pywavez.zwave.Constants import CommandClass

fct = ZWaveSerialization.functionsModule()


class CommandClassMeter(ZWaveCommandClassBase):
    code = CommandClass.METER
    name = "Meter"

    class MeterType(enum.IntEnum):
        RESERVED = 0
        ELECTRIC_METER = 1
        GAS_METER = 2
        WATER_METER = 3
        HEATING_METER = 4
        COOLING_METER = 5

    class RateType(enum.IntEnum):
        RESERVED = 0
        IMPORT_ONLY = 1
        EXPORT_ONLY = 2
        IMPORT_AND_EXPORT = 3


class CommandClassMeterV1(CommandClassMeter):
    version = 1

    Get = ZWaveSerialization.createClass(
        "Get", [fct.zwaveCommand(_class=0x32, cmd=0x01)]
    )
    Report = ZWaveSerialization.createClass(
        "Report",
        [
            fct.zwaveCommand(_class=0x32, cmd=0x02),
            fct.uint8(field="meterType", enum=CommandClassMeter.MeterType),
            fct.uintbits(
                virtualfield="size",
                mask=0x07,
                shift=0,
                value=_Expr("intsize(meterValue)"),
            ),
            fct.uintbits(field="scale", prevbyte=True, mask=0x03, shift=3),
            fct.uintbits(field="precision", prevbyte=True, mask=0x07, shift=5),
            fct.int(field="meterValue", bytes=_Value("size")),
        ],
    )

    commands = {0x01: Get, 0x02: Report}


class CommandClassMeterV2(CommandClassMeterV1):
    version = 2

    Get = ZWaveSerialization.createClass(
        "Get",
        [
            fct.zwaveCommand(_class=0x32, cmd=0x01),
            fct.uintbits(field="scale", mask=0x03, shift=3),
        ],
    )
    Report = ZWaveSerialization.createClass(
        "Report",
        [
            fct.zwaveCommand(_class=0x32, cmd=0x02),
            fct.uintbits(field="meterType", mask=0x1F, shift=0),
            fct.uintbits(field="rateType", prevbyte=True, mask=0x03, shift=5),
            fct.uintbits(
                virtualfield="size",
                mask=0x07,
                shift=0,
                value=_Expr(
                    "max(intsize(meterValue), intsize(previousMeterValue))"
                ),
            ),
            fct.uintbits(field="scale", prevbyte=True, mask=0x03, shift=3),
            fct.uintbits(field="precision", prevbyte=True, mask=0x07, shift=5),
            fct.int(field="meterValue", bytes=_Value("size")),
            fct.uint16(field="deltaTime"),
            fct.optional(
                field="previousMeterValue",
                present=_Value("deltaTime"),
                item=fct.int(bytes=_Value("size")),
            ),
        ],
    )
    SupportedGet = ZWaveSerialization.createClass(
        "SupportedGet", [fct.zwaveCommand(_class=0x32, cmd=0x03)]
    )
    SupportedReport = ZWaveSerialization.createClass(
        "SupportedReport",
        [
            fct.zwaveCommand(_class=0x32, cmd=0x04),
            fct.uintbits(field="meterType", mask=0x1F, shift=0),
            fct.boolean(field="meterReset", prevbyte=True, mask=0x80),
            fct.uintbits(field="scaleSupported", mask=0x0F, shift=0),
        ],
    )
    Reset = ZWaveSerialization.createClass(
        "Reset", [fct.zwaveCommand(_class=0x32, cmd=0x05)]
    )

    commands = {
        0x01: Get,
        0x02: Report,
        0x03: SupportedGet,
        0x04: SupportedReport,
        0x05: Reset,
    }


class CommandClassMeterV3(CommandClassMeterV2):
    version = 3

    Get = ZWaveSerialization.createClass(
        "Get",
        [
            fct.zwaveCommand(_class=0x32, cmd=0x01),
            fct.uintbits(field="scale", mask=0x07, shift=3),
        ],
    )
    Report = ZWaveSerialization.createClass(
        "Report",
        [
            fct.zwaveCommand(_class=0x32, cmd=0x02),
            fct.uintbits(field="meterType", mask=0x1F, shift=0),
            fct.uintbits(field="rateType", prevbyte=True, mask=0x03, shift=5),
            fct.boolean(field="scaleBit2", prevbyte=True, mask=0x80),
            fct.uintbits(
                virtualfield="size",
                mask=0x07,
                shift=0,
                value=_Expr(
                    "max(intsize(meterValue), intsize(previousMeterValue))"
                ),
            ),
            fct.uintbits(
                field="scaleBits10", prevbyte=True, mask=0x03, shift=3
            ),
            fct.uintbits(field="precision", prevbyte=True, mask=0x07, shift=5),
            fct.int(field="meterValue", bytes=_Value("size")),
            fct.uint16(field="deltaTime"),
            fct.optional(
                field="previousMeterValue",
                present=_Value("deltaTime"),
                item=fct.int(bytes=_Value("size")),
            ),
        ],
    )
    SupportedReport = ZWaveSerialization.createClass(
        "SupportedReport",
        [
            fct.zwaveCommand(_class=0x32, cmd=0x04),
            fct.uintbits(field="meterType", mask=0x1F, shift=0),
            fct.boolean(field="meterReset", prevbyte=True, mask=0x80),
            fct.uint8(field="scaleSupported"),
        ],
    )

    commands = {
        0x01: Get,
        0x02: Report,
        0x03: CommandClassMeterV2.SupportedGet,
        0x04: SupportedReport,
        0x05: CommandClassMeterV2.Reset,
    }


class CommandClassMeterV4(CommandClassMeterV3):
    version = 4

    Get = ZWaveSerialization.createClass(
        "Get",
        [
            fct.zwaveCommand(_class=0x32, cmd=0x01),
            fct.uintbits(field="scale", mask=0x07, shift=3),
            fct.uintbits(
                field="rateType",
                prevbyte=True,
                mask=0x03,
                shift=6,
                enum=CommandClassMeter.RateType,
            ),
            fct.uint8(field="scale2"),
        ],
    )
    Report = ZWaveSerialization.createClass(
        "Report",
        [
            fct.zwaveCommand(_class=0x32, cmd=0x02),
            fct.uintbits(
                field="meterType",
                mask=0x1F,
                shift=0,
                enum=CommandClassMeter.MeterType,
            ),
            fct.uintbits(
                field="rateType",
                prevbyte=True,
                mask=0x03,
                shift=5,
                enum=CommandClassMeter.RateType,
            ),
            fct.boolean(field="scaleBit2", prevbyte=True, mask=0x80),
            fct.uintbits(
                virtualfield="size",
                mask=0x07,
                shift=0,
                value=_Expr(
                    "max(intsize(meterValue), intsize(previousMeterValue))"
                ),
            ),
            fct.uintbits(
                field="scaleBits10", prevbyte=True, mask=0x03, shift=3
            ),
            fct.uintbits(field="precision", prevbyte=True, mask=0x07, shift=5),
            fct.int(field="meterValue", bytes=_Value("size")),
            fct.uint16(field="deltaTime"),
            fct.optional(
                field="previousMeterValue",
                present=_Value("deltaTime"),
                item=fct.int(bytes=_Value("size")),
            ),
            fct.uint8(field="scale2"),
        ],
    )
    SupportedReport = ZWaveSerialization.createClass(
        "SupportedReport",
        [
            fct.zwaveCommand(_class=0x32, cmd=0x04),
            fct.uintbits(
                field="meterType",
                mask=0x1F,
                shift=0,
                enum=CommandClassMeter.MeterType,
            ),
            fct.uintbits(
                field="rateType",
                prevbyte=True,
                mask=0x03,
                shift=5,
                enum=CommandClassMeter.RateType,
            ),
            fct.boolean(field="meterReset", prevbyte=True, mask=0x80),
            fct.uintbits(field="scaleSupported0", mask=0x7F, shift=0),
            fct.boolean(field="mst", prevbyte=True, mask=0x80),
            fct.uint8(
                virtualfield="numberOfScaleSupportedBytesToFollow",
                value=_Expr("len(scaleSupported)"),
            ),
            fct.binary(
                field="scaleSupported",
                bytes=_Value("numberOfScaleSupportedBytesToFollow"),
            ),
        ],
    )

    commands = {
        0x01: Get,
        0x02: Report,
        0x03: CommandClassMeterV2.SupportedGet,
        0x04: SupportedReport,
        0x05: CommandClassMeterV2.Reset,
    }


class CommandClassMeterV5(CommandClassMeterV4):
    version = 5

    commands = {
        0x01: CommandClassMeterV4.Get,
        0x02: CommandClassMeterV4.Report,
        0x03: CommandClassMeterV2.SupportedGet,
        0x04: CommandClassMeterV4.SupportedReport,
        0x05: CommandClassMeterV2.Reset,
    }


CommandClassMeter.versions = {
    1: CommandClassMeterV1,
    2: CommandClassMeterV2,
    3: CommandClassMeterV3,
    4: CommandClassMeterV4,
    5: CommandClassMeterV5,
}
