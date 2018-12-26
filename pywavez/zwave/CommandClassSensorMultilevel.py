import enum

from pywavez.serialization.Serialization import Expr as _Expr, Value as _Value
from pywavez.serialization.ZWaveSerialization import (
    ZWaveSerialization,
    ZWaveCommandClassBase,
)
from pywavez.zwave.Constants import CommandClass

fct = ZWaveSerialization.functionsModule()


class CommandClassSensorMultilevel(ZWaveCommandClassBase):
    code = CommandClass.SENSOR_MULTILEVEL
    name = "SensorMultilevel"

    class SensorType(enum.IntEnum):
        TEMPERATURE = 1
        GENERAL_PURPOSE_VALUE = 2
        LUMINANCE = 3
        POWER = 4
        RELATIVE_HUMIDITY = 5
        VELOCITY = 6
        DIRECTION = 7
        ATMOSPHERIC_PRESSURE = 8
        BAROMETRIC_PRESSURE = 9
        SOLAR_RADIATION = 10
        DEW_POINT = 11
        RAIN_RATE = 12
        TIDE_LEVEL = 13
        WEIGHT = 14
        VOLTAGE = 15
        CURRENT = 16
        CO2_LEVEL = 17
        AIR_FLOW = 18
        TANK_CAPACITY = 19
        DISTANCE = 20
        ANGLE_POSITION = 21
        ROTATION = 22
        WATER_TEMPERATURE = 23
        SOIL_TEMPERATURE = 24
        SEISMIC_INTENSITY = 25
        SEISMIC_MAGNITUDE = 26
        ULTRAVIOLET = 27
        ELECTRICAL_RESISTIVITY = 28
        ELECTRICAL_CONDUCTIVITY = 29
        LOUDNESS = 30
        MOISTURE = 31
        FREQUENCY = 32
        TIME = 33
        TARGET_TEMPERATURE = 34
        PARTICULATE_MATTER_25 = 35
        FORMALDEHYDE_CH2O_LEVEL = 36
        RADON_CONCENTRATION = 37
        METHANE_DENSITY_CH4 = 38
        VOLATILE_ORGANIC_COMPOUND = 39
        CARBON_MONOXIDE_CO_LEVEL = 40
        SOIL_HUMIDITY = 41
        SOIL_REACTIVITY = 42
        SOIL_SALINITY = 43
        HEART_RATE = 44
        BLOOD_PRESSURE = 45
        MUSCLE_MASS = 46
        FAT_MASS = 47
        BONE_MASS = 48
        TOTAL_BODY_WATER_TBW = 49
        BASIC_METABOLIC_RATE_BMR = 50
        BODY_MASS_INDEX_BMI = 51
        ACCELERATION_X_AXIS = 52
        ACCELERATION_Y_AXIS = 53
        ACCELERATION_Z_AXIS = 54
        SMOKE_DENSITY = 55
        WATER_FLOW = 56
        WATER_PRESSURE = 57
        RF_SIGNAL_STRENGTH = 58
        PARTICULATE_MATTER = 59
        RESPIRATORY_RATE = 60
        RELATIVE_MODULATION_LEVEL = 61
        BOILER_WATER_TEMPERATURE = 62
        DOMESTIC_HOT_WATER_TEMPERATURE = 63
        OUTSIDE_TEMPERATURE = 64
        EXHAUST_TEMPERATURE = 65


class CommandClassSensorMultilevelV1(CommandClassSensorMultilevel):
    version = 1

    Get = ZWaveSerialization.createClass(
        "Get", [fct.zwaveCommand(_class=0x31, cmd=0x04)]
    )
    Report = ZWaveSerialization.createClass(
        "Report",
        [
            fct.zwaveCommand(_class=0x31, cmd=0x05),
            fct.uint8(
                field="sensorType",
                enum=CommandClassSensorMultilevel.SensorType,
            ),
            fct.uintbits(
                virtualfield="size",
                mask=0x07,
                shift=0,
                value=_Expr("intsize(sensorValue)"),
            ),
            fct.uintbits(field="scale", prevbyte=True, mask=0x03, shift=3),
            fct.uintbits(field="precision", prevbyte=True, mask=0x07, shift=5),
            fct.int(field="sensorValue", bytes=_Value("size")),
        ],
    )

    commands = {0x04: Get, 0x05: Report}


class CommandClassSensorMultilevelV2(CommandClassSensorMultilevelV1):
    version = 2

    commands = {
        0x04: CommandClassSensorMultilevelV1.Get,
        0x05: CommandClassSensorMultilevelV1.Report,
    }


class CommandClassSensorMultilevelV3(CommandClassSensorMultilevelV2):
    version = 3

    commands = {
        0x04: CommandClassSensorMultilevelV1.Get,
        0x05: CommandClassSensorMultilevelV1.Report,
    }


class CommandClassSensorMultilevelV4(CommandClassSensorMultilevelV3):
    version = 4

    commands = {
        0x04: CommandClassSensorMultilevelV1.Get,
        0x05: CommandClassSensorMultilevelV1.Report,
    }


class CommandClassSensorMultilevelV5(CommandClassSensorMultilevelV4):
    version = 5

    SupportedGetSensor = ZWaveSerialization.createClass(
        "SupportedGetSensor", [fct.zwaveCommand(_class=0x31, cmd=0x01)]
    )
    SupportedSensorReport = ZWaveSerialization.createClass(
        "SupportedSensorReport",
        [
            fct.zwaveCommand(_class=0x31, cmd=0x02),
            fct.bitset(field="bitMask", bytes=None),
        ],
    )
    SupportedGetScale = ZWaveSerialization.createClass(
        "SupportedGetScale",
        [
            fct.zwaveCommand(_class=0x31, cmd=0x03),
            fct.uint8(
                field="sensorType",
                enum=CommandClassSensorMultilevel.SensorType,
            ),
        ],
    )
    Get = ZWaveSerialization.createClass(
        "Get",
        [
            fct.zwaveCommand(_class=0x31, cmd=0x04),
            fct.uint8(
                field="sensorType",
                enum=CommandClassSensorMultilevel.SensorType,
            ),
            fct.uintbits(field="scale", mask=0x03, shift=3),
        ],
    )
    SupportedScaleReport = ZWaveSerialization.createClass(
        "SupportedScaleReport",
        [
            fct.zwaveCommand(_class=0x31, cmd=0x06),
            fct.uint8(
                field="sensorType",
                enum=CommandClassSensorMultilevel.SensorType,
            ),
            fct.uintbits(field="scaleBitMask", mask=0x0F, shift=0),
        ],
    )

    commands = {
        0x01: SupportedGetSensor,
        0x02: SupportedSensorReport,
        0x03: SupportedGetScale,
        0x04: Get,
        0x05: CommandClassSensorMultilevelV1.Report,
        0x06: SupportedScaleReport,
    }


class CommandClassSensorMultilevelV6(CommandClassSensorMultilevelV5):
    version = 6

    commands = {
        0x01: CommandClassSensorMultilevelV5.SupportedGetSensor,
        0x02: CommandClassSensorMultilevelV5.SupportedSensorReport,
        0x03: CommandClassSensorMultilevelV5.SupportedGetScale,
        0x04: CommandClassSensorMultilevelV5.Get,
        0x05: CommandClassSensorMultilevelV1.Report,
        0x06: CommandClassSensorMultilevelV5.SupportedScaleReport,
    }


class CommandClassSensorMultilevelV7(CommandClassSensorMultilevelV6):
    version = 7

    commands = {
        0x01: CommandClassSensorMultilevelV5.SupportedGetSensor,
        0x02: CommandClassSensorMultilevelV5.SupportedSensorReport,
        0x03: CommandClassSensorMultilevelV5.SupportedGetScale,
        0x04: CommandClassSensorMultilevelV5.Get,
        0x05: CommandClassSensorMultilevelV1.Report,
        0x06: CommandClassSensorMultilevelV5.SupportedScaleReport,
    }


class CommandClassSensorMultilevelV8(CommandClassSensorMultilevelV7):
    version = 8

    commands = {
        0x01: CommandClassSensorMultilevelV5.SupportedGetSensor,
        0x02: CommandClassSensorMultilevelV5.SupportedSensorReport,
        0x03: CommandClassSensorMultilevelV5.SupportedGetScale,
        0x04: CommandClassSensorMultilevelV5.Get,
        0x05: CommandClassSensorMultilevelV1.Report,
        0x06: CommandClassSensorMultilevelV5.SupportedScaleReport,
    }


class CommandClassSensorMultilevelV9(CommandClassSensorMultilevelV8):
    version = 9

    commands = {
        0x01: CommandClassSensorMultilevelV5.SupportedGetSensor,
        0x02: CommandClassSensorMultilevelV5.SupportedSensorReport,
        0x03: CommandClassSensorMultilevelV5.SupportedGetScale,
        0x04: CommandClassSensorMultilevelV5.Get,
        0x05: CommandClassSensorMultilevelV1.Report,
        0x06: CommandClassSensorMultilevelV5.SupportedScaleReport,
    }


class CommandClassSensorMultilevelV10(CommandClassSensorMultilevelV9):
    version = 10

    commands = {
        0x01: CommandClassSensorMultilevelV5.SupportedGetSensor,
        0x02: CommandClassSensorMultilevelV5.SupportedSensorReport,
        0x03: CommandClassSensorMultilevelV5.SupportedGetScale,
        0x04: CommandClassSensorMultilevelV5.Get,
        0x05: CommandClassSensorMultilevelV1.Report,
        0x06: CommandClassSensorMultilevelV5.SupportedScaleReport,
    }


class CommandClassSensorMultilevelV11(CommandClassSensorMultilevelV10):
    version = 11

    commands = {
        0x01: CommandClassSensorMultilevelV5.SupportedGetSensor,
        0x02: CommandClassSensorMultilevelV5.SupportedSensorReport,
        0x03: CommandClassSensorMultilevelV5.SupportedGetScale,
        0x04: CommandClassSensorMultilevelV5.Get,
        0x05: CommandClassSensorMultilevelV1.Report,
        0x06: CommandClassSensorMultilevelV5.SupportedScaleReport,
    }


CommandClassSensorMultilevel.versions = {
    1: CommandClassSensorMultilevelV1,
    2: CommandClassSensorMultilevelV2,
    3: CommandClassSensorMultilevelV3,
    4: CommandClassSensorMultilevelV4,
    5: CommandClassSensorMultilevelV5,
    6: CommandClassSensorMultilevelV6,
    7: CommandClassSensorMultilevelV7,
    8: CommandClassSensorMultilevelV8,
    9: CommandClassSensorMultilevelV9,
    10: CommandClassSensorMultilevelV10,
    11: CommandClassSensorMultilevelV11,
}
