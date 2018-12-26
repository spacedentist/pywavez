import types

from pywavez.zwave.Constants import (
    LibraryType,
    MessageClass,
    MessageType,
    TransmitComplete,
    TransmitOption,
    UpdateState,
)
from pywavez.serialization.Serialization import Expr, Value
from pywavez.serialization.ZWaveSerialization import ZWaveSerialization

fct = ZWaveSerialization.functionsModule()

descriptions = {
    #########################################################################
    # SERIAL_API_GET_INIT_DATA = 0x02
    "SerialApiGetInitDataRequest": [
        fct.zwaveMessage(
            type=MessageType.REQUEST,
            _class=MessageClass.SERIAL_API_GET_INIT_DATA,
        )
    ],
    "SerialApiGetInitDataResponse": [
        fct.zwaveMessage(
            type=MessageType.RESPONSE,
            _class=MessageClass.SERIAL_API_GET_INIT_DATA,
        ),
        fct.uint8(field="serialApiApplicationVersion"),
        fct.boolean(field="isSlave", mask=0x01, prevbyte=False),
        fct.boolean(field="timerSupport", mask=0x02, prevbyte=True),
        fct.boolean(field="isSecondary", mask=0x04, prevbyte=True),
        fct.boolean(field="isSIS", mask=0x08, prevbyte=True),
        fct.uint8(virtualfield="nodeBitfieldBytes", value=29),
        fct.bitset(field="nodes", offset=1, bytes=Value("nodeBitfieldBytes")),
        fct.uint8(field="chipType"),
        fct.uint8(field="chipVersion"),
    ],
    #########################################################################
    # APPLICATION_COMMAND_HANDLER = 0x04
    "ApplicationCommandHandlerRequest": [
        fct.zwaveMessage(
            type=MessageType.REQUEST,
            _class=MessageClass.APPLICATION_COMMAND_HANDLER,
        ),
        fct.uint8(field="status"),
        fct.uint8(field="nodeId"),
        fct.uint8(virtualfield="payloadLength", value=Expr("len(payload)")),
        fct.binary(field="payload", bytes=Value("payloadLength")),
    ],
    #########################################################################
    # SERIAL_API_SET_TIMEOUTS = 0x06
    "SerialApiSetTimeoutsRequest": [
        fct.zwaveMessage(
            type=MessageType.REQUEST,
            _class=MessageClass.SERIAL_API_SET_TIMEOUTS,
        ),
        fct.uint8(field="rxAckTimeout"),
        fct.uint8(field="rxByteTimeout"),
    ],
    "SerialApiSetTimeoutsResponse": [
        fct.zwaveMessage(
            type=MessageType.RESPONSE,
            _class=MessageClass.SERIAL_API_SET_TIMEOUTS,
        ),
        fct.uint8(field="oldRxAckTimeout"),
        fct.uint8(field="oldRxByteTimeout"),
    ],
    #########################################################################
    # SERIAL_API_GET_CAPABILITIES = 0x07
    "SerialApiGetCapabilitiesRequest": [
        fct.zwaveMessage(
            type=MessageType.REQUEST,
            _class=MessageClass.SERIAL_API_GET_CAPABILITIES,
        )
    ],
    "SerialApiGetCapabilitiesResponse": [
        fct.zwaveMessage(
            type=MessageType.RESPONSE,
            _class=MessageClass.SERIAL_API_GET_CAPABILITIES,
        ),
        fct.uint8(field="serialApiVersion"),
        fct.uint8(field="serialApiRevision"),
        fct.uint16(field="manufacturerId"),
        fct.uint16(field="manufacturerProduct"),
        fct.uint16(field="manufacturerProductId"),
        fct.bitset(field="supportedFunctions", offset=1, bytes=32),
    ],
    #########################################################################
    # SEND_NODE_INFORMATION = 0x12
    "SendNodeInformationRequest": [
        fct.zwaveMessage(
            type=MessageType.REQUEST,
            _class=MessageClass.SEND_NODE_INFORMATION,
            inbound=False,
            outbound=True,
            nodeIdField="destNode",
        ),
        fct.uint8(field="destNode"),
        fct.uint8(field="txOptions", enum=TransmitOption),
        fct.uint8(field="funcId"),
    ],
    "SendNodeInformationResponse": [
        fct.zwaveMessage(
            type=MessageType.RESPONSE,
            _class=MessageClass.SEND_NODE_INFORMATION,
        ),
        fct.uint8(field="retVal"),
    ],
    "SendNodeInformationIncomingRequest": [
        fct.zwaveMessage(
            type=MessageType.REQUEST,
            _class=MessageClass.SEND_NODE_INFORMATION,
            inbound=True,
            outbound=False,
        ),
        fct.uint8(field="funcId"),
        fct.uint8(field="txStatus", enum=TransmitComplete),
        fct.binary(field="extraData", bytes=None),
    ],
    #########################################################################
    # SEND_DATA = 0x13
    "SendDataRequest": [
        fct.zwaveMessage(
            type=MessageType.REQUEST,
            _class=MessageClass.SEND_DATA,
            inbound=False,
            outbound=True,
            nodeIdField="nodeId",
        ),
        fct.uint8(field="nodeId"),
        fct.uint8(virtualfield="dataLength", value=Expr("len(data)")),
        fct.binary(field="data", bytes=Value("dataLength")),
        fct.uint8(field="txOptions", enum=TransmitOption),
        fct.uint8(field="funcId"),
    ],
    "SendDataResponse": [
        fct.zwaveMessage(
            type=MessageType.RESPONSE, _class=MessageClass.SEND_DATA
        ),
        fct.uint8(field="retVal"),
    ],
    "SendDataIncomingRequest": [
        fct.zwaveMessage(
            type=MessageType.REQUEST,
            _class=MessageClass.SEND_DATA,
            inbound=True,
            outbound=False,
        ),
        fct.uint8(field="funcId"),
        fct.uint8(field="txStatus", enum=TransmitComplete),
        fct.binary(field="extraData", bytes=None),
    ],
    #########################################################################
    # GET_VERSION = 0x15
    "GetVersionRequest": [
        fct.zwaveMessage(
            type=MessageType.REQUEST, _class=MessageClass.GET_VERSION
        )
    ],
    "GetVersionResponse": [
        fct.zwaveMessage(
            type=MessageType.RESPONSE, _class=MessageClass.GET_VERSION
        ),
        fct.nulTerminatedString(field="libraryVersion"),
        fct.uint8(field="libraryType", enum=LibraryType),
    ],
    #########################################################################
    # MEMORY_GET_ID = 0x20
    "MemoryGetIdRequest": [
        fct.zwaveMessage(
            type=MessageType.REQUEST, _class=MessageClass.MEMORY_GET_ID
        )
    ],
    "MemoryGetIdResponse": [
        fct.zwaveMessage(
            type=MessageType.RESPONSE, _class=MessageClass.MEMORY_GET_ID
        ),
        fct.uint32(field="homeId"),
        fct.uint8(field="controllerNodeId"),
    ],
    #########################################################################
    # GET_NODE_PROTOCOL_INFO = 0x41
    "GetNodeProtocolInfoRequest": [
        fct.zwaveMessage(
            type=MessageType.REQUEST,
            _class=MessageClass.GET_NODE_PROTOCOL_INFO,
        ),
        fct.uint8(field="nodeId"),
    ],
    "GetNodeProtocolInfoResponse": [
        fct.zwaveMessage(
            type=MessageType.RESPONSE,
            _class=MessageClass.GET_NODE_PROTOCOL_INFO,
        ),
        fct.uintbits(field="version", shift=0, mask=0x07),
        fct.uintbits(field="maxBaudRate", shift=3, mask=0x38, prevbyte=True),
        fct.boolean(field="routing", mask=0x40, prevbyte=True),
        fct.boolean(field="listening", mask=0x80, prevbyte=True),
        fct.boolean(field="security", mask=0x01, prevbyte=False),
        fct.boolean(field="controller", mask=0x02, prevbyte=True),
        fct.boolean(field="specificDevice", mask=0x04, prevbyte=True),
        fct.boolean(field="routingSlave", mask=0x08, prevbyte=True),
        fct.boolean(field="beamCapability", mask=0x10, prevbyte=True),
        fct.boolean(field="sensor250ms", mask=0x20, prevbyte=True),
        fct.boolean(field="sensor1000ms", mask=0x40, prevbyte=True),
        fct.boolean(field="optionalFunctionality", mask=0x80, prevbyte=True),
        fct.uint8(field="reserved"),
        fct.uint8(field="basic"),
        fct.uint8(field="generic"),
        fct.uint8(field="specific"),
    ],
    #########################################################################
    # DELETE_RETURN_ROUTE = 0x47
    "DeleteReturnRouteRequest": [
        fct.zwaveMessage(
            type=MessageType.REQUEST,
            _class=MessageClass.DELETE_RETURN_ROUTE,
            inbound=False,
            outbound=True,
            nodeIdField="nodeId",
        ),
        fct.uint8(field="nodeId"),
        fct.uint8(field="funcId"),
    ],
    "DeleteReturnRouteResponse": [
        fct.zwaveMessage(
            type=MessageType.RESPONSE, _class=MessageClass.DELETE_RETURN_ROUTE
        ),
        fct.uint8(field="retVal"),
    ],
    "DeleteReturnRouteIncomingRequest": [
        fct.zwaveMessage(
            type=MessageType.REQUEST,
            _class=MessageClass.DELETE_RETURN_ROUTE,
            inbound=True,
            outbound=False,
        ),
        fct.uint8(field="funcId"),
        fct.uint8(field="bStatus"),
    ],
    #########################################################################
    # APPLICATION_UPDATE = 0x49
    "ApplicationUpdateRequest": [
        fct.zwaveMessage(
            type=MessageType.REQUEST, _class=MessageClass.APPLICATION_UPDATE
        ),
        fct.uint8(field="status", enum=UpdateState),
        fct.uint8(field="nodeId"),
        fct.uint8(
            virtualfield="dataLength",
            value=Expr(
                "len(commandClasses)"
                " + (basic is not None) "
                " + (generic is not None)"
                " + (specific is not None)"
            ),
        ),
        fct.optional(
            field="basic", item=fct.uint8(), present=Expr("dataLength > 0")
        ),
        fct.optional(
            field="generic", item=fct.uint8(), present=Expr("dataLength > 1")
        ),
        fct.optional(
            field="specific", item=fct.uint8(), present=Expr("dataLength > 2")
        ),
        fct.array(
            field="commandClasses",
            length=Expr("max(0, dataLength - 3)"),
            items=fct.uint8(),
        ),
    ],
    #########################################################################
    # REQUEST_NODE_INFO = 0x60
    "RequestNodeInfoRequest": [
        fct.zwaveMessage(
            type=MessageType.REQUEST,
            _class=MessageClass.REQUEST_NODE_INFO,
            # nodeIdField='nodeId',
        ),
        fct.uint8(field="nodeId"),
    ],
    "RequestNodeInfoResponse": [
        fct.zwaveMessage(
            type=MessageType.RESPONSE, _class=MessageClass.REQUEST_NODE_INFO
        ),
        fct.boolean(field="success"),
    ],
    #########################################################################
    # GET_ROUTING_TABLE_LINE = 0x80
    "GetRoutingTableLineRequest": [
        fct.zwaveMessage(
            type=MessageType.REQUEST,
            _class=MessageClass.GET_ROUTING_TABLE_LINE,
        ),
        fct.uint8(field="nodeId"),
        fct.boolean(field="removeBad"),
        fct.boolean(field="removeNonReps"),
        fct.magic(bytes=b"\x00"),
    ],
    "GetRoutingTableLineResponse": [
        fct.zwaveMessage(
            type=MessageType.RESPONSE,
            _class=MessageClass.GET_ROUTING_TABLE_LINE,
        ),
        fct.bitset(field="nodes", offset=1, bytes=29),
    ],
}

#############################################################################

Message = types.ModuleType("Message")
for name, desc in descriptions.items():
    cls = ZWaveSerialization.createClass(name, desc)
    setattr(Message, name, cls)
