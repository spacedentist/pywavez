import enum
import functools
import inspect
import keyword
import logging
import sys
import types
import typing

from .ParseError import ParseError


class Serialization:
    @classmethod
    def createClass(cls, name, description):
        self = cls()
        slots = []
        attributes = {"__slots__": slots, "__annotations__": {}}
        reader_funcs = []
        writer_funcs = []
        default_values = {}

        for item in description:
            reader, writer, fieldtype = self._getItemFunction(item, attributes)
            field = item.get("field")
            virtualfield = item.get("virtualfield")
            value = item.get("value")
            if field is not None:
                field = str(field)
                if (
                    not field.isidentifier()
                    or keyword.iskeyword(field)
                    or field.startswith("__")
                ):
                    raise Exception(f"Invalid field name: { field !r}")
                if field in slots:
                    raise Exception(f"Duplicate field name: { field !r}")
                field = sys.intern(field)
                slots.append(field)
                attributes["__annotations__"][field] = fieldtype
                if reader:
                    reader = fieldReader(reader, field)
                if writer:
                    writer = fieldWriter(writer, field)
                try:
                    default_values[field] = item["defaultValue"]
                except KeyError:
                    pass
            else:
                if reader:
                    reader = fieldReader(reader, virtualfield)
                if writer:
                    writer = virtualfieldWriter(writer, virtualfield, value)
            if reader:
                reader_funcs.append(reader)
            if writer:
                writer_funcs.append(writer)

        def readFromBytes(cls, ba: bytes, pos: int = 0):
            obj = cls.__new__(cls)
            d = {"__obj": obj}
            ba = bytes(ba)
            for f in reader_funcs:
                d["_bytesRemaining"] = len(ba) - pos
                pos = f(d, ba, pos)
                if pos > len(ba):
                    raise Exception("position beyond data buffer")
            for key in slots:
                setattr(obj, key, d[key])
            return pos, obj

        def fromBytes(cls, ba: bytes):
            pos, obj = cls.readFromBytes(ba)
            if pos < len(ba):
                logging.warning(
                    f"spurious data at end of message: { ba[pos:].hex() }"
                )
            return obj

        def toBytes(self) -> bytearray:
            d = dict((k, getattr(self, k)) for k in self.__slots__)
            d["__obj"] = self
            ba = bytearray()
            pos = 0
            for f in writer_funcs:
                ba, pos = f(d, ba, pos)
            if len(ba) > pos:
                return ba[0:pos]
            elif len(ba) < pos:
                raise SystemExit("toBytes produced short output")
            return ba

        if slots:
            constructor_def = "def __init__(__self, *, {}):\n".format(
                ", ".join(slots)
            )
            for key in slots:
                constructor_def += f"    __self.{ key } = { key }\n"
            namespace = {}
            exec(constructor_def, namespace)
            constructor = attributes["__init__"] = namespace["__init__"]
            constructor.__kwdefaults__ = default_values

        attributes["readFromBytes"] = classmethod(readFromBytes)
        attributes["fromBytes"] = classmethod(fromBytes)
        attributes["toBytes"] = toBytes
        attributes["__repr__"] = objectRepr(name)

        return type(name, (), attributes)

    @classmethod
    def functions(cls):
        result = {}
        for funcname in (x for x in dir(cls) if x.startswith("_func_")):
            func = getattr(cls, funcname)
            argspec = inspect.getfullargspec(func)
            vars = frozenset(argspec.kwonlyargs)
            vars_without_defaults = (
                vars.difference(argspec.kwonlydefaults)
                if argspec.kwonlydefaults
                else vars
            )
            funcname = funcname[6:]  # lose '_func_' prefix
            result[funcname] = makeDescriptionItemFactory(
                funcname, vars, vars_without_defaults
            )
        return result

    @classmethod
    def functionsModule(cls):
        mod = types.ModuleType("functions")
        mod.__dict__.update(cls.functions())
        return mod

    def _getItemFunction(self, item, attributes):
        funcname = item["func"]
        return getattr(self, "_func_" + funcname)(
            attributes,
            **dict((k, v) for k, v in item.items() if k.startswith("_")),
        )

    @staticmethod
    def _func_noop():
        def reader(ba, pos, eval):
            return pos, None

        def writer(value, ba, pos, eval):
            return ba, pos

        return reader, writer, None

    @staticmethod
    def _func_magic(attributes, *, _bytes: typing.ByteString):
        length = len(_bytes)

        def reader(ba, pos, eval):
            if len(ba) < pos + length:
                raise Exception("short message")
            if ba[pos : pos + length] != _bytes:
                raise Exception("magic mismatch")
            return pos + length, None

        def writer(value, ba, pos, eval):
            ba[pos:] = _bytes
            return ba, pos + length

        return reader, writer, None

    @staticmethod
    def _func_skip(attributes, *, _bytes: int = 1):
        def reader(ba, pos, eval):
            if len(ba) < pos + _bytes:
                raise Exception("short message")
            return pos + _bytes, None

        def writer(value, ba, pos, eval):
            ba[pos:] = b"\x00" * _bytes
            return ba, pos + _bytes

        return reader, writer, None

    def _func_nulTerminatedString(self, attributes, *, _encoding="ascii"):
        def reader(ba, pos, eval):
            nul = ba.find(0, pos)
            if nul == -1:
                raise Exception("no nul")
            return nul + 1, ba[pos:nul].decode(_encoding)

        def writer(value, ba, pos, eval):
            val = value.encode(_encoding) + b"\x00"
            length = len(val)
            ba[pos : pos + length] = val
            return ba, pos + length

        return reader, writer, str

    def _func_int(
        self,
        attributes,
        *,
        _bytes=1,
        _unsigned=False,
        _enum: typing.Optional[type] = None,
    ):
        conv_enum, convback_enum, returntype = prepareEnum(_enum)
        if _unsigned:

            def conv(x):
                return conv_enum(bytes2uint(x))

            def convback(x, b):
                return uint2bytes(convback_enum(x), b)

        else:

            def conv(x):
                return conv_enum(bytes2sint(x))

            def convback(x, b):
                return sint2bytes(convback_enum(x), b)

        def reader(ba, pos, eval):
            b = eval(_bytes)
            return pos + b, conv(ba[pos : pos + b])

        def writer(value, ba, pos, eval):
            b = eval(_bytes)
            ba[pos : pos + 1] = convback(value, b)
            return ba, pos + b

        return reader, writer, returntype

    _func_int8 = _func_int
    _func_int16 = functools.partialmethod(_func_int, _bytes=2)
    _func_int24 = functools.partialmethod(_func_int, _bytes=3)
    _func_int32 = functools.partialmethod(_func_int, _bytes=4)

    _func_uint = functools.partialmethod(_func_int, _unsigned=True)
    _func_uint8 = _func_uint
    _func_uint16 = functools.partialmethod(_func_int, _unsigned=True, _bytes=2)
    _func_uint24 = functools.partialmethod(_func_int, _unsigned=True, _bytes=3)
    _func_uint32 = functools.partialmethod(_func_int, _unsigned=True, _bytes=4)

    def _func_uintbits(
        self,
        attributes,
        *,
        _shift=0,
        _mask=0xFF,
        _prevbyte=False,
        _enum: typing.Optional[type] = None,
    ):
        conv, convback, returntype = prepareEnum(_enum)

        def reader(ba, pos, eval):
            if _prevbyte:
                pos -= 1
            return pos + 1, conv((ba[pos] >> _shift) & _mask)

        def writer(value, ba, pos, eval):
            if not _prevbyte:
                pos += 1
                if pos >= len(ba):
                    ba += b"\x00" * (pos - len(ba))
            ba[pos - 1] |= (convback(value) & _mask) << _shift
            return ba, pos

        return reader, writer, returntype

    def _func_bitset(self, attributes, *, _offset=0, _bytes=1, _enum=None):
        conv, convback, elementtype = prepareEnum(_enum)

        def reader(ba, pos, eval):
            if _bytes is None:
                length = len(ba) - pos
            else:
                length = eval(_bytes)
            res = set()

            for idx in range(length):
                for bit in range(8):
                    if ba[pos + idx] & (1 << bit):
                        res.add(conv(idx * 8 + bit + _offset))

            return pos + length, res

        def writer(value, ba, pos, eval):
            if _bytes is None:
                length = (max(value) - _offset) // 8 + 1
            else:
                length = eval(_bytes)

            ba[pos : pos + length] = setbits(
                bytearray(length), map(convback, value), _offset
            )

            return ba, pos + length

        return reader, writer, typing.Set[elementtype]

    def _func_binary(self, attributes, *, _bytes=None):
        def reader(ba, pos, eval):
            if _bytes is None:
                length = len(ba) - pos
            else:
                length = eval(_bytes)
            return pos + length, ba[pos : pos + length]

        def writer(value, ba, pos, eval):
            if _bytes is None:
                length = len(value)
            else:
                length = eval(_bytes)
            ba[pos : pos + length] = value
            return ba, pos + length

        return reader, writer, typing.ByteString

    def _func_boolean(self, attributes, *, _mask=0xFF, _prevbyte=False):
        def reader(ba, pos, eval):
            if not _prevbyte:
                pos += 1
            return pos, bool(ba[pos - 1] & _mask)

        def writer(value, ba, pos, eval):
            if not _prevbyte:
                pos += 1
                if pos >= len(ba):
                    ba += b"\x00" * (pos - len(ba))
            if value:
                ba[pos - 1] |= _mask
            return ba, pos

        return reader, writer, bool

    def _func_optional(self, attributes, *, _item, _present):
        itemrdr, itemwtr, itemtype = self._getItemFunction(_item, attributes)

        def reader(ba, pos, eval):
            if eval(_present):
                return itemrdr(ba, pos, eval)
            else:
                return pos, None

        def writer(value, ba, pos, eval):
            p = eval(_present)
            if p is not None and not p and value is not None:
                raise Exception("optional mismatch")
            if p or value is not None:
                ba, pos = itemwtr(value, ba, pos, eval)
            return ba, pos

        return reader, writer, typing.Optional[itemtype]

    def _func_array(self, attributes, *, _items, _length=None):
        itemrdr, itemwtr, itemtype = self._getItemFunction(_items, attributes)

        def reader(ba, pos, eval):
            length = eval(_length)
            res = []
            if length is None:
                while pos < len(ba):
                    pos, value = itemrdr(ba, pos, eval)
                    res.append(value)
            else:
                for i in range(length):
                    pos, value = itemrdr(ba, pos, eval)
                    res.append(value)
            return pos, res

        def writer(value, ba, pos, eval):
            length = eval(_length)
            if length is not None and len(value) != length:
                raise Exception("array length mismatch")
            for i in value:
                ba, pos = itemwtr(i, ba, pos, eval)
            return ba, pos

        return reader, writer, typing.List[itemtype]

    def _func_classvar(self, attributes, *, _name, _val):
        attributes[_name] = _val
        return None, None, None

    def _func_object(self, attributes, *, _type):
        def reader(ba, pos, eval):
            t = eval(_type)
            return t.readFromBytes(ba, pos)

        def writer(value, ba, pos, eval):
            t = eval(_type)
            if not isinstance(value, t):
                raise Exception(f"object does not match type { t !r}")
            value = value.toBytes()
            length = len(value)
            ba[pos : pos + length] = value
            return ba, pos + length

        return reader, writer, None


class Expr:
    def __init__(self, expr):
        self.__expr = compile(expr, f"<Expr { expr !r}>", "eval")

    def __call__(self, locals_dict):
        return eval(
            self.__expr, {"__builtins__": stripped_down_builtins}, locals_dict
        )


class Value:
    def __init__(self, key):
        self.__key = key

    def __call__(self, locals_dict):
        return locals_dict.get(self.__key)


class ExprValueEvaluator:
    def __init__(self, state):
        self.state = state

    def __call__(self, x):
        if isinstance(x, (Value, Expr)):
            return x(self.state)
        else:
            return x


def fieldReader(rdr, field):
    def reader(state, ba, pos):
        eval = ExprValueEvaluator(state)
        pos, value = rdr(ba, pos, eval)
        if field is not None:
            state[field] = value
        return pos

    return reader


def fieldWriter(wtr, field):
    def writer(state, ba, pos):
        eval = ExprValueEvaluator(state)
        return wtr(state[field], ba, pos, eval)

    return writer


def virtualfieldWriter(wtr, virtualfield, value):
    def writer(state, ba, pos):
        eval = ExprValueEvaluator(state)
        val = eval(value)
        if virtualfield is not None:
            state[virtualfield] = val
        return wtr(val, ba, pos, eval)

    return writer


def prepareEnum(_enum):
    if _enum is not None and not issubclass(_enum, enum.Enum):
        raise Exception("'enum' field must be None or a subclass of enum.Enum")
    if _enum is None:
        conv = convback = lambda x: x
        returntype = int
    elif issubclass(_enum, enum.IntEnum):

        def conv(x):
            try:
                return _enum(x)
            except ValueError:
                return int(x)

        def convback(x):
            return int(x)

        returntype = typing.Union[_enum, int]
    else:
        conv = _enum

        def convback(x):
            return x.value

        returntype = _enum

    return conv, convback, returntype


def objectRepr(name):
    def __repr__(self):
        p = ", ".join(
            f"{ k }={ getattr(self, k, '<undefined>') !r}"
            for k in self.__slots__
        )
        return f"{ name }({ p })"

    return __repr__


def bytes2uint(b: typing.ByteString) -> int:
    res = 0
    for i in b:
        res = (res << 8) | i
    return res


def bytes2sint(b: typing.ByteString) -> int:
    v = bytes2uint(b)
    if v & (1 << (len(b) * 8 - 1)):
        v -= 1 << (len(b) * 8)
    return v


def uint2bytes(v: int, b: int) -> bytearray:
    return bytearray((v >> ((b - p - 1) * 8)) & 0xFF for p in range(b))


def sint2bytes(v: int, b: int) -> bytearray:
    if v < 0:
        v += 1 << (b * 8)
    return uint2bytes(v, b)


def setbits(ba, bits, offset):
    length = len(ba)
    high = length * 8

    for b in bits:
        v = b - offset
        if 0 <= v < high:
            ba[v // 8] |= 1 << (v % 8)
        else:
            raise ParseError("bit number out of range")
    return ba


reserved_field_names = frozenset(
    ("field", "virtualfield", "value", "defaultValue")
)


def makeDescriptionItemFactory(funcname, vars, vars_without_defaults):
    if any((not v.startswith("_")) for v in vars):
        raise Exception(
            "all parameter names must start with _: " + " ".join(vars)
        )

    def factory(**kwargs):
        params = dict(
            (
                k
                if k.startswith("_") or k in reserved_field_names
                else f"_{ k }",
                v,
            )
            for k, v in kwargs.items()
        )
        argnames = frozenset(p for p in params if p.startswith("_"))
        missing_vars = vars_without_defaults.difference(argnames)
        if missing_vars:
            raise Exception("missing parameters: " + " ".join(missing_vars))
        invalid_vars = set(argnames).difference(vars)
        if invalid_vars:
            raise Exception("invalid parameters: " + " ".join(invalid_vars))
        params["func"] = funcname
        return params

    return factory


def assertEqual(x, *y):
    if any(x != yy for yy in y):
        raise Exception(f"equality assertion failed { (x,) + tuple(y) !r}")
    return x


def uintsize(x):
    x = int(x)
    if x < 0:
        raise Exception("negative number passed to uintsize")
    size = 1
    while x > 255:
        size += 1
        x >>= 8
    return size


def intsize(x):
    x = int(x)
    size = 1
    if x < 0:
        x = -x
        while x > 128:
            size += 1
            x >>= 8
    else:
        while x >= 128:
            size += 1
            x >>= 8
    return size


stripped_down_builtins = types.ModuleType("builtins")
stripped_down_builtins.assertEqual = assertEqual
stripped_down_builtins.intsize = intsize
stripped_down_builtins.len = len
stripped_down_builtins.max = max
stripped_down_builtins.min = min
stripped_down_builtins.uintsize = uintsize
