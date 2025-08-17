import json
import base64
from urllib.request import urlopen
from datetime import datetime
from typing import List

from .openai_client import client
from .db import get_messages_collection

# 간단 날씨 Mock
async def get_weather_info(location: str) -> dict:
    return {
        "location": location,
        "temperature": "22°C",
        "condition": "맑음",
        "humidity": "65%",
        "wind": "동남풍 2m/s",
    }


async def correct_spelling(text: str) -> dict:
    prompt = f"""다음 문장의 맞춤법을 교정해주세요. JSON 형식으로 응답해주세요.

문장: "{text}"

응답 형식:
{{
  "original": "원본 문장",
  "corrected": "교정된 문장",
  "corrections": [{{"wrong":"","correct":"","position":""}}]
}}
"""
    completion = await client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
    )
    try:
        return json.loads(completion.choices[0].message.content)
    except Exception:
        return {"original": text, "corrected": completion.choices[0].message.content}


async def translate_text(text: str, target_language: str = "영어") -> dict:
    prompt = f"다음 텍스트를 {target_language}로 번역해주세요:\n\n{text}\n\n번역 결과만 출력해주세요."
    completion = await client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
    )
    return {"original": text, "translated": completion.choices[0].message.content, "target_language": target_language}


async def generate_image(prompt: str) -> dict:
    response = await client.images.generate(model="dall-e-3", prompt=prompt, n=1, size="1024x1024")
    image_url = response.data[0].url
    image_bytes = urlopen(image_url).read()
    image_base64 = base64.b64encode(image_bytes).decode("utf-8")
    return {"image_url": image_url, "image_base64": image_base64, "prompt": prompt}


async def chatbot_response(message: str, context: List[dict] | None = None) -> str:
    messages = [{"role": "system", "content": "당신은 도움이 되는 AI 어시스턴트입니다. 한국어로 대화합니다."}]
    if context:
        messages.extend(context)
    messages.append({"role": "user", "content": message})

    completion = await client.chat.completions.create(model="gpt-4", messages=messages)
    return completion.choices[0].message.content


TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "특정 지역의 날씨 정보를 가져옵니다",
            "parameters": {"type": "object", "properties": {"location": {"type": "string"}}, "required": ["location"]},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "correct_spelling",
            "description": "텍스트의 맞춤법을 교정합니다",
            "parameters": {"type": "object", "properties": {"text": {"type": "string"}}, "required": ["text"]},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "translate_text",
            "description": "텍스트를 번역합니다",
            "parameters": {
                "type": "object",
                "properties": {"text": {"type": "string"}, "target_language": {"type": "string"}},
                "required": ["text"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "generate_image",
            "description": "이미지를 생성합니다",
            "parameters": {"type": "object", "properties": {"prompt": {"type": "string"}}, "required": ["prompt"]},
        },
    },
]


async def handle_function_calling(message: str) -> dict:
    completion = await client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": message}],
        tools=TOOLS,
        tool_choice="auto",
    )
    response_message = completion.choices[0].message
    if not response_message.tool_calls:
        return {"type": "text", "content": response_message.content}

    results = []
    for call in response_message.tool_calls:
        name = call.function.name
        args = json.loads(call.function.arguments)
        if name == "get_weather":
            res = await get_weather_info(args["location"])
        elif name == "correct_spelling":
            res = await correct_spelling(args["text"])
        elif name == "translate_text":
            res = await translate_text(args["text"], args.get("target_language", "영어"))
        elif name == "generate_image":
            res = await generate_image(args["prompt"])
        else:
            res = {"error": f"unknown function: {name}"}
        results.append({"function": name, "result": res})

    return {"type": "function_call", "content": response_message.content, "results": results}
