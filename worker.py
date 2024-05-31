import asyncio
import aiohttp
import logging

from temporalio.client import Client
from temporalio.worker import Worker

from workflow import DropletWorkflow
from activities import DropletActivities
from shared import TASK_QUEUE_NAME


async def main():
    logging.basicConfig(level=logging.INFO)
    # Start client
    client = await Client.connect("localhost:7233")

    # Run the worker
    async with aiohttp.ClientSession() as session:
        activities = DropletActivities(session)

        worker = Worker(
            client,
            task_queue=TASK_QUEUE_NAME,
            workflows=[DropletWorkflow],
            activities=[
                activities.create_droplet,
                activities.reboot_droplet,
                activities.terminate_droplet,
            ],
        )
        logging.info(f"Starting the worker....{client.identity}")
        await worker.run()


if __name__ == "__main__":
    asyncio.run(main())
