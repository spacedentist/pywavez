import unittest

from pywavez.serialization.Serialization import Expr, Serialization


class TestGetVersion(unittest.TestCase):
    def test_foo(self):
        s = Serialization()
        f = s.functionsModule()

        GetVersionResponse = s.createClass(
            "GetVersionResponse",
            [
                f.magic(bytes=b"\x01\x15"),
                f.nulTerminatedString(field="libraryVersion"),
                f.uint8(field="libraryType"),
            ],
        )

        data = bytes.fromhex("01155a2d5761766520342e30350001")
        obj = GetVersionResponse.fromBytes(data)
        self.assertEqual(obj.libraryVersion, "Z-Wave 4.05")
        self.assertEqual(obj.libraryType, 1)
        self.assertEqual(obj.toBytes(), data)

    def test_foo2(self):
        s = Serialization()
        f = s.functionsModule()

        Class = s.createClass(
            "Class",
            [
                f.uint8(field="sensorType"),
                f.uintbits(field="size", shift=0, mask=0x07, prevbyte=False),
                f.uintbits(field="scale", shift=3, mask=0x03, prevbyte=True),
                f.uintbits(
                    field="precision", shift=5, mask=0x07, prevbyte=True
                ),
                f.uint(field="sensorValue", bytes=Expr("size")),
            ],
        )

        data = bytes.fromhex("014208ca")
        obj = Class.fromBytes(data)
        self.assertEqual(obj.size, 2)
        self.assertEqual(obj.scale, 0)
        self.assertEqual(obj.precision, 2)
        self.assertEqual(obj.sensorValue, 2250)
        self.assertEqual(obj.toBytes(), data)

    def test_array(self):
        s = Serialization()
        f = s.functionsModule()

        Class = s.createClass(
            "Class",
            [
                f.uint8(virtualfield="length", value=Expr("len(data)")),
                f.array(field="data", length=Expr("length"), items=f.uint8()),
                f.uint8(field="foo"),
                f.array(field="data2", length=3, items=f.uint8()),
                f.array(
                    field="x",
                    length=3,
                    items=f.array(length=3, items=f.uint8()),
                ),
            ],
        )

        data = bytes.fromhex("050b0c0d0e0f64202122010203040506070809")
        obj = Class.fromBytes(data)
        self.assertEqual(obj.data, [11, 12, 13, 14, 15])
        self.assertEqual(obj.foo, 100)
        self.assertEqual(obj.data2, [32, 33, 34])
        self.assertEqual(obj.x, [[1, 2, 3], [4, 5, 6], [7, 8, 9]])
        self.assertEqual(obj.toBytes(), data)

    def test_optional(self):
        s = Serialization()
        f = s.functionsModule()

        Class = s.createClass(
            "Class",
            [
                f.boolean(
                    virtualfield="b1", value=Expr("v1 is not None"), mask=0x01
                ),
                f.boolean(
                    virtualfield="b2",
                    value=Expr("v2 is not None"),
                    mask=0x02,
                    prevbyte=True,
                ),
                f.boolean(
                    virtualfield="b3",
                    value=Expr("v3 is not None"),
                    mask=0x04,
                    prevbyte=True,
                ),
                f.boolean(
                    virtualfield="b4",
                    value=Expr("v4 is not None"),
                    mask=0x08,
                    prevbyte=True,
                ),
                f.optional(field="v1", present=Expr("b1"), item=f.uint8()),
                f.optional(field="v2", present=Expr("b2"), item=f.uint8()),
                f.optional(field="v3", present=Expr("b3"), item=f.uint16()),
                f.optional(field="v4", present=Expr("b4"), item=f.uint16()),
            ],
        )

        data = bytes.fromhex("05123456")
        obj = Class.fromBytes(data)
        self.assertEqual(obj.v1, 0x12)
        self.assertEqual(obj.v2, None)
        self.assertEqual(obj.v3, 0x3456)
        self.assertEqual(obj.v4, None)
        self.assertEqual(obj.toBytes(), data)

    def test_constructor(self):
        s = Serialization()
        f = s.functionsModule()

        Class = s.createClass(
            "Class",
            [
                f.nulTerminatedString(field="x", defaultValue="foo"),
                f.nulTerminatedString(field="y"),
                f.nulTerminatedString(field="z", defaultValue="bar"),
            ],
        )

        obj = Class(y="yeiks")
        self.assertEqual(obj.x, "foo")
        self.assertEqual(obj.y, "yeiks")
        self.assertEqual(obj.z, "bar")

        obj = Class(x="xxx", z="xxz", y="yeiks")
        self.assertEqual(obj.x, "xxx")
        self.assertEqual(obj.y, "yeiks")
        self.assertEqual(obj.z, "xxz")


if __name__ == "__main__":
    unittest.main()
