import platform
import asyncio
import logging

from bleak import BleakScanner, BLEDevice, BleakGATTCharacteristic

if platform.system() == "Linux":
    from bleak.backends.bluezdbus.client import BleakClientBlueZDBus as BleakClient
else:
    from bleak import BleakClient


logger = logging.getLogger(__name__)


async def scan(device_name: str) -> set[BLEDevice]:
    """
    Function that scans available Bluetooth devices
    If a device's advertised name corresponds to the 'device_name' :param,
    it will be added to the set of devices

    :param device_name: name of the device we are looking for
    :return: set of matching devices
    """
    devices = set(await BleakScanner.discover())
    # only add devices that advertise a name and an address
    devices = {device for device in devices if device.name and device.address}
    # only add devices that have the name of the device we are looking for
    devices = {device for device in devices if device_name in device.name}
    return devices


async def connect(device: BLEDevice) -> BleakClient:
    """
    Function that connects to a device

    WARNING: BleakClientBlueZDBus is Linux specific, this code will break on Windows and Mac

    :param device: device to connect to
    :return: connected client
    """
    client = BleakClient(device)

    # loop until we are connected
    while not client.is_connected:
        try:
            # connect to the device
            await client.connect()
            logger.info(f"Connected: {client.is_connected}")
            return client
        except Exception as e:
            logger.info(f"Connection to {device.name} failed or lost, error: {e}")
            logger.info("Retrying...")
            await asyncio.sleep(1)
            client = BleakClient(device)


def get_characteristics(client: BleakClient, required_services: list[str] = None) -> set[tuple[str, BleakGATTCharacteristic]]:
    """
    Function that gets the services of a device

    :param required_services: list of services to get
    :param client: client to get services from
    """
    characteristics = set()
    advertised_services = client.services
    for service in advertised_services:
        for characteristic in service.characteristics:
            if required_services is None or characteristic.description in required_services:
                if "read" in characteristic.properties and "notify" in characteristic.properties:
                    characteristics.add((characteristic.description, characteristic))
    return characteristics


def temperature_callback(handle, data) -> tuple[str, float]:
    """
    Callback function for temperature characteristic
    :param handle:
    :param data: bytes data received from the characteristic
    :return: temperature in °C
    """
    logger.info(f'Temperature {int.from_bytes(data, byteorder="little", signed=True) / 100}°C')
    return "temperature", int.from_bytes(data, byteorder="little", signed=True) / 100


def humidity_callback(handle, data) -> tuple[str, float]:
    """
    Callback function for humidity characteristic
    :param handle:
    :param data: bytes data received from the characteristic
    :return: humidity in %
    """
    logger.info(f'Humidity {int.from_bytes(data, byteorder="little", signed=False) / 100}%')
    return "humidity", int.from_bytes(data, byteorder="little", signed=False) / 100
