class NodeUpdate:
    __slots__ = ("id",)

    def __init__(self, id):
        self.id = id


class NodeUpdateTypes:
    class ProtocolInfo(NodeUpdate):
        __slots__ = ("protocolInfo",)

        def __init__(self, id, pi):
            super().__init__(id)
            self.protocolInfo = pi

        def __repr__(self):
            return (
                "<NodeUpdate.ProtocolInfo"
                f" nodeId={ self.id }"
                f" protocolInfo={ self.protocolInfo !r}"
                ">"
            )

    class CommandClass(NodeUpdate):
        __slots__ = "endpoint", "class_", "code", "version"

        def __init__(self, id, endpoint, class_, code, version):
            super().__init__(id)
            self.endpoint = endpoint
            self.class_ = class_
            self.code = code
            self.version = version

        def __repr__(self):
            return (
                "<NodeUpdate.CommandClass"
                f" nodeId={ self.id }"
                f" endpoint={ self.endpoint }"
                f" class_={ self.class_ !r}"
                f" code={ self.code }"
                f" version={ self.version }"
                ">"
            )

    class ManufacturerInfo(NodeUpdate):
        __slots__ = "manufacturerId", "productTypeId", "productId"

        def __init__(self, id, cmd):
            super().__init__(id)
            self.manufacturerId = cmd.manufacturerId
            self.productTypeId = cmd.productTypeId
            self.productId = cmd.productId

        def __repr__(self):
            return (
                "<NodeUpdate.ManufacturerInfo"
                f" nodeId={ self.id }"
                f" manufacturerId=0x{ self.manufacturerId :04x}"
                f" productTypeId=0x{ self.productTypeId :04x}"
                f" productId=0x{ self.productId :04x}"
                ">"
            )


for key in dir(NodeUpdateTypes):
    if not key.startswith("_"):
        setattr(NodeUpdate, key, getattr(NodeUpdateTypes, key))
