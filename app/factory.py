from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import json

from .config import APP_TITLE, FRONTEND_ORIGINS
from .schemas import TextRequest, WeatherRequest
from .websocket_manager import ConnectionManager
from .db import get_messages_collection, serialize_document
from .services import (
    chatbot_response,
    handle_function_calling,
    get_weather_info,
    correct_spelling,
    translate_text,
    generate_image,
)


def create_app() -> FastAPI:
    app = FastAPI(title=APP_TITLE)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=FRONTEND_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    manager = ConnectionManager()
    messages_collection = get_messages_collection()

    @app.get("/messages")
    async def get_messages():
        messages = list(messages_collection.find().sort("timestamp", 1))
        return [serialize_document(msg) for msg in messages]

    @app.post("/spellcheck")
    async def spellcheck_endpoint(req: TextRequest):
        return await correct_spelling(req.text)

    @app.post("/translate")
    async def translate_endpoint(req: TextRequest):
        return await translate_text(req.text)

    @app.post("/weather")
    async def weather_endpoint(req: WeatherRequest):
        return await get_weather_info(req.location)

    @app.post("/generate-image")
    async def generate_image_endpoint(req: TextRequest):
        return await generate_image(req.text)

    @app.websocket("/ws/{nickname}")
    async def websocket_endpoint(websocket: WebSocket, nickname: str):
        await manager.connect(websocket, nickname)
        try:
            while True:
                raw = await websocket.receive_text()
                try:
                    data = json.loads(raw)
                except json.JSONDecodeError:
                    continue

                timestamp = datetime.utcnow().isoformat()
                data["timestamp"] = timestamp

                msg_type = data.get("type", "text")
                message = data.get("message", "")

                if msg_type == "text":
                    doc = {
                        "nickname": data.get("nickname", nickname),
                        "message": message,
                        "timestamp": timestamp,
                        "type": "text",
                    }
                    result = messages_collection.insert_one(doc)  # 수정: 저장 결과 받기
                    saved_doc = messages_collection.find_one({"_id": result.inserted_id})  # 수정: 저장된 문서 읽기
                    await manager.broadcast(serialize_document(saved_doc))  # 수정: 직렬화 후 브로드캐스트

                elif msg_type == "ai_chat":
                    print(f"AI 챗봇 요청 받음: {message}")
                    past = list(messages_collection.find().sort("timestamp", -1).limit(10))[::-1]
                    context = []
                    for msg in past:
                        role = "assistant" if msg.get("type") == "ai_chat" else "user"
                        context.append({"role": role, "content": msg["message"]})
                    
                    print(f"컨텍스트: {len(context)}개 메시지")
                    reply = await chatbot_response(message, context)
                    print(f"AI 응답: {reply}")
                    
                    ai_msg = {"type": "ai_chat", "nickname": "AI 어시스턴트", "message": reply, "timestamp": timestamp}
                    result = messages_collection.insert_one(ai_msg)  # 수정: 저장 결과 받기
                    saved_ai_msg = messages_collection.find_one({"_id": result.inserted_id})  # 수정: 저장된 문서 읽기
                    print(f"AI 메시지 브로드캐스트 시도: {saved_ai_msg}")
                    await manager.broadcast(serialize_document(saved_ai_msg))  # 수정: 직렬화 후 브로드캐스트
                    print("AI 메시지 브로드캐스트 완료")
                    
                elif msg_type == "function_call":
                    result = await handle_function_calling(message)
                    fn_msg = {
                        "type": "function_result",
                        "nickname": "AI 어시스턴트",
                        "message": json.dumps(result, ensure_ascii=False),
                        "timestamp": timestamp,
                    }
                    result_insert = messages_collection.insert_one(fn_msg)  # 수정: 저장 결과 받기
                    saved_fn_msg = messages_collection.find_one({"_id": result_insert.inserted_id})  # 수정: 저장된 문서 읽기
                    await manager.broadcast(serialize_document(saved_fn_msg))  # 수정: 직렬화 후 브로드캐스트

                elif msg_type == "image_generation":
                    result = await generate_image(message)
                    if "error" not in result:
                        image_msg = {
                            "type": "image",
                            "nickname": "AI 어시스턴트",
                            "message": f"이미지가 생성되었습니다: {message}",
                            "image_data": result["image_base64"],
                            "timestamp": timestamp,
                        }
                    else:
                        image_msg = {
                            "type": "error",
                            "nickname": "AI 어시스턴트",
                            "message": result["error"],
                            "timestamp": timestamp,
                        }
                    result_insert = messages_collection.insert_one(image_msg)  # 수정: 저장 결과 받기
                    saved_image_msg = messages_collection.find_one({"_id": result_insert.inserted_id})  # 수정: 저장된 문서 읽기
                    await manager.broadcast(serialize_document(saved_image_msg))  # 수정: 직렬화 후 브로드캐스트


        except WebSocketDisconnect:
            manager.disconnect(nickname)
            await manager.broadcast({
                "type": "system",
                "nickname": "시스템",
                "message": f"{nickname}님이 나갔습니다.",
                "timestamp": datetime.utcnow().isoformat(),
            })

    return app
