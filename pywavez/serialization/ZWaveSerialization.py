import typing

from pywavez.serialization.Serialization import Serialization


class ZWaveSerialization(Serialization):
    def _func_zwaveMessage(
        self,
        attributes,
        *,
        _type: "MessageType",
        _class: "MessageClass",
        _outbound: bool = True,
        _inbound: bool = True,
        _nodeIdField: typing.Optional[str] = None,
    ):
        attributes["MessageType"] = _type
        attributes["MessageClass"] = _class
        attributes["Outbound"] = _outbound
        attributes["Inbound"] = _inbound
        attributes["NodeIdField"] = _nodeIdField
        return self._func_magic(
            attributes, _bytes=bytes((_type.value, _class.value))
        )

    def _func_zwaveCommand(self, attributes, *, _class, _cmd, _mask=0xFF):
        attributes["CommandClassCode"] = _class
        attributes["CommandCode"] = _cmd
        attributes["CommandCodeMask"] = _mask
        reader, writer, fieldtype = self._func_magic(
            attributes, _bytes=bytes((_class, _cmd))
        )

        if _mask != 0xFF:

            def reader(ba, pos, eval):
                if len(ba) < pos + 2:
                    raise Exception("short message")
                if ba[pos] != _class or ba[pos + 1] & _mask != _cmd:
                    raise Exception("magic mismatch")
                return pos + 2, None

        return reader, writer, fieldtype

    def _func_variantMarker(self, attributes, *, _marker: int):
        def reader(ba, pos, eval):
            mp = ba.find(_marker, pos)
            if mp == -1:
                return len(ba), ba[pos:]
            else:
                return mp + 1, ba[pos:mp]

        def writer(value, ba, pos, eval):
            val = value + bytes((_marker,))
            length = len(val)
            ba[pos : pos + length] = val
            return ba, pos + length

        return reader, writer, str


class ZWaveCommandClassBase:
    ...


# resolve forward references in type hints above
from pywavez.zwave.Constants import MessageType, MessageClass  # noqa: E402
