# Copyright (c) 2025 Bytedance Ltd. and/or its affiliates
# SPDX-License-Identifier: MIT
from .llm import async_respone

async def theme_classifier_agent(content, model, lang, cycle=5):
    respone = {}
    for i in range(cycle):
        try:
            if lang == 'en':
                from .prompts_en import prompts
            else:
                from .prompts_zh import prompts
            messages = [
                {"role": "system", "content": prompts['theme_class_sys']},
                {"role": "user", "content": prompts['theme_class'].render(content=content)},
            ]

            respone = await async_respone(messages, model, temperature=0.01, top_p=0.7, max_tokens=12288, cycle=5)
            if respone.get('Run status', '') == "System Error":
                return respone
            assert 'Decision' in respone.keys()
        except Exception as e:
            print(f"[{i}/{cycle}] Worker failed with error: {e}")
            if i == cycle - 1:
                respone = {"Run status": "System Error", "Error message": str(e)}
    return respone
