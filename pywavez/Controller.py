import asyncio
import bisect
import collections
import functools
import logging
import time
import traceback

from asyncinit import asyncinit

from pywavez.zwave import outboundMessageClass, inboundMessageFromBytes
from pywavez.zwave.Constants import LibraryType, MessageClass, MessageType
from pywavez.util import toCamelCase, waitForOne, spawnTask
from pywavez.ControllerNode import ControllerNode
from pywavez.Transmission import (
    Priority,
    MessageTransmission,
    SimpleQueue,
    MessageQueue,
)


class FuncIdManager:
    class TimeoutEvent:
        __slots__ = "id", "expires", "cancelled", "future"

        def __init__(self, id, expires):
            self.id = id
            self.expires = expires
            self.cancelled = False
            self.future = asyncio.Future()

        def __lt__(self, other):
            return self.expires < other.expires

    class FuncId:
        __slots__ = "_FuncId__id", "release", "future"

        def __init__(self, id, release, future):
            self.__id = id
            self.release = release
            self.future = future

        @property
        def value(self):
            return self.__id

    def __init__(self):
        self.__available_ids = collections.deque(range(1, 256))
        self.__event = asyncio.Event()
        self.__timeout_events_by_time = collections.deque()
        self.__timeout_events_by_id = {}

    async def get(self, timeout=90):
        now = time.monotonic()
        while not self.__available_ids:
            while self.__timeout_events_by_time and (
                self.__timeout_events_by_time[0].expires < now
                or self.__timeout_events_by_time[0].cancelled
            ):
                toe = self.__timeout_events_by_time.popleft()
                if self.__cancel(toe):
                    break

            if self.__available_ids:
                break

            self.__event.clear()
            if self.__timeout_events_by_time:
                timeout = self.__timeout_events_by_time[0].expires - now
                await waitForOne(self.__event.wait(), timeout=timeout)
            else:
                await self.__event.wait()
            now = time.monotonic()

        id = self.__available_ids.popleft()
        toe = self.TimeoutEvent(id, now + timeout)
        self.__timeout_events_by_id[id] = toe
        idx = bisect.bisect_right(self.__timeout_events_by_time, toe)
        self.__timeout_events_by_time.insert(idx, toe)
        return self.FuncId(id, lambda: self.__cancel(toe), toe.future)

    def set_result(self, id, result):
        self.__timeout_events_by_id[id].future.set_result(result)

    def __cancel(self, toe):
        if not toe.cancelled:
            toe.cancelled = True
            del self.__timeout_events_by_id[toe.id]
            self.__available_ids.append(toe.id)
            self.__event.set()
            return True


@asyncinit
class Controller:
    async def __init__(self, sp):
        self.__sp = sp
        self.__mq = MessageQueue()
        self.__node = [None] * 233
        self.__responseHandler = {
            MessageClass.SERIAL_API_GET_INIT_DATA: self.__handleSerialApiGetInitDataResponse
        }
        self.__incomingRequestHandler = {
            MessageClass.APPLICATION_UPDATE: self.__handleApplicationUpdateRequest,
            MessageClass.APPLICATION_COMMAND_HANDLER: self.__handleApplicationCommandHandlerRequest,
            MessageClass.SEND_DATA: self.__handleSendDataRequest,
        }
        self._funcIdManager = FuncIdManager()
        self._requestNodeInfoLock = asyncio.Lock()

        self._receivedMessages = SimpleQueue()
        self.hasMessage = self._receivedMessages.hasMessage
        self.waitForMessage = self._receivedMessages.waitForMessage
        self.takeMessage = self._receivedMessages.takeMessage

        self.__task = spawnTask(self.__taskImpl())

        cap = await self.__sendMessage(
            outboundMessageClass(
                MessageType.REQUEST, MessageClass.SERIAL_API_GET_CAPABILITIES
            )()
        )
        self.__manufacturer = (
            cap.manufacturerId,
            cap.manufacturerProduct,
            cap.manufacturerProductId,
        )
        self.__serialApiVersionRevision = (
            cap.serialApiVersion,
            cap.serialApiRevision,
        )
        funcs = []
        for f in cap.supportedFunctions:
            try:
                funcs.append(MessageClass(f))
            except ValueError:
                logging.warning(
                    f"Controller supports unknown message class { f }"
                )
        self.__setSupportedFunctions(funcs)

        if hasattr(self, "memoryGetId"):
            msg = await self.memoryGetId()
            self.__homeId = f"{ msg.homeId :08x}"
            self.__controllerNodeId = msg.controllerNodeId
        else:
            self.__homeId = None
            self.__controllerNodeId = 1  # best guess

        vr = await self.getVersion()
        self.__libraryVersion = vr.libraryVersion
        self.__libraryType = vr.libraryType

        # this will set self.__apiInitData
        await self.serialApiGetInitData()

        if self.__libraryType != LibraryType.BRIDGE_CONTROLLER and hasattr(
            self, "serialApiSetTimeouts"
        ):
            await self.serialApiSetTimeouts(rxAckTimeout=150, rxByteTimeout=15)

        # TODO: SERIAL_API_APPL_NODE_INFORMATION

        for id in sorted(self.__apiInitData.nodes):
            if id == self.__controllerNodeId:
                continue
            if not 1 <= id <= 232:
                logging.warning(f"Invalid node id { id }")
                continue
            self.__addNode(id)

    def __addNode(self, id):
        if self.__node[id] is not None:
            logging.warning(f"Tried to add already existing node { id }")
            return
        self.__node[id] = ControllerNode(id, self)

    async def shutdown(self):
        self.__task.cancel()
        await self.__sp.close()

    def sendCommand(
        self, node_id, command, *, endpoint=0, priority=Priority.DEFAULT
    ):
        return self._getNode(node_id).sendCommand(
            command, endpoint=endpoint, priority=priority
        )

    async def __taskImpl(self):
        msgtx = None
        tx_timeout = None

        while True:
            if msgtx is None:
                if not self.__sp.messageReady() and not self.__mq.hasMessage():
                    await waitForOne(
                        self.__mq.waitForMessage(), self.__sp.waitForMessage()
                    )
            else:
                if not self.__sp.messageReady():
                    await waitForOne(
                        self.__sp.waitForMessage(),
                        timeout=tx_timeout - time.monotonic(),
                    )

            while self.__sp.messageReady():
                msg = await next(self.__sp)
                try:
                    msg = inboundMessageFromBytes(msg)
                except Exception:
                    logging.warning(
                        f"Ignoring unknown incoming message: { msg.hex() }"
                    )
                    continue
                logging.debug(f"msg received: { msg !r}")
                if (
                    msgtx is not None
                    and msg.MessageType is MessageType.RESPONSE
                    and msg.MessageClass is msgtx.message.MessageClass
                ):
                    msgtx.transmitting = False
                    msgtx.finished = True
                    if msgtx.responseHandler is not None:
                        try:
                            msgtx.responseHandler(msgtx.message, msg)
                        except Exception as ex:
                            logging.warning(
                                f"Response handler raised exception: { ex !r}"
                            )
                    msgtx.set_result(msg)
                    msgtx = None
                    tx_timeout = None
                    continue
                if msg.MessageType is MessageType.REQUEST:
                    handler = self.__incomingRequestHandler.get(
                        msg.MessageClass
                    )
                    if handler is not None:
                        try:
                            for rmsg in handler(msg):
                                self._receivedMessages.append(rmsg)
                                logging.debug(
                                    f"msg received (after handler): { rmsg !r}"
                                )
                        except Exception as ex:
                            logging.warning(
                                "Incoming request handler raised exception: "
                                f"{ ex !r}"
                            )
                            traceback.print_exc()
                        msg = None
                if msg is not None:
                    self._receivedMessages.append(msg)

            if msgtx is None and self.__mq.hasMessage():
                if not self.__sp.idle:
                    # The SerialProtocol is busy with receiving or sending a
                    # message. Let's not interfere. Wait until idle state
                    # is reached, but also stop if there is a message ready.
                    await waitForOne(
                        self.__sp.waitForIdleState(),
                        self.__sp.waitForMessage(),
                    )
                    # Start over, so any received message is processed first.
                    continue
                msgtx = self.__mq.takeMessage()
                msgtx.transmitting = True
                logging.debug(f"Attempting transmission: { msgtx.message !r}")
                try:
                    data = msgtx.message.toBytes()
                except Exception as ex:
                    msgtx.set_exception(ex)
                    msgtx = None
                else:
                    logging.debug(f"outgoing: { msgtx.message !r}")
                    try:
                        await self.__sp.send(data)
                    except Exception as ex:
                        logging.info(f"Exception while sending: { ex !r}")
                        await asyncio.sleep(0.05)
                        if msgtx.retransmission >= msgtx.maxRetransmissions:
                            msgtx.set_exception(ex)
                        else:
                            msgtx.retransmission += 1
                            msgtx.pauseUntil = time.monotonic() + 1
                            msgtx.transmitting = False
                            self.__mq.add(msgtx)
                        msgtx = None
                    else:
                        tx_timeout = time.monotonic() + 5
            elif tx_timeout is not None and time.monotonic() >= tx_timeout:
                msgtx.retransmission += 1
                msgtx.pauseUntil = time.monotonic() + 1
                msgtx.transmitting = False
                self.__mq.add(msgtx)
                msgtx = None

    def __sendMessage(self, message, **kwargs):
        msgtx = MessageTransmission(message, **kwargs)
        self.__mq.add(msgtx)
        return msgtx

    def __setSupportedFunctions(self, message_classes):
        self.__supportedFunctions = message_classes = frozenset(
            message_classes
        )
        for msgclass in MessageClass:
            try:
                cl = outboundMessageClass(MessageType.REQUEST, msgclass)
            except KeyError:
                continue
            name = toCamelCase(msgclass.name)
            if msgclass in message_classes:
                if cl.NodeIdField is None:

                    def node_id_func(msg):
                        return None

                else:
                    node_id_func = (lambda nif: lambda msg: getattr(msg, nif))(
                        cl.NodeIdField
                    )
                resp_handler = self.__responseHandler.get(msgclass)
                func = self.__makeCallFunction(cl, node_id_func, resp_handler)
                implfunc = getattr(self, f"_{ name }Impl", None)
                if implfunc is not None:
                    func = functools.partial(implfunc, func)
            else:
                func = raise_not_implemented
            setattr(self, name, func)

    def __makeCallFunction(self, cl, node_id_func, resp_handler):
        def func(PRIORITY=Priority.DEFAULT, **kwargs):
            msg = cl(**kwargs)
            logging.debug(f"makeCallFunction func : { msg !r}")
            node_id = node_id_func(msg)
            return self.__sendMessage(
                msg,
                nodeId=node_id,
                priority=PRIORITY,
                response_handler=resp_handler,
            )

        return func

    def _getNode(self, id):
        if not 1 <= id <= 232:
            raise Exception(f"Bogus node id: { id }")
        node = self.__node[id]
        if node is None:
            raise Exception(f"Unknown node id: { id }")
        return node

    def __handleSerialApiGetInitDataResponse(self, req, resp):
        self.__apiInitData = resp

    def __handleApplicationUpdateRequest(self, msg):
        if msg.nodeId == 0:
            yield msg
        else:
            node = self._getNode(msg.nodeId)
            yield from node.setCommandClasses(0, msg.commandClasses)
            node.nodeActive()

    def __handleSendDataRequest(self, msg):
        try:
            self._funcIdManager.set_result(msg.funcId, msg.txStatus)
        except Exception as ex:
            logging.warning(f"Controller.__handleSendDataRequest: { ex !r}")
        yield msg

    def __handleApplicationCommandHandlerRequest(self, msg):
        try:
            node = self._getNode(msg.nodeId)
        except Exception:
            yield msg
        else:
            # yield from node.handleApplicationCommandHandlerRequest(msg)
            for x in node.handleApplicationCommandHandlerRequest(msg):
                yield x

    @property
    def homeId(self):
        return self.__homeId

    @property
    def controllerNodeId(self):
        return self.__controllerNodeId

    @property
    def nodeIds(self):
        return set(self.__apiInitData.nodes)


def raise_not_implemented(**kwargs):
    raise NotImplementedError("ZWave controller does not implement function")
