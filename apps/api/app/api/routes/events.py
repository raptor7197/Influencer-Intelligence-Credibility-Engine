import asyncio

from fastapi import APIRouter
from starlette.responses import StreamingResponse

from app.services.event_bus import event_bus

router = APIRouter(tags=["events"])


@router.get("/events")
async def event_stream():
    queue = await event_bus.subscribe()

    async def generate():
        try:
            while True:
                payload = await queue.get()
                yield f"data: {payload}\n\n"
        except asyncio.CancelledError:
            await event_bus.unsubscribe(queue)

    return StreamingResponse(generate(), media_type="text/event-stream")
