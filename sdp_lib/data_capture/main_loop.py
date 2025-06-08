import asyncio
from collections.abc import Iterable

from sdp_lib.data_capture.producers import AbstractProducer
from sdp_lib.data_capture.storage import LogWriter


async def main(delay: float, producers: Iterable[AbstractProducer], log_writer: LogWriter):
    while True:
        pending = [asyncio.create_task(prod.request_and_process(), name=prod.get_name()) for prod in producers]
        while pending:
            done, pending = await asyncio.wait(pending, return_when=asyncio.FIRST_COMPLETED)
            for done_task in done:
                await done_task
                producer: AbstractProducer = done_task.result()
                producer.event_process()
        asyncio.create_task(asyncio.to_thread(log_writer.write_all))
        await asyncio.sleep(delay)