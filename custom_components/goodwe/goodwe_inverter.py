"""The GoodWe inverter data retrieval module"""
import asyncio
import logging
from enum import Enum
from typing import Any, Callable, Dict, NamedTuple, Optional, Tuple

_LOGGER = logging.getLogger(__name__)

_WORK_MODES_ET: Dict[int, str] = {
    0: "Wait Mode",
    1: "Normal(On-Grid)",
    2: "Normal(Off-Grid)",
    3: "Fault Mode",
    4: "Flash Mode",
    5: "Check Mode",
}

_BATTERY_MODES_ET: Dict[int, str] = {
    0: "No battery or battery disconnected",
    1: "Spare",
    2: "Discharge",
    3: "Charge",
    4: "To be charged",
    5: "To be discharged",
}

_PV_MODES: Dict[int, str] = {
    0: "Disconnect the inverter and PV panels",
    1: "No power output PV",
    2: "Working,PV has a power output",
}

_LOAD_MODES: Dict[int, str] = {
    0: "The inverter is connected to a load",
    1: "Inverter and the load is disconnected",
}

_WORK_MODES: Dict[int, str] = {
    0: "Wait for the conditions to generate electricity",
    1: "The inverter is generating",
    2: "System abnormalities, while stopping power",
    3: "System is severely abnormal, 20 seconds after the restart",
}

_ENERGY_MODES: Dict[int, str] = {
    0: "Check Mode",
    1: "Wait Mode",
    2: "Normal(On-Grid)",
    4: "Normal(Off-Grid)",
    8: "Flash Mode",
    16: "Fault Mode",
    32: "Battery Standby",
    64: "Battery Charging",
    128: "Battery Discharging",
}

_GRID_MODES: Dict[int, str] = {
    0: "Inverter neither send power to grid,nor get power from grid",
    1: "Inverter sends power to grid",
    2: "Inverter gets power from grid",
}

_SAFETY_COUNTRIES_ET: Dict[int, str] = {
    0: "Italy",
    1: "Czech",
    2: "Germany",
    3: "Spain",
    4: "Greece",
    5: "Denmark",
    6: "Belguim",
    7: "Romania",
    8: "G98",
    9: "Australia",
    10: "France",
    11: "China",
    13: "Poland",
    14: "South Africa",
    15: "AustraliaL",
    16: "Brazil",
    17: "Thailand MEA",
    18: "Thailand PEA",
    19: "Mauritius",
    20: "Holland",
    21: "Northern Ireland",
    22: "China Higher",
    23: "French 50Hz",
    24: "French 60Hz",
    25: "Australia Ergon",
    26: "Australia Energex",
    27: "Holland 16/20A",
    28: "Korea",
    29: "China Station",
    30: "Austria",
    31: "India",
    32: "50Hz Grid Default",
    33: "Warehouse",
    34: "Philippines",
    35: "Ireland",
    36: "Taiwan",
    37: "Bulgaria",
    38: "Barbados",
    39: "China Highest",
    40: "G99",
    41: "Sweden",
    42: "Chile",
    43: "Brazil LV",
    44: "NewZealand",
    45: "IEEE1547 208VAC",
    46: "IEEE1547 220VAC",
    47: "IEEE1547 240VAC",
    48: "60Hz LV Default",
    49: "50Hz LV Default",
    50: "AU_WAPN",
    51: "AU_MicroGrid",
    52: "JP_50Hz",
    53: "JP_60Hz",
    54: "India Higher",
    55: "DEWA LV",
    56: "DEWA MV",
    57: "Slovakia",
    58: "GreenGrid",
    59: "Hungary",
    60: "Sri Lanka",
    61: "Spain Islands",
    62: "Ergon30K",
    63: "Energex30K",
    64: "IEEE1547 230/400V",
    65: "IEC61727 60Hz",
    66: "Switzerland",
    67: "CEI-016",
    68: "AU_Horizon",
    69: "Cyprus",
    70: "AU_SAPN",
    71: "AU_Ausgrid",
    72: "AU_Essential",
    73: "AU_Pwcore&CitiPW",
    74: "Hong Kong",
    75: "Poland MV",
    76: "Holland MV",
    77: "Sweden MV",
    78: "VDE4110",
    96: "cUSA_208VacDefault",
    97: "cUSA_240VacDefault",
    98: "cUSA_208VacCA_SCE",
    99: "cUSA_240VacCA_SCE",
    100: "cUSA_208VacCA_SDGE",
    101: "cUSA_240VacCA_SDGE",
    102: "cUSA_208VacCA_PGE",
    103: "cUSA_240VacCA_PGE",
    104: "cUSA_208VacHECO_14HO",
    105: "cUSA_240VacHECO_14HO0x69",
    106: "cUSA_208VacHECO_14HM",
    107: "cUSA_240VacHECO_14HM",
}


def _read_voltage(data: bytes, offset: int) -> float:
    value = (data[offset] << 8) | data[offset + 1]
    return float(value) / 10


def _read_current(data: bytes, offset: int) -> float:
    value = (data[offset] << 8) | data[offset + 1]
    if value > 32768:
        value = value - 65536
    return float(value) / 10


def _read_power(data: bytes, offset: int) -> int:
    value = (
        (data[offset] << 24)
        | (data[offset + 1] << 16)
        | (data[offset + 2] << 8)
        | data[offset + 3]
    )
    if value > 32768:
        value = value - 65536
    return value


def _read_power2(data: bytes, offset: int) -> int:
    value = (data[offset] << 8) | data[offset + 1]
    if value > 32768:
        value = value - 65536
    return value


def _read_power_k(data: bytes, offset: int) -> float:
    value = (
        (data[offset] << 24)
        | (data[offset + 1] << 16)
        | (data[offset + 2] << 8)
        | data[offset + 3]
    )
    if value > 32768:
        value = value - 65536
    return float(value) / 10


def _read_power_k2(data: bytes, offset: int) -> float:
    value = (data[offset] << 8) | data[offset + 1]
    if value > 32768:
        value = value - 65536
    return float(value) / 10


def _read_freq(data: bytes, offset: int) -> float:
    value = (data[offset] << 8) | data[offset + 1]
    return float(value) / 100


def _read_temp(data: bytes, offset: int) -> float:
    value = (data[offset] << 8) | data[offset + 1]
    return float(value) / 10


def _read_byte(data: bytes, offset: int) -> int:
    return data[offset]


def _read_bytes2(data: bytes, offset: int) -> int:
    return (data[offset] << 8) | data[offset + 1]


def _read_bytes4(data: bytes, offset: int) -> int:
    return (
        (data[offset + 0] << 24)
        | (data[offset + 1] << 16)
        | (data[offset + 2] << 8)
        | data[offset + 3]
    )


def _read_grid_mode(data: bytes, offset: int) -> int:
    value = _read_bytes4(data, offset)
    if value > 32768:
        value -= 65535
    if value < -90:
        return 2
    elif value >= 90:
        return 1
    else:
        return 0


def _read_battery_mode(data: bytes, offset: int) -> Optional[str]:
    return _BATTERY_MODES_ET.get(_read_bytes2(data, offset))


def _read_safety_country(data: bytes, offset: int) -> Optional[str]:
    return _SAFETY_COUNTRIES_ET.get(_read_bytes2(data, offset))


def _read_work_mode(data: bytes, offset: int) -> Optional[str]:
    return _WORK_MODES_ET.get(_read_bytes2(data, offset))


def _read_pv_mode1(data: bytes, offset: int) -> Optional[str]:
    return _PV_MODES.get(_read_byte(data, offset))


def _read_work_mode1(data: bytes, offset: int) -> Optional[str]:
    return _WORK_MODES.get(_read_byte(data, offset))


def _read_load_mode1(data: bytes, offset: int) -> Optional[str]:
    return _LOAD_MODES.get(_read_byte(data, offset))


def _read_energy_mode1(data: bytes, offset: int) -> Optional[str]:
    return _ENERGY_MODES.get(_read_byte(data, offset))


def _read_battery_mode1(data: bytes, offset: int) -> Optional[str]:
    return _BATTERY_MODES_ET.get(_read_byte(data, offset))


class SensorKind(Enum):
    """Enumeration of sensor kinds"""

    pv = 1
    ac = 2
    ups = 3
    bat = 4


class InverterInfo(NamedTuple):
    """Object representing inverter model and version info"""

    model_name: str
    serial_number: str
    software_version: str


class Sensor(NamedTuple):
    """Definition of inverter sensor and its attributes"""

    id: str
    offset: int
    getter: Callable[[bytes, int], Any]
    unit: str
    name: str
    kind: Optional[SensorKind]


class _UdpInverterProtocol(asyncio.DatagramProtocol):
    def __init__(
        self,
        request: bytes,
        response_lenghts: Tuple[int, ...],
        on_response_received: asyncio.futures.Future,
        timeout: int = 2,
    ):
        self.request: bytes = request
        self.response_lenghts: Tuple[int, ...] = response_lenghts
        self.on_response_received: asyncio.futures.Future = on_response_received
        self.transport: asyncio.transports.DatagramTransport
        self.timeout: int = timeout
        self.retry_nr: int = 1

    def connection_made(self, transport: asyncio.transports.DatagramTransport):
        self.transport = transport
        _LOGGER.debug("Send: '%s'", self.request.hex())
        self.transport.sendto(self.request)
        asyncio.get_event_loop().call_later(self.timeout, self._timeout_heartbeat)

    def connection_lost(self, exc: Exception):
        if exc is not None:
            _LOGGER.debug("Socket closed with error: '%s'", exc)
        if not self.on_response_received.done():
            self.on_response_received.cancel()

    def datagram_received(self, data: bytes, addr: Tuple[str, int]):
        _LOGGER.debug("Received: '%s'", data.hex())
        if len(data) in self.response_lenghts:
            self.on_response_received.set_result(data)
            self.transport.close()
        else:
            _LOGGER.debug(
                "Unexpected response length: expected %s, received: %d",
                self.response_lenghts,
                len(data),
            )
            self.retry_nr += 1
            self.connection_made(self.transport)

    def error_received(self, exc: Exception):
        _LOGGER.debug("Received error: '%s'", exc)

    def _timeout_heartbeat(self):
        if self.on_response_received.done():
            self.transport.close()
        elif self.retry_nr < 4:
            _LOGGER.debug("Timeout #%d", self.retry_nr)
            self.retry_nr += 1
            self.connection_made(self.transport)
        else:
            _LOGGER.debug("Timeout #%d, closing socket", self.retry_nr)
            self.transport.close()


async def _read_from_socket(
    command_spec: Tuple[bytes, Tuple[int, ...]], inverter_address: Tuple[str, int]
) -> bytes:
    loop = asyncio.get_running_loop()
    on_response_received = loop.create_future()
    transport, _ = await loop.create_datagram_endpoint(
        lambda: _UdpInverterProtocol(
            command_spec[0], command_spec[1], on_response_received
        ),
        remote_addr=inverter_address,
    )
    try:
        await on_response_received
        result = on_response_received.result()
        if result is not None:
            return result
        else:
            raise RuntimeError(
                "No response received to '" + command_spec[0].hex() + "' request"
            )
    finally:
        transport.close()


class Inverter:
    """Base wrapper around Inverter UDP protocol"""

    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.model_name = None
        self.serial_number = None
        self.software_version = None

    async def get_model(self) -> InverterInfo:
        """Request the model information from the inverter"""
        data = await self._make_model_request(self.host, self.port)
        self.model_name = data.model_name
        self.serial_number = data.serial_number
        self.software_version = data.software_version
        return data

    async def get_data(self) -> Dict[str, Any]:
        """Request the runtime data from the inverter"""
        return await self._make_request(self.host, self.port)

    @classmethod
    async def _make_model_request(cls, host, port) -> InverterInfo:
        """
        Return instance of 'InverterInfo'
        Raise exception if unable to get version
        """
        raise NotImplementedError()

    @classmethod
    async def _make_request(cls, host, port) -> Dict[str, Any]:
        """
        Return dictionary of sensor names and their values
        Raise exception if unable to get data
        """
        raise NotImplementedError()

    @classmethod
    def sensors(cls) -> Tuple[Sensor, ...]:
        """
        Return tuple of sensor definitions
        """
        raise NotImplementedError()

    @staticmethod
    def _map_response(resp_data: bytes, sensors: Tuple[Sensor, ...]) -> Dict[str, Any]:
        """Process the response data and return dictionary with runtime values"""
        return {
            sensor_id: fn(resp_data, offset)
            for (sensor_id, offset, fn, _, name, _) in sensors
        }


async def discover(host, port=8899) -> Inverter:
    """Contact the inverter at the specified value and answer appropriare Inverter instance

    Raise exception if unable to contact or recognise supported inverter
    """
    failures = []
    for inverter in REGISTRY:
        i = inverter(host, port)
        try:
            _LOGGER.debug("Probing %s inverter at %s:%s", inverter.__name__, host, port)
            response = await i.get_model()
            _LOGGER.debug(
                "Detected %s protocol inverter %s, S/N:%s",
                inverter.__name__,
                response.model_name,
                response.serial_number,
            )
            return i
        except asyncio.exceptions.CancelledError as ex:
            failures.append(ex)
        except Exception as ex:
            failures.append(ex)
    msg = (
        "Unable to connect to the inverter at "
        f"host={host} port={port}, or your inverter is not supported yet.\n"
        f"Failures={str(failures)}"
    )
    raise RuntimeError(msg)


class ET(Inverter):
    """Class representing inverter of ET family"""

    # (request data including checksum, expected response lengths)
    _READ_DEVICE_VERSION_INFO: Tuple[bytes, Tuple[int, ...]] = (
        bytes((0xF7, 0x03, 0x88, 0xB8, 0x00, 0x21, 0x3A, 0xC1)),
        (73,),
    )
    _READ_DEVICE_RUNNING_DATA1: Tuple[bytes, Tuple[int, ...]] = (
        bytes((0xF7, 0x03, 0x89, 0x1C, 0x00, 0x7D, 0x7A, 0xE7)),
        (257,),
    )
    _READ_BATTERY_INFO: Tuple[bytes, Tuple[int, ...]] = (
        bytes((0xF7, 0x03, 0x90, 0x88, 0x00, 0x0B, 0xBD, 0xB1)),
        (29,),
    )

    __sensors: Tuple[Sensor, ...] = (
        Sensor("vpv1", 6, _read_voltage, "V", "PV1 Voltage", SensorKind.pv),
        Sensor("ipv1", 8, _read_current, "A", "PV1 Current", SensorKind.pv),
        Sensor("ppv1", 10, _read_power, "W", "PV1 Power", SensorKind.pv),
        Sensor("vpv2", 14, _read_voltage, "V", "PV2 Voltage", SensorKind.pv),
        Sensor("ipv2", 16, _read_current, "A", "PV2 Current", SensorKind.pv),
        Sensor("ppv2", 18, _read_power, "W", "PV2 Power", SensorKind.pv),
        # Sensor("vpv3", 22, _read_voltage, "V", "PV3 Voltage", SensorKind.pv),
        # Sensor("ipv3", 24, _read_current, "A", "PV3 Current", SensorKind.pv),
        # Sensor("ppv3", 26, _read_power, "W", "PV3 Power", SensorKind.pv),
        # Sensor("vpv4", 30, _read_voltage, "V", "PV4 Voltage", SensorKind.pv),
        # Sensor("ipv4", 32, _read_current, "A", "PV4 Current", SensorKind.pv),
        # Sensor("ppv4", 34, _read_power, "W", "PV4 Power", SensorKind.pv),
        # ppv1 + ppv2 + ppv3 + ppv4
        Sensor(
            "ppv",
            0,
            lambda data, _: _read_power(data, 10) + _read_power(data, 18),
            "W",
            "PV Power",
            SensorKind.pv,
        ),
        Sensor("xx38", 38, _read_bytes2, "", "Unknown sensor@38", None),
        Sensor("xx40", 40, _read_bytes2, "", "Unknown sensor@40", None),
        Sensor("vgrid", 42, _read_voltage, "V", "On-grid 1 Voltage", SensorKind.ac),
        Sensor("igrid", 44, _read_current, "A", "On-grid Current", SensorKind.ac),
        Sensor("fgrid", 46, _read_freq, "Hz", "On-grid Frequency", SensorKind.ac),
        Sensor("pgrid", 48, _read_power, "W", "On-grid Power", SensorKind.ac),
        Sensor("vgrid2", 52, _read_voltage, "V", "On-grid2 Voltage", SensorKind.ac),
        Sensor("igrid2", 54, _read_current, "A", "On-grid2 Current", SensorKind.ac),
        Sensor("fgrid2", 56, _read_freq, "Hz", "On-grid2 Frequency", SensorKind.ac),
        Sensor("pgrid2", 58, _read_power, "W", "On-grid2 Power", SensorKind.ac),
        Sensor("vgrid3", 62, _read_voltage, "V", "On-grid3 Voltage", SensorKind.ac),
        Sensor("igrid3", 64, _read_current, "A", "On-grid3 Current", SensorKind.ac),
        Sensor("fgrid3", 66, _read_freq, "Hz", "On-grid3 Frequency", SensorKind.ac),
        Sensor("pgrid3", 68, _read_power, "W", "On-grid3 Power", SensorKind.ac),
        Sensor("xx72", 72, _read_bytes2, "", "Unknown sensor@72", None),
        Sensor(
            "total_inverter_power", 74, _read_power, "W", "Total Power", SensorKind.ac
        ),
        Sensor("active_power", 78, _read_power, "W", "Active Power", SensorKind.ac),
        Sensor("grid_in_out", 78, _read_grid_mode, "", "On-grid Mode", SensorKind.ac),
        Sensor(
            "grid_in_out_label",
            0,
            lambda data, _: _GRID_MODES.get(_read_grid_mode(data, 78)),
            "",
            "On-grid Mode",
            SensorKind.ac,
        ),
        Sensor("xx82", 82, _read_bytes2, "", "Unknown sensor@82", None),
        Sensor("xx84", 84, _read_bytes2, "", "Unknown sensor@84", None),
        Sensor("xx86", 86, _read_bytes2, "", "Unknown sensor@86", None),
        Sensor("backup_v1", 90, _read_voltage, "V", "Back-up1 Voltage", SensorKind.ups),
        Sensor("backup_i1", 92, _read_current, "A", "Back-up1 Current", SensorKind.ups),
        Sensor("backup_f1", 94, _read_freq, "Hz", "Back-up1 Frequency", SensorKind.ups),
        Sensor("xx96", 96, _read_bytes2, "", "Unknown sensor@96", None),
        Sensor("backup_p1", 98, _read_power, "W", "Back-up1 Power", SensorKind.ups),
        Sensor(
            "backup_v2", 102, _read_voltage, "V", "Back-up2 Voltage", SensorKind.ups
        ),
        Sensor(
            "backup_i2", 104, _read_current, "A", "Back-up2 Current", SensorKind.ups
        ),
        Sensor(
            "backup_f2", 106, _read_freq, "Hz", "Back-up2 Frequency", SensorKind.ups
        ),
        Sensor("xx108", 108, _read_bytes2, "", "Unknown sensor@108", None),
        Sensor("backup_p2", 110, _read_power, "W", "Back-up2 Power", SensorKind.ups),
        Sensor(
            "backup_v3", 114, _read_voltage, "V", "Back-up3 Voltage", SensorKind.ups
        ),
        Sensor(
            "backup_i3", 116, _read_current, "A", "Back-up3 Current", SensorKind.ups
        ),
        Sensor(
            "backup_f3", 118, _read_freq, "Hz", "Back-up3 Frequency", SensorKind.ups
        ),
        Sensor("xx120", 120, _read_bytes2, "", "Unknown sensor@120", None),
        Sensor("backup_p3", 122, _read_power, "W", "Back-up3 Power", SensorKind.ups),
        Sensor("load_p1", 126, _read_power, "W", "Load 1", SensorKind.ac),
        Sensor("load_p2", 130, _read_power, "W", "Load 2", SensorKind.ac),
        Sensor("load_p3", 134, _read_power, "W", "Load 3", SensorKind.ac),
        # load_p1 + load_p2 + load_p3
        Sensor(
            "load_ptotal",
            0,
            lambda data, _: _read_power(data, 126)
            + _read_power(data, 130)
            + _read_power(data, 134),
            "W",
            "Load Total",
            SensorKind.ac,
        ),
        Sensor("backup_ptotal", 138, _read_power, "W", "Back-up Power", SensorKind.ups),
        Sensor("pload", 142, _read_power, "W", "Load", SensorKind.ac),
        Sensor("xx146", 146, _read_bytes2, "", "Unknown sensor@146", None),
        Sensor(
            "temperature2",
            148,
            _read_temp,
            "C",
            "Inverter Temperature 2",
            SensorKind.ac,
        ),
        Sensor("xx150", 150, _read_bytes2, "", "Unknown sensor@150", None),
        Sensor(
            "temperature", 152, _read_temp, "C", "Inverter Temperature", SensorKind.ac
        ),
        Sensor("xx154", 154, _read_bytes2, "", "Unknown sensor@154", None),
        Sensor("xx156", 156, _read_bytes2, "", "Unknown sensor@156", None),
        Sensor("xx158", 158, _read_bytes2, "", "Unknown sensor@158", None),
        Sensor("vbattery1", 160, _read_voltage, "V", "Battery Voltage", SensorKind.bat),
        Sensor("ibattery1", 162, _read_current, "A", "Battery Current", SensorKind.bat),
        # round(vbattery1 * ibattery1),
        Sensor(
            "pbattery1",
            0,
            lambda data, _: round(_read_voltage(data, 160) * _read_current(data, 162)),
            "W",
            "Battery Power",
            SensorKind.bat,
        ),
        Sensor("battery_mode", 168, _read_bytes2, "", "Battery Mode", SensorKind.bat),
        Sensor(
            "battery_mode_label",
            168,
            _read_battery_mode,
            "",
            "Battery Mode",
            SensorKind.bat,
        ),
        Sensor("xx170", 170, _read_bytes2, "", "Unknown sensor@170", None),
        Sensor("safety_country", 172, _read_bytes2, "", "Safety Country", None),
        Sensor(
            "safety_country_label",
            172,
            _read_safety_country,
            "",
            "Safety Country",
            None,
        ),
        Sensor("work_mode", 174, _read_bytes2, "", "Work Mode", None),
        Sensor("work_mode_label", 174, _read_work_mode, "", "Work Mode", None),
        Sensor("xx176", 176, _read_bytes2, "", "Unknown sensor@176", None),
        Sensor("strwork_mode", 178, _read_bytes4, "", "Error Codes", None),
        Sensor("strwork_mode_label", 178, _read_bytes4, "", "Error Codes", None),
        Sensor("e_total", 182, _read_power_k, "kWh", "Total PV Generation", None),
        Sensor("e_day", 186, _read_power_k, "kWh", "Today's PV Generation", None),
        Sensor("xx190", 190, _read_bytes2, "", "Unknown sensor@190", None),
        Sensor("xx192", 192, _read_bytes2, "", "Unknown sensor@192", None),
        Sensor("xx194", 194, _read_bytes2, "", "Unknown sensor@194", None),
        Sensor("xx196", 196, _read_bytes2, "", "Unknown sensor@196", None),
        Sensor("xx198", 198, _read_bytes2, "", "Unknown sensor@198", None),
        Sensor("diagnose_result", 240, _read_bytes4, "", "Diag Status", None),
        # ppv1 + ppv2 + pbattery - active_power
        Sensor(
            "house_consumption",
            0,
            lambda data, _: _read_power(data, 10)
            + _read_power(data, 18)
            + round(_read_voltage(data, 160) * _read_current(data, 162))
            - _read_power(data, 78),
            "W",
            "House Comsumption",
            None,
        ),
    )

    __sensors_battery: Tuple[Sensor, ...] = (
        Sensor("battery_bms", 0, _read_bytes2, "", "Battery BMS", SensorKind.bat),
        Sensor("battery_index", 2, _read_bytes2, "", "Battery Index", SensorKind.bat),
        Sensor(
            "battery_temperature",
            6,
            _read_temp,
            "C",
            "Battery Temperature",
            SensorKind.bat,
        ),
        Sensor(
            "battery_charge_limit",
            8,
            _read_bytes2,
            "A",
            "Battery Charge Limit",
            SensorKind.bat,
        ),
        Sensor(
            "battery_discharge_limit",
            10,
            _read_bytes2,
            "A",
            "Battery Discharge Limit",
            SensorKind.bat,
        ),
        Sensor(
            "battery_status", 12, _read_bytes2, "", "Battery Status", SensorKind.bat
        ),
        Sensor(
            "battery_soc",
            14,
            _read_bytes2,
            "%",
            "Battery State of Charge",
            SensorKind.bat,
        ),
        Sensor(
            "battery_soh",
            16,
            _read_bytes2,
            "%",
            "Battery State of Health",
            SensorKind.bat,
        ),
        Sensor(
            "battery_warning", 20, _read_bytes2, "", "Battery Warning", SensorKind.bat
        ),
    )

    @classmethod
    async def _make_model_request(cls, host: str, port: int) -> InverterInfo:
        response = await _read_from_socket(cls._READ_DEVICE_VERSION_INFO, (host, port))
        response = response[5:-2]
        return InverterInfo(
            model_name=response[22:32].decode("utf-8").rstrip(),
            serial_number=response[6:22].decode("utf-8"),
            software_version=response[54:66].decode("utf-8"),
        )

    @classmethod
    async def _make_request(cls, host: str, port: int) -> Dict[str, Any]:
        raw_data = await _read_from_socket(cls._READ_DEVICE_RUNNING_DATA1, (host, port))
        data = cls._map_response(raw_data[5:-2], cls.__sensors)
        raw_data = await _read_from_socket(cls._READ_BATTERY_INFO, (host, port))
        data.update(cls._map_response(raw_data[5:-2], cls.__sensors_battery))
        return data

    @classmethod
    def sensors(cls) -> Tuple[Sensor, ...]:
        return cls.__sensors + cls.__sensors_battery


class ES(Inverter):
    """Class representing inverter of ES/EM family"""

    # (request data including checksum, expected response lengths)
    _READ_DEVICE_VERSION_INFO: Tuple[bytes, Tuple[int, ...]] = (
        bytes((0xAA, 0x55, 0xC0, 0x7F, 0x01, 0x02, 0x00, 0x02, 0x41)),
        (85, 86),
    )
    _READ_DEVICE_RUNNING_DATA: Tuple[bytes, Tuple[int, ...]] = (
        bytes((0xAA, 0x55, 0xC0, 0x7F, 0x01, 0x06, 0x00, 0x02, 0x45)),
        (142, 149),
    )

    __sensors: Tuple[Sensor, ...] = (
        Sensor("vpv1", 0, _read_voltage, "V", "PV1 Voltage", SensorKind.pv),
        Sensor("ipv1", 2, _read_current, "A", "PV1 Current", SensorKind.pv),
        Sensor(
            "ppv1",
            0,
            lambda data, _: round(_read_voltage(data, 0) * _read_current(data, 2)),
            "W",
            "PV1 Power",
            SensorKind.pv,
        ),
        Sensor("pv1_mode", 4, _read_byte, "", "PV1 Mode", SensorKind.pv),
        Sensor("pv1_mode_label", 4, _read_pv_mode1, "", "PV1 Mode", SensorKind.pv),
        Sensor("vpv2", 5, _read_voltage, "V", "PV2 Voltage", SensorKind.pv),
        Sensor("ipv2", 7, _read_current, "A", "PV2 Current", SensorKind.pv),
        Sensor(
            "ppv2",
            0,
            lambda data, _: round(_read_voltage(data, 5) * _read_current(data, 7)),
            "W",
            "PV2 Power",
            SensorKind.pv,
        ),
        Sensor("pv2_mode", 9, _read_byte, "", "PV2 Mode", SensorKind.pv),
        Sensor("pv2_mode_label", 9, _read_pv_mode1, "", "PV2 Mode", SensorKind.pv),
        Sensor(
            "ppv",
            0,
            lambda data, _: round(_read_voltage(data, 0) * _read_current(data, 2))
            + round(_read_voltage(data, 5) * _read_current(data, 7)),
            "W",
            "PV Power",
            SensorKind.pv,
        ),
        Sensor("vbattery1", 10, _read_voltage, "V", "Battery Voltage", SensorKind.bat),
        # Sensor("vbattery2", 12, _read_voltage, "V", "Battery Voltage 2", SensorKind.bat),
        # Sensor("vbattery3", 14, _read_voltage, "V", "Battery Voltage 3", SensorKind.bat),
        Sensor(
            "battery_temperature",
            16,
            _read_temp,
            "C",
            "Battery Temperature",
            SensorKind.bat,
        ),
        Sensor("ibattery1", 18, _read_current, "A", "Battery Current", SensorKind.bat),
        # round(vbattery1 * ibattery1),
        Sensor(
            "pbattery1",
            0,
            lambda data, _: round(_read_voltage(data, 10) * _read_current(data, 18)),
            "W",
            "Battery Power",
            SensorKind.bat,
        ),
        Sensor(
            "battery_charge_limit",
            20,
            _read_bytes2,
            "A",
            "Battery Charge Limit",
            SensorKind.bat,
        ),
        Sensor(
            "battery_discharge_limit",
            22,
            _read_bytes2,
            "A",
            "Battery Discharge Limit",
            SensorKind.bat,
        ),
        Sensor(
            "battery_status", 24, _read_bytes2, "", "Battery Status", SensorKind.bat
        ),
        Sensor(
            "battery_soc",
            26,
            _read_byte,
            "%",
            "Battery State of Charge",
            SensorKind.bat,
        ),
        # Sensor("cbattery2", 27, _read_byte, "%", "Battery State of Charge 2", SensorKind.bat),
        # Sensor("cbattery3", 28, _read_byte, "%", "Battery State of Charge 3", SensorKind.bat),
        Sensor(
            "battery_soh",
            29,
            _read_byte,
            "%",
            "Battery State of Health",
            SensorKind.bat,
        ),
        Sensor("battery_mode", 30, _read_byte, "", "Battery Mode", SensorKind.bat),
        Sensor(
            "battery_mode_label",
            30,
            _read_battery_mode1,
            "",
            "Battery Mode",
            SensorKind.bat,
        ),
        Sensor(
            "battery_warning", 31, _read_bytes2, "", "Battery Warning", SensorKind.bat
        ),
        Sensor("meter_status", 33, _read_byte, "", "Meter status", SensorKind.ac),
        Sensor("vgrid", 34, _read_voltage, "V", "On-grid Voltage", SensorKind.ac),
        Sensor("igrid", 36, _read_current, "A", "On-grid Current", SensorKind.ac),
        Sensor(
            "pgrid", 38, _read_power2, "W", "On-grid Power (EzMeter)", SensorKind.ac
        ),
        Sensor("fgrid", 40, _read_freq, "Hz", "On-grid Frequency", SensorKind.ac),
        Sensor("grid_mode", 42, _read_byte, "", "Work Mode", None),
        Sensor("grid_mode_label", 42, _read_work_mode1, "", "Work Mode", None),
        Sensor("vload", 43, _read_voltage, "V", "Back-up Voltage", SensorKind.ups),
        Sensor("iload", 45, _read_current, "A", "Back-up Current", SensorKind.ups),
        Sensor("pload", 47, _read_power2, "W", "On-grid Power", SensorKind.ups),
        Sensor("fload", 49, _read_freq, "Hz", "Back-up Frequency", SensorKind.ups),
        Sensor("load_mode", 51, _read_byte, "", "Load Mode", None),
        Sensor("load_mode_label", 51, _read_load_mode1, "", "Load Mode", None),
        Sensor("work_mode", 52, _read_byte, "", "Energy Mode", None),
        Sensor("work_mode_label", 52, _read_energy_mode1, "", "Energy Mode", None),
        Sensor("temperature", 53, _read_temp, "C", "Inverter Temperature", None),
        Sensor("error_codes", 55, _read_bytes4, "", "Error Codes", None),
        Sensor("e_total", 59, _read_power_k, "kWh", "Total PV Generation", None),
        Sensor("h_total", 63, _read_bytes4, "", "Hours Total", None),
        Sensor("e_day", 67, _read_power_k2, "kWh", "Today's PV Generation", None),
        Sensor(
            "e_load_day", 69, _read_power_k2, "kWh", "Today's Load Consumption", None
        ),
        Sensor("e_load_total", 71, _read_power_k, "kW", "Total Load", None),
        Sensor("total_power", 75, _read_power2, "W", "Total Power", None),
        # Effective work mode 77
        # Effective relay control 78-79
        Sensor("grid_in_out", 80, _read_byte, "", "On-grid Mode", SensorKind.ac),
        Sensor(
            "grid_in_out_label",
            0,
            lambda data, _: _GRID_MODES.get(_read_byte(data, 80)),
            "",
            "On-grid Mode",
            SensorKind.ac,
        ),
        # pgrid with sign
        Sensor(
            "active_power",
            0,
            lambda data, _: (-1 if _read_byte(data, 80) == 2 else 1)
            * _read_power2(data, 38),
            "W",
            "Active Power",
            SensorKind.ac,
        ),
        Sensor("pback_up", 81, _read_power2, "W", "Back-up Power", SensorKind.ups),
        Sensor(
            "plant_power",
            0,
            lambda data, _: round(_read_power2(data, 47) + _read_power2(data, 81)),
            "W",
            "Plant Power",
            None,
        ),
        Sensor("diagnose_result", 89, _read_bytes4, "", "Diag Status", None),
        # ppv1 + ppv2 + pbattery - active_power
        Sensor(
            "house_consumption",
            0,
            lambda data, _: round(_read_voltage(data, 0) * _read_current(data, 2))
            + round(_read_voltage(data, 5) * _read_current(data, 7))
            + round(_read_voltage(data, 10) * _read_current(data, 18))
            - ((-1 if _read_byte(data, 80) == 2 else 1) * _read_power2(data, 38)),
            "W",
            "House Comsumption",
            None,
        ),
    )

    @classmethod
    async def _make_model_request(cls, host: str, port: int) -> InverterInfo:
        response = await _read_from_socket(cls._READ_DEVICE_VERSION_INFO, (host, port))
        return InverterInfo(
            model_name=response[12:22].decode("utf-8").rstrip(),
            serial_number=response[38:54].decode("utf-8"),
            software_version=response[58:70].decode("utf-8"),
        )

    @classmethod
    async def _make_request(cls, host: str, port: int) -> Dict[str, Any]:
        raw_data = await _read_from_socket(cls._READ_DEVICE_RUNNING_DATA, (host, port))
        data = cls._map_response(raw_data[7:-2], cls.__sensors)
        return data

    @classmethod
    def sensors(cls) -> Tuple[Sensor, ...]:
        return cls.__sensors


# registry of supported inverter models
REGISTRY = [ET, ES]
