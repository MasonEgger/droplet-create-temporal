import asyncio
import sys
import argparse


from shared import TASK_QUEUE_NAME, DropletSpec
from temporalio.client import Client
from workflow import DropletWorkflow


async def main():
    # Create client connected to server at the given address
    client = await Client.connect("localhost:7233", namespace="default")

    parser = argparse.ArgumentParser(
        description="Create a DigitalOcean Droplet and manage its lifecycle via Temporal"
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("-c", "--create", action="store_true", help="Create a Droplet")
    group.add_argument("-r", "--reboot", action="store_true", help="Reboot a Droplet")
    group.add_argument(
        "-t", "--terminate", action="store_true", help="Terminate a Droplet"
    )
    parser.add_argument("-n", "--name", help="Name of the Droplet", required=True)

    args = parser.parse_args()

    workflow_id = f"droplet-{args.name}"

    if args.create is True:
        await create_droplet(client, args.name, workflow_id)
    elif args.reboot is True:
        await send_signal(client, "reboot", workflow_id)
    elif args.terminate is True:
        await send_signal(client, "terminate", workflow_id)
    else:
        parser.print_help()
        sys.exit(1)


async def send_signal(client: Client, signal: str, workflow_id: str):
    handle = client.get_workflow_handle(workflow_id)
    await handle.signal("lifecycle_signals", signal)


async def create_droplet(client: Client, name: str, workflow_id: str):
    # Execute a workflow
    handle = await client.start_workflow(
        DropletWorkflow.run,
        name,
        id=workflow_id,
        task_queue=TASK_QUEUE_NAME,
    )


if __name__ == "__main__":
    asyncio.run(main())
