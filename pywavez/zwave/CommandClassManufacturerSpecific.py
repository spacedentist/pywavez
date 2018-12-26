import enum

from pywavez.serialization.Serialization import Expr as _Expr, Value as _Value
from pywavez.serialization.ZWaveSerialization import (
    ZWaveSerialization,
    ZWaveCommandClassBase,
)
from pywavez.zwave.Constants import CommandClass

fct = ZWaveSerialization.functionsModule()


class CommandClassManufacturerSpecific(ZWaveCommandClassBase):
    code = CommandClass.MANUFACTURER_SPECIFIC
    name = "ManufacturerSpecific"

    class DeviceIdType(enum.IntEnum):
        RESERVED = 0
        SERIAL_NUMBER = 1

    class DeviceIdDataFormat(enum.IntEnum):
        RESERVED = 0
        BINARY = 1


class CommandClassManufacturerSpecificV1(CommandClassManufacturerSpecific):
    version = 1

    Get = ZWaveSerialization.createClass(
        "Get", [fct.zwaveCommand(_class=0x72, cmd=0x04)]
    )
    Report = ZWaveSerialization.createClass(
        "Report",
        [
            fct.zwaveCommand(_class=0x72, cmd=0x05),
            fct.uint16(field="manufacturerId"),
            fct.uint16(field="productTypeId"),
            fct.uint16(field="productId"),
        ],
    )

    commands = {0x04: Get, 0x05: Report}


class CommandClassManufacturerSpecificV2(CommandClassManufacturerSpecificV1):
    version = 2

    DeviceSpecificGet = ZWaveSerialization.createClass(
        "DeviceSpecificGet",
        [
            fct.zwaveCommand(_class=0x72, cmd=0x06),
            fct.uintbits(
                field="deviceIdType",
                mask=0x07,
                shift=0,
                enum=CommandClassManufacturerSpecific.DeviceIdType,
            ),
        ],
    )
    DeviceSpecificReport = ZWaveSerialization.createClass(
        "DeviceSpecificReport",
        [
            fct.zwaveCommand(_class=0x72, cmd=0x07),
            fct.uintbits(
                field="deviceIdType",
                mask=0x07,
                shift=0,
                enum=CommandClassManufacturerSpecific.DeviceIdType,
            ),
            fct.uintbits(
                virtualfield="deviceIdDataLengthIndicator",
                mask=0x1F,
                shift=0,
                value=_Expr("len(deviceIdData)"),
            ),
            fct.uintbits(
                field="deviceIdDataFormat",
                prevbyte=True,
                mask=0x07,
                shift=5,
                enum=CommandClassManufacturerSpecific.DeviceIdDataFormat,
            ),
            fct.binary(
                field="deviceIdData",
                bytes=_Value("deviceIdDataLengthIndicator"),
            ),
        ],
    )

    commands = {
        0x04: CommandClassManufacturerSpecificV1.Get,
        0x05: CommandClassManufacturerSpecificV1.Report,
        0x06: DeviceSpecificGet,
        0x07: DeviceSpecificReport,
    }


CommandClassManufacturerSpecific.versions = {
    1: CommandClassManufacturerSpecificV1,
    2: CommandClassManufacturerSpecificV2,
}
