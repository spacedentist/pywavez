import collections

ReceivedCommand = collections.namedtuple(
    "ReceivedCommand", ("nodeId", "endpoint", "command")
)
