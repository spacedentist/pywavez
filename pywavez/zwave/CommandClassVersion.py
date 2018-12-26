from pywavez.serialization.Serialization import Expr as _Expr, Value as _Value
from pywavez.serialization.ZWaveSerialization import (
    ZWaveSerialization,
    ZWaveCommandClassBase,
)
from pywavez.zwave.Constants import CommandClass

fct = ZWaveSerialization.functionsModule()


class CommandClassVersion(ZWaveCommandClassBase):
    code = CommandClass.VERSION
    name = "Version"


class CommandClassVersionV1(CommandClassVersion):
    version = 1

    Get = ZWaveSerialization.createClass(
        "Get", [fct.zwaveCommand(_class=0x86, cmd=0x11)]
    )
    Report = ZWaveSerialization.createClass(
        "Report",
        [
            fct.zwaveCommand(_class=0x86, cmd=0x12),
            fct.uint8(field="zWaveLibraryType"),
            fct.uint8(field="zWaveProtocolVersion"),
            fct.uint8(field="zWaveProtocolSubVersion"),
            fct.uint8(field="applicationVersion"),
            fct.uint8(field="applicationSubVersion"),
        ],
    )
    CommandClassGet = ZWaveSerialization.createClass(
        "CommandClassGet",
        [
            fct.zwaveCommand(_class=0x86, cmd=0x13),
            fct.uint8(field="requestedCommandClass", enum=CommandClass),
        ],
    )
    CommandClassReport = ZWaveSerialization.createClass(
        "CommandClassReport",
        [
            fct.zwaveCommand(_class=0x86, cmd=0x14),
            fct.uint8(field="requestedCommandClass", enum=CommandClass),
            fct.uint8(field="commandClassVersion"),
        ],
    )

    commands = {
        0x11: Get,
        0x12: Report,
        0x13: CommandClassGet,
        0x14: CommandClassReport,
    }


class CommandClassVersionV2(CommandClassVersionV1):
    version = 2

    Report = ZWaveSerialization.createClass(
        "Report",
        [
            fct.zwaveCommand(_class=0x86, cmd=0x12),
            fct.uint8(field="zWaveLibraryType"),
            fct.uint8(field="zWaveProtocolVersion"),
            fct.uint8(field="zWaveProtocolSubVersion"),
            fct.uint8(field="firmware0Version"),
            fct.uint8(field="firmware0SubVersion"),
            fct.uint8(field="hardwareVersion"),
            fct.uint8(
                virtualfield="numberOfFirmwareTargets", value=_Expr("len(vg)")
            ),
            fct.classvar(
                name="Firmware",
                val=ZWaveSerialization.createClass(
                    "Firmware",
                    [
                        fct.uint8(field="firmwareVersion"),
                        fct.uint8(field="firmwareSubVersion"),
                    ],
                ),
            ),
            fct.array(
                field="firmwareTargets",
                items=fct.object(type=_Value("__obj.Firmware")),
                length=_Value("numberOfFirmwareTargets"),
            ),
        ],
    )

    commands = {
        0x11: CommandClassVersionV1.Get,
        0x12: Report,
        0x13: CommandClassVersionV1.CommandClassGet,
        0x14: CommandClassVersionV1.CommandClassReport,
    }


class CommandClassVersionV3(CommandClassVersionV2):
    version = 3

    CapabilitiesGet = ZWaveSerialization.createClass(
        "CapabilitiesGet", [fct.zwaveCommand(_class=0x86, cmd=0x15)]
    )
    CapabilitiesReport = ZWaveSerialization.createClass(
        "CapabilitiesReport",
        [
            fct.zwaveCommand(_class=0x86, cmd=0x16),
            fct.boolean(field="version", mask=0x01),
            fct.boolean(field="commandClass", prevbyte=True, mask=0x02),
            fct.boolean(field="zWaveSoftware", prevbyte=True, mask=0x04),
        ],
    )
    ZwaveSoftwareGet = ZWaveSerialization.createClass(
        "ZwaveSoftwareGet", [fct.zwaveCommand(_class=0x86, cmd=0x17)]
    )
    ZwaveSoftwareReport = ZWaveSerialization.createClass(
        "ZwaveSoftwareReport",
        [
            fct.zwaveCommand(_class=0x86, cmd=0x18),
            fct.uint24(field="sdkVersion"),
            fct.uint24(field="applicationFrameworkApiVersion"),
            fct.uint16(field="applicationFrameworkBuildNumber"),
            fct.uint24(field="hostInterfaceVersion"),
            fct.uint16(field="hostInterfaceBuildNumber"),
            fct.uint24(field="zWaveProtocolVersion"),
            fct.uint16(field="zWaveProtocolBuildNumber"),
            fct.uint24(field="applicationVersion"),
            fct.uint16(field="applicationBuildNumber"),
        ],
    )

    commands = {
        0x11: CommandClassVersionV1.Get,
        0x12: CommandClassVersionV2.Report,
        0x13: CommandClassVersionV1.CommandClassGet,
        0x14: CommandClassVersionV1.CommandClassReport,
        0x15: CapabilitiesGet,
        0x16: CapabilitiesReport,
        0x17: ZwaveSoftwareGet,
        0x18: ZwaveSoftwareReport,
    }


CommandClassVersion.versions = {
    1: CommandClassVersionV1,
    2: CommandClassVersionV2,
    3: CommandClassVersionV3,
}
