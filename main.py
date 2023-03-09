import asyncio
import datetime
import logging

from utils import scan, connect, get_characteristics
from utils import get_database


logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

required_services = ["Temperature", "Humidity"]
services_to_subscribe = []
clients = []

database = get_database("main")


async def main():
    logger.info("Starting program")

    # device_name can be a substring of the device name (e.g. "Nano" will match "Nano 33 BLE Sense")
    base_device_name = "Nano 33 BLE Sense"
    ble_devices = await scan(base_device_name)
    
    for device in ble_devices:
        logger.info(f"Device found: {device}")
        logger.info(f"Connecting to {device.name}")

        client = await connect(device)
        clients.append((device.name, client))

        characteristics = get_characteristics(client, required_services)
        logger.info(f"Characteristics found: {characteristics}")

        for char in characteristics:
            description, gatt_char = char
            if description.lower() in map(str.lower, required_services):
                callback_func_format = f"{description.lower()}_callback"
                services_to_subscribe.append((gatt_char, callback_func_format))

        logger.info(f"Services to subscribe to: {services_to_subscribe}")

    while True:
        try:
            for index, client_tuple in enumerate(clients):

                name, client = client_tuple
                readings = {}
                
                for callback in services_to_subscribe:
                    gatt_char, callback_func_format = callback
                    data = await client.read_gatt_char(gatt_char)
                    data = eval(callback_func_format)(gatt_char, data)
                    key, value = data
                    readings.update({key: value})

                collection = database[f"{name}_{str(index)}"]
                collection.insert_one({
                    "timestamp": datetime.datetime.now(),
                    "data": readings,
                    "device_address": client.address,
                })

            await asyncio.sleep(10)

        except KeyboardInterrupt:
            logger.info("Exiting program")
            for client_tuple in clients:
                name, client = client_tuple
                await client.disconnect()
            break
        except Exception as e:
            logger.error(f"Error: {e}")
            for client_tuple in clients:
                name, client = client_tuple
                await client.disconnect()
            break


if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    asyncio.run(main())
