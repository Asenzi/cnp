import asyncio
from collections import defaultdict
from typing import Any

from fastapi import WebSocket


class ImRealtimeHub:
    def __init__(self) -> None:
        self._connections: dict[int, set[WebSocket]] = defaultdict(set)
        self._lock = asyncio.Lock()

    async def connect(self, *, user_pk: int, websocket: WebSocket) -> None:
        await websocket.accept()
        async with self._lock:
            self._connections[int(user_pk)].add(websocket)

    async def disconnect(self, *, user_pk: int, websocket: WebSocket) -> None:
        async with self._lock:
            bucket = self._connections.get(int(user_pk))
            if not bucket:
                return
            if websocket in bucket:
                bucket.remove(websocket)
            if not bucket:
                self._connections.pop(int(user_pk), None)

    async def is_online(self, *, user_pk: int) -> bool:
        async with self._lock:
            bucket = self._connections.get(int(user_pk))
            return bool(bucket)

    async def send_to_user(self, *, user_pk: int, event: str, data: dict[str, Any]) -> bool:
        async with self._lock:
            sockets = list(self._connections.get(int(user_pk), set()))
        if not sockets:
            return False

        stale: list[WebSocket] = []
        payload = {"event": str(event), "data": data}
        sent_count = 0
        for socket in sockets:
            try:
                await socket.send_json(payload)
                sent_count += 1
            except Exception:  # noqa: BLE001
                stale.append(socket)

        if not stale:
            return sent_count > 0

        async with self._lock:
            bucket = self._connections.get(int(user_pk))
            if not bucket:
                return
            for socket in stale:
                if socket in bucket:
                    bucket.remove(socket)
            if not bucket:
                self._connections.pop(int(user_pk), None)
        return sent_count > 0

    async def send_to_users(self, *, user_pks: list[int], event: str, data: dict[str, Any]) -> dict[int, bool]:
        result: dict[int, bool] = {}
        for user_pk in {int(item) for item in user_pks if int(item) > 0}:
            result[user_pk] = await self.send_to_user(user_pk=user_pk, event=event, data=data)
        return result

    async def broadcast(self, *, event: str, data: dict[str, Any]) -> None:
        async with self._lock:
            pairs = [(user_pk, list(sockets)) for user_pk, sockets in self._connections.items()]
        payload = {"event": str(event), "data": data}
        stale_pairs: list[tuple[int, WebSocket]] = []
        for user_pk, sockets in pairs:
            for socket in sockets:
                try:
                    await socket.send_json(payload)
                except Exception:  # noqa: BLE001
                    stale_pairs.append((int(user_pk), socket))

        if not stale_pairs:
            return

        async with self._lock:
            for user_pk, socket in stale_pairs:
                bucket = self._connections.get(user_pk)
                if not bucket:
                    continue
                if socket in bucket:
                    bucket.remove(socket)
                if not bucket:
                    self._connections.pop(user_pk, None)


im_realtime_hub = ImRealtimeHub()
