import unittest

from pywavez.zwave import Message, inboundMessageFromBytes
from pywavez.zwave.Constants import LibraryType


class TestGetVersion(unittest.TestCase):
    def test_GetVersionResponse(self):
        data = bytes.fromhex("01155a2d5761766520342e30350001")
        obj = inboundMessageFromBytes(data)
        self.assertEqual(type(obj), Message.GetVersionResponse)
        self.assertEqual(obj.libraryVersion, "Z-Wave 4.05")
        self.assertEqual(obj.libraryType, LibraryType.STATIC_CONTROLLER)
        self.assertEqual(obj.toBytes(), data)

    def test_SerialApiGetCapabilitiesResponse(self):
        data = bytes.fromhex(
            "0107aabb12345678abcd00020820800002000000"
            "0000000000000000000000000000000000000000"
            "0000"
        )
        obj = inboundMessageFromBytes(data)
        self.assertEqual(type(obj), Message.SerialApiGetCapabilitiesResponse)
        self.assertEqual(obj.serialApiVersion, 0xAA)
        self.assertEqual(obj.serialApiRevision, 0xBB)
        self.assertEqual(obj.manufacturerId, 0x1234)
        self.assertEqual(obj.manufacturerProduct, 0x5678)
        self.assertEqual(obj.manufacturerProductId, 0xABCD)
        self.assertEqual(obj.supportedFunctions, {10, 20, 30, 40, 50})
        self.assertEqual(obj.toBytes(), data)

    def test_SerialApiGetInitDataResponse(self):
        data = bytes.fromhex(
            "010205001dadff3f000000000000000000000000"
            "00000000000000000000000000000500"
        )
        obj = inboundMessageFromBytes(data)
        self.assertEqual(type(obj), Message.SerialApiGetInitDataResponse)
        self.assertEqual(obj.serialApiApplicationVersion, 5)
        self.assertEqual(obj.isSlave, False)
        self.assertEqual(obj.timerSupport, False)
        self.assertEqual(obj.isSecondary, False)
        self.assertEqual(obj.isSIS, False)
        self.assertEqual(
            obj.nodes,
            {
                1,
                3,
                4,
                6,
                8,
                9,
                10,
                11,
                12,
                13,
                14,
                15,
                16,
                17,
                18,
                19,
                20,
                21,
                22,
            },
        )
        self.assertEqual(obj.chipType, 5)
        self.assertEqual(obj.chipVersion, 0)
        self.assertEqual(obj.toBytes(), data)


if __name__ == "__main__":
    unittest.main()
