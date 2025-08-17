from typing import Dict
from fastapi import WebSocket
import logging

logger = logging.getLogger(__name__)

class ConnectionManager:
    def __init__(self) -> None:
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, nickname: str) -> None:
        await websocket.accept()
        self.active_connections[nickname] = websocket
        logger.info(f"사용자 {nickname} 연결됨. 총 연결 수: {len(self.active_connections)}")

    def disconnect(self, nickname: str) -> None:
        if nickname in self.active_connections:
            self.active_connections.pop(nickname, None)
            logger.info(f"사용자 {nickname} 연결 해제됨. 총 연결 수: {len(self.active_connections)}")

    async def broadcast(self, message: dict) -> None:
        if not self.active_connections:
            logger.warning("활성 연결이 없어 메시지를 전송할 수 없습니다.")
            return
            
        for connection in self.active_connections.values():
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"메시지 전송 실패: {e}")
                # 연결이 끊어진 경우 제거
                self._remove_dead_connections()

    def _remove_dead_connections(self):
        """끊어진 연결들을 정리"""
        dead_connections = []
        for nickname, connection in self.active_connections.items():
            if connection.client_state.value == 3:  # WebSocketState.DISCONNECTED
                dead_connections.append(nickname)
        
        for nickname in dead_connections:
            self.disconnect(nickname)
