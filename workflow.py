import asyncio
from datetime import timedelta

from temporalio import workflow
from temporalio.common import RetryPolicy

with workflow.unsafe.imports_passed_through():
    from shared import DropletSpec, DropletResult
    from activities import DropletActivities


@workflow.defn
class DropletWorkflow:
    def __init__(self) -> None:
        self.instructions: asyncio.Queue[str] = asyncio.Queue()
        self.terminate = False

    @workflow.run
    async def run(self, input: str) -> str:
        workflow.logger.workflow_info_on_message = False
        workflow.logger.info(f"Droplet creation requested with spec: {input}")

        retry_policy = RetryPolicy(
            initial_interval=timedelta(seconds=15),
            backoff_coefficient=2.0,
            maximum_interval=timedelta(seconds=120),
            maximum_attempts=1,
        )

        droplet_record = await workflow.execute_activity_method(
            DropletActivities.create_droplet,
            input,
            start_to_close_timeout=timedelta(seconds=300),
            retry_policy=retry_policy,
        )
        while True:
            await workflow.wait_condition(
                lambda: not self.instructions.empty() or self.terminate
            )

            while not self.instructions.empty():
                instruction = self.instructions.get_nowait()

                if instruction == "terminate":
                    self.terminate = True
                    workflow.logger.info("Terminating droplet")
                elif instruction == "reboot":
                    workflow.logger.info("Rebooting droplet")
                    droplet_terminate_result = await workflow.execute_activity_method(
                        DropletActivities.reboot_droplet,
                        droplet_record,
                        start_to_close_timeout=timedelta(seconds=5),
                    )
            if self.terminate is True:
                break

        droplet_terminate_result = await workflow.execute_activity_method(
            DropletActivities.terminate_droplet,
            droplet_record,
            start_to_close_timeout=timedelta(seconds=5),
        )

    @workflow.signal
    async def lifecycle_signals(self, instruction: str) -> None:
        await self.instructions.put(instruction)
