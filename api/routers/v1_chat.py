"""Chat routes: stream one turn as server-sent events, and reset a thread. Thin handlers only."""

from __future__ import annotations

from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response
from starlette.background import BackgroundTask
from starlette.responses import StreamingResponse

from api.dependencies import get_runtime, get_service_keys, get_settings, get_threads
from api.schemas.chat import ChatRequest, ThreadId, ThreadSnapshot
from api.services.agent_runner import AgentRuntime, run_turn
from api.services.snapshots import thread_snapshot
from api.services.sse import encode_event
from api.services.threads import ThreadStore
from app.key_vault import ServiceKeys
from config.ui import UiSettings

router = APIRouter(prefix="/api/v1/chat", tags=["chat"])
UNKNOWN = "That run is no longer available."
BUSY = "A turn is already running for this thread."
SSE_HEADERS = {"Cache-Control": "no-cache", "X-Accel-Buffering": "no"}


async def _frames(
    body: ChatRequest, keys: ServiceKeys, threads: ThreadStore, runtime: AgentRuntime
) -> AsyncGenerator[str]:
    try:
        async for event in run_turn(body, keys=keys, threads=threads, runtime=runtime):
            yield encode_event(event)
    finally:
        threads.release(body.thread_id)


@router.post("/stream")
async def chat_stream(
    body: ChatRequest,
    keys: Annotated[ServiceKeys, Depends(get_service_keys)],
    threads: Annotated[ThreadStore, Depends(get_threads)],
    runtime: Annotated[AgentRuntime, Depends(get_runtime)],
) -> StreamingResponse:
    """Run one turn of ``thread_id`` and stream its events."""
    if not threads.claim(body.thread_id):
        raise HTTPException(status_code=409, detail=BUSY)
    return StreamingResponse(
        _frames(body, keys, threads, runtime),
        media_type="text/event-stream",
        headers=SSE_HEADERS,
        background=BackgroundTask(threads.release, body.thread_id),
    )


@router.get("/threads/{thread_id}")
def get_thread(
    thread_id: ThreadId,
    threads: Annotated[ThreadStore, Depends(get_threads)],
    settings: Annotated[UiSettings, Depends(get_settings)],
) -> ThreadSnapshot:
    """A held thread's messages, workspace and usage, so the interface can resume it."""
    snapshot = thread_snapshot(threads, thread_id, settings.pricing)
    if snapshot is None:
        raise HTTPException(status_code=404, detail=UNKNOWN)
    return snapshot


@router.delete("/threads/{thread_id}", status_code=204)
def reset_thread(
    thread_id: ThreadId, threads: Annotated[ThreadStore, Depends(get_threads)]
) -> Response:
    """Forget a thread's history (new assessment)."""
    if not threads.reset(thread_id):
        raise HTTPException(status_code=409, detail=BUSY)
    return Response(status_code=204)
