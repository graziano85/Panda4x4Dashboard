import asyncio
from bleak import BleakClient

# MAC address del sensore da analizzare (usa FL per iniziare)
ADDRESS = "4B:A2:00:00:01:58"

async def main():
    print("Connessione al sensore...")
    async with BleakClient(ADDRESS) as client:
        print("Connesso. Lettura servizi...\n")
        services = await client.get_services()

        for service in services:
            print("SERVICE:", service.uuid)
            for char in service.characteristics:
                print("  CHAR:", char.uuid, char.properties)

asyncio.run(main())

