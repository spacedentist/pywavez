import asyncio
import functools
import logging
import random
import time
import traceback

from pywavez.NodeUpdate import NodeUpdate
from pywavez.zwave import getCommandClassVersion
from pywavez.zwave.Constants import (
    CommandClass,
    TransmitComplete,
    TransmitOption,
)
from pywavez.util import spawnTask, waitForOne

from pywavez.ReceivedCommand import ReceivedCommand
from pywavez.Transmission import Priority, CommandTransmission, MessageQueue


class ControllerNode:
    def __init__(self, id, controller):
        self.__id = id
        self.__controller = controller

        self.protocolInfo = None
        self.manufacturerInfo = None
        self.commandClassCodes = {}  # endpoint -> tuple[CommandClass]
        self.commandQueue = MessageQueue()
        self.commandClassVersion = {}  # (endpoint, CommandClass) -> version
        self.commandClass = {}  # (endpoint, CommandClass) -> Python class
        self.endPointReport = None
        self.nodeActiveEvent = asyncio.Event()
        self.noAckCount = 0
        self.noAckCountThreshold = 3
        self.wakeUpNotificationEvent = asyncio.Event()
        self.sendsWakeUpNotifications = False
        self.initializationTask = spawnTask(
            self.__nodeInitializationTaskImpl()
        )
        self.commandDispatcherTask = spawnTask(
            self.__commandDispatcherTaskImpl()
        )

        self.commandHandler = {
            (CommandClass.VERSION, 0x14): self.versionReportHandler,
            (
                CommandClass.MANUFACTURER_SPECIFIC,
                0x05,
            ): self.manufacturerSpecificReportHandler,
            (
                CommandClass.MULTI_CHANNEL,
                0x08,
            ): self.multiChannelEndpointReportHandler,
            (
                CommandClass.MULTI_CHANNEL,
                0x0A,
            ): self.multiChannelCapabilityReportHandler,
            (
                CommandClass.MULTI_CHANNEL,
                0x0D,
            ): self.multiChannelCmdEncapHandler,
            (CommandClass.WAKE_UP, 0x07): self.wakeUpNotificationHandler,
        }

    @property
    def id(self):
        return self.__id

    def shutdown(self):
        if self.initializationTask is not None:
            self.initializationTask.cancel()
            self.initializationTask = None
        if self.commandDispatcherTask is not None:
            self.commandDispatcherTask.cancel()
            self.commandDispatcherTask = None

    def nodeActive(self):
        self.nodeActiveEvent.set()

    def sendCommand(self, command, *, endpoint=0, priority=Priority.DEFAULT):
        cmdtx = CommandTransmission(
            command, nodeId=self.__id, endpoint=endpoint, priority=priority
        )
        self.commandQueue.add(cmdtx)
        return cmdtx

    def setCommandClasses(self, endpoint, cc_codes):
        try:
            cc_codes = cc_codes[0 : cc_codes.index(0xEF)]
        except ValueError:
            ...
        cc = []
        for code in cc_codes:
            try:
                cc.append(CommandClass(code))
            except ValueError:
                cc.append(code)
        cc = tuple(cc)
        self.commandClassCodes[endpoint] = cc

        for i in cc:
            vers = self.commandClassVersion.get((endpoint, i))
            cc_class = self.commandClass.get((endpoint, i))
            yield NodeUpdate.CommandClass(
                self.__id, endpoint, cc_class, i, vers
            )

    def handleApplicationCommandHandlerRequest(self, msg, endpoint=0):
        try:
            parsed_command = self.parse_command(msg.payload, endpoint)
        except Exception as ex:
            logging.warning(
                "Error parsing APPLICATION_COMMAND_HANDLER payload: "
                f"{ msg.payload !r} node={ self.__id } "
                f"exception: { ex !r}"
            )
            yield msg
            return
        else:
            if parsed_command is None:
                yield msg
            else:
                yield from self.handleCommand(parsed_command, endpoint)
        finally:
            self.nodeActive()

    def parse_command(self, payload, endpoint):
        if len(payload) < 2:
            raise Exception(f"Short command: {payload !r}")

        cc_code, cmd_code = payload[0:2]
        cmd = None
        cc_enum = CommandClass(cc_code)
        try:
            cc = self.commandClass[endpoint, cc_enum]
        except KeyError:
            # If this is a VERSION.CommandClassReport or WAKE_UP.Notification
            # and we haven't got a version yet, then parse as version 1.
            if (cc_code, cmd_code) not in (
                (CommandClass.VERSION.value, 0x14),
                (CommandClass.WAKE_UP.value, 0x07),
            ):
                return
            cc = getCommandClassVersion(cc_code, 1)
        cmd = cc.commands[cmd_code]
        return cmd.fromBytes(payload)

    def handleCommand(self, cmd, endpoint):
        handler = self.commandHandler.get(
            (cmd.CommandClassCode, cmd.CommandCode)
        )
        if handler is None:
            yield ReceivedCommand(self.__id, endpoint, cmd)
        else:
            try:
                yield from handler(cmd, endpoint)
                return
            except Exception as ex:
                logging.warning(
                    f"Command handler raised exception: { ex !r}"
                    f" (endpoint: { endpoint } cmd: { cmd !r})"
                )

    def versionReportHandler(self, cmd, endpoint):
        reqcc = cmd.requestedCommandClass
        try:
            reqcc = CommandClass(reqcc)
        except ValueError:
            pass
        vers = cmd.commandClassVersion
        self.commandClassVersion[endpoint, reqcc] = vers
        try:
            cc_class = getCommandClassVersion(reqcc, vers)
            self.commandClass[endpoint, reqcc] = cc_class
        except KeyError:
            cc_class = None
        yield NodeUpdate.CommandClass(
            self.__id, endpoint, cc_class, reqcc, vers
        )

    def manufacturerSpecificReportHandler(self, cmd, endpoint):
        if endpoint == 0:
            self.manufacturerInfo = cmd
            yield NodeUpdate.ManufacturerInfo(self.__id, cmd)

    def multiChannelEndpointReportHandler(self, cmd, endpoint):
        self.endPointReport = cmd
        return ()

    def multiChannelCapabilityReportHandler(self, cmd, endpoint):
        yield from self.setCommandClasses(cmd.endPoint, cmd.commandClass)

    def multiChannelCmdEncapHandler(self, cmd, endpoint):
        if cmd.bitAddress:
            to_us = bool(1 & cmd.destinationEndPoint)
        else:
            to_us = cmd.destinationEndPoint == 0

        if not to_us:
            yield ReceivedCommand(self.__id, 0, cmd)
            return

        payload = bytes((cmd.commandClass, cmd.command)) + cmd.parameter
        endpoint = cmd.sourceEndPoint

        try:
            parsed_command = self.parse_command(payload, endpoint)
        except Exception as ex:
            logging.warning(
                "Error parsing MULTI_CHANNEL_CMD_ENCAP payload: "
                f"{ payload !r} node={ self.__id } endpoint={ endpoint } "
                f"exception: { ex !r}"
            )
            yield ReceivedCommand(self.__id, 0, cmd)
            return

        yield from self.handleCommand(parsed_command, endpoint)

    def wakeUpNotificationHandler(self, cmd, endpoint):
        if not self.sendsWakeUpNotifications:
            self.sendsWakeUpNotifications = True
            # insert a bogus item into the commandQueue to make the command
            # dispatcher switch to sendsWakeUpNotifications mode
            self.commandQueue.add(
                CommandTransmission(None, priority=Priority.WAKE_UP)
            )
            self.nodeActive()
        self.wakeUpNotificationEvent.set()
        return (ReceivedCommand(self.__id, endpoint, cmd),)

    async def __commandDispatcherTaskImpl(self):
        while True:
            if self.sendsWakeUpNotifications:
                await self.wakeUpNotificationEvent.wait()
                await self.commandQueue.waitForMessage(0.2)
                if self.commandQueue.hasMessage():
                    cmdtx = self.commandQueue.takeMessage()
                else:
                    for i in 1, 2, 3:
                        if await self.__transmitCommand(b"\x84\x08"):
                            break
                    self.wakeUpNotificationEvent.clear()
                    continue
            else:
                await waitForOne(
                    self.nodeActiveEvent.wait(), timeout=random.gauss(30, 3)
                )
                cmdtx = await self.commandQueue.getMessage()

            if cmdtx.message is None:
                # discard this bogus message
                continue

            cmdtx.transmitting = True

            command = cmdtx.message
            if cmdtx.endpoint > 0:
                multi_channel = self.commandClass.get(
                    (0, CommandClass.MULTI_CHANNEL)
                )
                if multi_channel is None:
                    cmdtx.set_exception(
                        Exception("Node does not support multi channel")
                    )
                    continue
                command = multi_channel.MultiChannelCmdEncap(
                    sourceEndPoint=0,
                    destinationEndPoint=cmdtx.endpoint,
                    bitAddress=False,
                    commandClass=command.CommandClassCode,
                    command=command.CommandCode,
                    parameter=command.toBytes()[2:],
                )

            command = command.toBytes()

            if await self.__transmitCommand(command):
                cmdtx.set_result(None)
            else:
                cmdtx.retransmission += 1
                cmdtx.pauseUntil = time.monotonic() + 5
                cmdtx.transmitting = False
                self.commandQueue.addFirst(cmdtx)

            await asyncio.sleep(abs(random.gauss(0.2, 0.04)))

    async def __transmitCommand(self, command_bytes):
        func_id = await self.__controller._funcIdManager.get()

        if self.noAckCount % 2:
            tx_options = TransmitOption.ACK | TransmitOption.EXPLORE
        else:
            tx_options = TransmitOption.ACK | TransmitOption.AUTO_ROUTE

        try:
            retval = (
                await self.__controller.sendData(
                    nodeId=self.__id,
                    data=command_bytes,
                    txOptions=tx_options,
                    funcId=func_id.value,
                )
            ).retVal
        except Exception as ex:
            retval = False
            logging.warning(
                f"sendData(nodeId={self.__id}) raised exception: { ex !r}"
            )
        if not retval:
            func_id.release()
            return False

        try:
            tx_complete = await asyncio.wait_for(func_id.future, timeout=65)
        except Exception:
            tx_complete = None
        finally:
            func_id.release()

        if tx_complete == TransmitComplete.OK:
            self.noAckCount = 0
            self.nodeActiveEvent.set()
            return True

        if tx_complete == TransmitComplete.NO_ACK:
            self.noAckCount += 1
            if self.noAckCount >= self.noAckCountThreshold:
                self.nodeActiveEvent.clear()

        return False

    async def __nodeInitializationTaskImpl(self):
        wait = 0
        while self.protocolInfo is None:
            try:
                self.protocolInfo = await self.__controller.getNodeProtocolInfo(
                    nodeId=self.__id
                )
            except Exception:
                wait = (wait + 2) * 1.5
                await asyncio.sleep(abs(random.gauss(wait, wait / 5)))
            else:
                self.__controller._receivedMessages.append(
                    NodeUpdate.ProtocolInfo(self.__id, self.protocolInfo)
                )

        wait = 0
        while 0 not in self.commandClassCodes:
            async with self.__controller._requestNodeInfoLock:
                self.nodeActiveEvent.clear()
                try:
                    await self.__controller.requestNodeInfo(nodeId=self.__id)
                except Exception:
                    ...
                await waitForOne(self.nodeActiveEvent.wait(), timeout=2)
            wait = (wait + 4) * 1.5
            await waitForOne(
                self.nodeActiveEvent.wait(),
                timeout=abs(random.gauss(wait, wait / 5)),
            )

        self.__ongoing_tasks = set()
        self.__task_repetition_count = {}
        CommandClassVersionV1 = getCommandClassVersion(CommandClass.VERSION, 1)

        while True:
            if self.sendsWakeUpNotifications:
                await self.wakeUpNotificationEvent.wait()
                await asyncio.sleep(abs(random.gauss(0.05, 0.01)))
            else:
                await asyncio.sleep(abs(random.gauss(5, 1)))

            # Get command class versions for all endpoints we know the
            # supported command classes of
            for endpoint, cc in set(
                (endpoint, cc)
                for endpoint, cc_codes in self.commandClassCodes.items()
                for cc in cc_codes
            ).difference(self.commandClassVersion):
                priority = (
                    0
                    if endpoint != 0
                    else self.__initCCVersionPriority.get(cc, 0)
                )
                self.__addInitTask(
                    f"getCommandClassVersion-{ endpoint }-{ cc }",
                    functools.partial(
                        lambda x: x not in self.commandClassVersion,
                        (endpoint, cc),
                    ),
                    functools.partial(
                        lambda endpoint, cc, priority: self.sendCommand(
                            CommandClassVersionV1.CommandClassGet(
                                requestedCommandClass=cc
                            ),
                            endpoint=endpoint,
                            priority=priority,
                        ),
                        endpoint,
                        cc,
                        priority + Priority.INITALIZATION,
                    ),
                )

            self.__addInitTask(
                "getMultiChannelEndpoints",
                lambda: self.endPointReport is None
                and hasattr(
                    self.commandClass.get((0, CommandClass.MULTI_CHANNEL)),
                    "EndPointGet",
                ),
                lambda: self.sendCommand(
                    self.commandClass[
                        0, CommandClass.MULTI_CHANNEL
                    ].EndPointGet()
                ),
            )

            self.__addInitTask(
                "getManufacturerInfo",
                lambda: self.manufacturerInfo is None
                and hasattr(
                    self.commandClass.get(
                        (0, CommandClass.MANUFACTURER_SPECIFIC)
                    ),
                    "Get",
                ),
                lambda: self.sendCommand(
                    self.commandClass[
                        0, CommandClass.MANUFACTURER_SPECIFIC
                    ].Get()
                ),
            )

            if self.endPointReport is not None:
                for ep in range(
                    1, self.endPointReport.individualEndPoints + 1
                ):
                    self.__addInitTask(
                        f"getMultiChannelEndpointCapabilities-{ ep }",
                        functools.partial(
                            lambda ep: ep
                            <= self.endPointReport.individualEndPoints
                            and ep not in self.commandClassCodes,
                            ep,
                        ),
                        functools.partial(
                            lambda ep: self.sendCommand(
                                self.commandClass[
                                    0, CommandClass.MULTI_CHANNEL
                                ].CapabilityGet(endPoint=ep)
                            ),
                            ep,
                        ),
                    )

            if not self.__ongoing_tasks:
                sleep_time = abs(random.gauss(1800, 360))
                logging.info(
                    f"Node initialization task: node #{ self.__id } - "
                    f"sleeping for { sleep_time } seconds"
                )
                await asyncio.sleep(sleep_time)

    __initCCVersionPriority = {
        CommandClass.MANUFACTURER_SPECIFIC: 2,
        CommandClass.MULTI_CHANNEL: 1,
        CommandClass.VERSION: -1,
        CommandClass.WAKE_UP: -1,
    }

    def __addInitTask(self, key, condition, action):
        if key in self.__ongoing_tasks:
            return
        try:
            condition = bool(condition())
        except Exception:
            condition = False
        if condition:
            count = self.__task_repetition_count.get(key, 0)
            self.__task_repetition_count[key] = count + 1
            self.__ongoing_tasks.add(key)
        else:
            self.__task_repetition_count.pop(key, None)
            return

        async def execute_action():
            try:
                try:
                    await action()
                except asyncio.CancelledError:
                    return
                except Exception:
                    traceback.print_exc()
                delay = 3 * abs(random.gauss(1, 0.2)) * (1.2 ** count)
                await asyncio.sleep(delay)
            finally:
                self.__ongoing_tasks.discard(key)

        logging.info(f"Adding init task { key !r} to node { self.__id }")
        asyncio.create_task(execute_action())
