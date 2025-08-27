import asyncio
from typing import Dict
from .base import json_parse
from volcenginesdkarkruntime import AsyncArk
from .llm_info import model_agent as chat_api_key
from .llm_info import model_vison as vision_api_key


async def async_respone(messages, model, temperature=0.01, top_p=0.7, max_tokens=12288, cycle=5) -> Dict:
    client = AsyncArk(
        api_key=chat_api_key
    )
    semaphore = asyncio.Semaphore(3)
    async with semaphore:
        for attempt in range(cycle):
            try:
                response = await client.chat.completions.create(
                    model=model,
                    messages=messages,
                    temperature=temperature,
                    top_p=top_p,
                    max_tokens=max_tokens,
                )
                response_content = ' '.join(response.choices[0].message.content.replace('，', ',').split())
                if '</answer>' in response_content:
                    response_content = response_content.split('<answer>')[-1].strip('</answer>')
                if "I'm unable to answer that question" in response_content:
                    return {"Run status": "System Error"}
                response = json_parse(response_content)
                return response
            except Exception as e:
                if attempt == cycle - 1:
                    return {
                        "Run status": "System Error",
                        "content": f"Failed to generate final answer after 5 attempts. Error: {str(e)}"
                    }
                if "Error code: 429" in str(e):
                    await asyncio.sleep(60)


async def async_chat_with_image(prompt, base64_image, vision_model, cycle=5):
    # 需要传给大模型的图片
    # image_path = "path_to_your_image.jpg"
    # 将图片转为Base64编码
    # base64_image = encode_image(image_path)
    client = AsyncArk(
        api_key=vision_api_key
    )
    semaphore = asyncio.Semaphore(3)
    async with semaphore:
        for attempt in range(cycle):
            try:
                response = await client.chat.completions.create(
                    model=vision_model,
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "text",
                                    "text": prompt,
                                },
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": f"data:image/jpeg;base64,{base64_image}"
                                    },
                                },
                            ],
                        }
                    ],
                )
                msg = response.choices[0].message.content.replace('$', '').replace('\\', '')
                if "I'm unable to answer that question" in msg:
                    return 'System Error'
                return msg
            except Exception as e:
                if attempt == cycle - 1:
                    return f'Failed to generate step after {cycle} attempts. Error: {str(e)}"'
                if "Error code: 429" in str(e):
                    await asyncio.sleep(60)
