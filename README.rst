pywavez
=======

pywavez is a native Python3, asynchronous implementation of the ZWave protocol.

To create a Controller object:

>>> from pywavez import Controller
>>> c = await Controller("/dev/ttyACM0")

This will execute a basic initialisation procedure. The returned ``Controller``
object can be used to communicate with ZWave components.

Documentation: to be written...
