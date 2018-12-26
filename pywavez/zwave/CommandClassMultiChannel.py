from pywavez.serialization.Serialization import Expr as _Expr, Value as _Value
from pywavez.serialization.ZWaveSerialization import (
    ZWaveSerialization,
    ZWaveCommandClassBase,
)
from pywavez.zwave.Constants import CommandClass

fct = ZWaveSerialization.functionsModule()


class CommandClassMultiChannel(ZWaveCommandClassBase):
    code = CommandClass.MULTI_CHANNEL
    name = "MultiChannel"


class CommandClassMultiInstanceV1(CommandClassMultiChannel):
    version = 1
    name = "MultiInstance"

    Get = ZWaveSerialization.createClass(
        "Get",
        [
            fct.zwaveCommand(_class=0x60, cmd=0x04),
            fct.uint8(field="commandClass"),
        ],
    )
    Report = ZWaveSerialization.createClass(
        "Report",
        [
            fct.zwaveCommand(_class=0x60, cmd=0x05),
            fct.uint8(field="commandClass"),
            fct.uint8(field="instances"),
        ],
    )
    CmdEncap = ZWaveSerialization.createClass(
        "CmdEncap",
        [
            fct.zwaveCommand(_class=0x60, cmd=0x06),
            fct.uint8(field="instance"),
            fct.uint8(field="commandClass"),
            fct.uint8(field="command"),
            fct.binary(field="parameter"),
        ],
    )

    commands = {0x04: Get, 0x05: Report, 0x06: CmdEncap}


class CommandClassMultiChannelV2(CommandClassMultiInstanceV1):
    version = 2
    name = "MultiChannel"

    Report = ZWaveSerialization.createClass(
        "Report",
        [
            fct.zwaveCommand(_class=0x60, cmd=0x05),
            fct.uint8(field="commandClass"),
            fct.uintbits(field="instances", mask=0x7F, shift=0),
        ],
    )
    CmdEncap = ZWaveSerialization.createClass(
        "CmdEncap",
        [
            fct.zwaveCommand(_class=0x60, cmd=0x06),
            fct.uintbits(field="instance", mask=0x7F, shift=0),
            fct.uint8(field="commandClass"),
            fct.uint8(field="command"),
            fct.binary(field="parameter"),
        ],
    )
    EndPointGet = ZWaveSerialization.createClass(
        "EndPointGet", [fct.zwaveCommand(_class=0x60, cmd=0x07)]
    )
    EndPointReport = ZWaveSerialization.createClass(
        "EndPointReport",
        [
            fct.zwaveCommand(_class=0x60, cmd=0x08),
            fct.boolean(field="identical", mask=0x40),
            fct.boolean(field="dynamic", prevbyte=True, mask=0x80),
            fct.uintbits(field="individualEndPoints", mask=0x7F, shift=0),
        ],
    )
    CapabilityGet = ZWaveSerialization.createClass(
        "CapabilityGet",
        [
            fct.zwaveCommand(_class=0x60, cmd=0x09),
            fct.uintbits(field="endPoint", mask=0x7F, shift=0),
        ],
    )
    CapabilityReport = ZWaveSerialization.createClass(
        "CapabilityReport",
        [
            fct.zwaveCommand(_class=0x60, cmd=0x0A),
            fct.uintbits(field="endPoint", mask=0x7F, shift=0),
            fct.boolean(field="dynamic", prevbyte=True, mask=0x80),
            fct.uint8(field="genericDeviceClass"),
            fct.uint8(field="specificDeviceClass"),
            fct.binary(field="commandClass"),
        ],
    )
    EndPointFind = ZWaveSerialization.createClass(
        "EndPointFind",
        [
            fct.zwaveCommand(_class=0x60, cmd=0x0B),
            fct.uint8(field="genericDeviceClass"),
            fct.uint8(field="specificDeviceClass"),
        ],
    )
    EndPointFindReport = ZWaveSerialization.createClass(
        "EndPointFindReport",
        [
            fct.zwaveCommand(_class=0x60, cmd=0x0C),
            fct.uint8(field="reportsToFollow"),
            fct.uint8(field="genericDeviceClass"),
            fct.uint8(field="specificDeviceClass"),
            fct.array(
                field="endPoint",
                length=None,
                items=fct.uintbits(mask=0x7F, shift=0),
            ),
        ],
    )
    MultiChannelCmdEncap = ZWaveSerialization.createClass(
        "MultiChannelCmdEncap",
        [
            fct.zwaveCommand(_class=0x60, cmd=0x0D),
            fct.uintbits(field="sourceEndPoint", mask=0x7F, shift=0),
            fct.uintbits(field="destinationEndPoint", mask=0x7F, shift=0),
            fct.boolean(field="bitAddress", prevbyte=True, mask=0x80),
            fct.uint8(field="commandClass"),
            fct.uint8(field="command"),
            fct.binary(field="parameter"),
        ],
    )

    commands = {
        0x04: CommandClassMultiInstanceV1.Get,
        0x05: Report,
        0x06: CmdEncap,
        0x07: EndPointGet,
        0x08: EndPointReport,
        0x09: CapabilityGet,
        0x0A: CapabilityReport,
        0x0B: EndPointFind,
        0x0C: EndPointFindReport,
        0x0D: MultiChannelCmdEncap,
    }


class CommandClassMultiChannelV3(CommandClassMultiChannelV2):
    version = 3

    commands = {
        0x04: CommandClassMultiInstanceV1.Get,
        0x05: CommandClassMultiChannelV2.Report,
        0x06: CommandClassMultiChannelV2.CmdEncap,
        0x07: CommandClassMultiChannelV2.EndPointGet,
        0x08: CommandClassMultiChannelV2.EndPointReport,
        0x09: CommandClassMultiChannelV2.CapabilityGet,
        0x0A: CommandClassMultiChannelV2.CapabilityReport,
        0x0B: CommandClassMultiChannelV2.EndPointFind,
        0x0C: CommandClassMultiChannelV2.EndPointFindReport,
        0x0D: CommandClassMultiChannelV2.MultiChannelCmdEncap,
    }


class CommandClassMultiChannelV4(CommandClassMultiChannelV3):
    version = 4

    EndPointReport = ZWaveSerialization.createClass(
        "EndPointReport",
        [
            fct.zwaveCommand(_class=0x60, cmd=0x08),
            fct.boolean(field="identical", mask=0x40),
            fct.boolean(field="dynamic", prevbyte=True, mask=0x80),
            fct.uintbits(field="individualEndPoints", mask=0x7F, shift=0),
            fct.uintbits(field="aggregatedEndPoints", mask=0x7F, shift=0),
        ],
    )
    AggregatedMembersGet = ZWaveSerialization.createClass(
        "AggregatedMembersGet",
        [
            fct.zwaveCommand(_class=0x60, cmd=0x0E),
            fct.uintbits(field="aggregatedEndPoint", mask=0x7F, shift=0),
        ],
    )
    AggregatedMembersReport = ZWaveSerialization.createClass(
        "AggregatedMembersReport",
        [
            fct.zwaveCommand(_class=0x60, cmd=0x0F),
            fct.uintbits(field="aggregatedEndPoint", mask=0x7F, shift=0),
            fct.uint8(
                virtualfield="numberOfBitMasks",
                value=_Expr("len(aggregatedMembersBitMask)"),
            ),
            fct.bitset(
                field="aggregatedMembersBitMask",
                bytes=_Value("numberOfBitMasks"),
            ),
        ],
    )

    commands = {
        0x04: CommandClassMultiInstanceV1.Get,
        0x05: CommandClassMultiChannelV2.Report,
        0x06: CommandClassMultiChannelV2.CmdEncap,
        0x07: CommandClassMultiChannelV2.EndPointGet,
        0x08: EndPointReport,
        0x09: CommandClassMultiChannelV2.CapabilityGet,
        0x0A: CommandClassMultiChannelV2.CapabilityReport,
        0x0B: CommandClassMultiChannelV2.EndPointFind,
        0x0C: CommandClassMultiChannelV2.EndPointFindReport,
        0x0D: CommandClassMultiChannelV2.MultiChannelCmdEncap,
        0x0E: AggregatedMembersGet,
        0x0F: AggregatedMembersReport,
    }


CommandClassMultiChannel.versions = {
    1: CommandClassMultiInstanceV1,
    2: CommandClassMultiChannelV2,
    3: CommandClassMultiChannelV3,
    4: CommandClassMultiChannelV4,
}
