import importlib
import pkgutil
import typing

from .Constants import MessageType, MessageClass
from .Message import Message
from pywavez.serialization.ParseError import ParseError


_inbound_message_classes = {
    MessageType.REQUEST.value: {},
    MessageType.RESPONSE.value: {},
}
_outbound_message_classes = {
    MessageType.REQUEST.value: {},
    MessageType.RESPONSE.value: {},
}

for name in dir(Message):
    if name.startswith("_"):
        continue
    cls = getattr(Message, name)
    if cls.Inbound:
        _inbound_message_classes[cls.MessageType.value][
            cls.MessageClass.value
        ] = cls
    if cls.Outbound:
        _outbound_message_classes[cls.MessageType.value][
            cls.MessageClass.value
        ] = cls


def messageFromBytes(inbound: bool, data: typing.ByteString):
    if len(data) < 2:
        raise ParseError("short message")
    try:
        cls = (
            _inbound_message_classes if inbound else _outbound_message_classes
        )[data[0]][data[1]]
    except KeyError:
        raise ParseError(
            f"unknown message type or class 0x{data[0]:02x} 0x{data[1]:02x} "
            f'({ "inbound" if inbound else "outbound" })'
        )
    return cls.fromBytes(data)


def inboundMessageFromBytes(data: typing.ByteString):
    return messageFromBytes(True, data)


def outboundMessageFromBytes(data: typing.ByteString):
    return messageFromBytes(False, data)


def inboundMessageClass(type: MessageType, _class: MessageClass):
    return _inbound_message_classes[type.value][_class.value]


def outboundMessageClass(type: MessageType, _class: MessageClass):
    return _outbound_message_classes[type.value][_class.value]


_command_classes = {}
for module_info in pkgutil.iter_modules(path=__path__):
    mod = module_info.name
    if not module_info.ispkg and mod.startswith("CommandClass"):
        cls = getattr(importlib.import_module(f".{ mod }", __package__), mod)
        _command_classes[cls.code] = cls
        globals()[mod] = cls
_command_class_codes = frozenset(_command_classes)


def getSupportedCommandClassCodes():
    return _command_class_codes


def getCommandClassVersion(cmd_class, version):
    return _command_classes[cmd_class].versions[version]
