import os
import sys
import asyncio
import pandas as pd
from scripts.base import json_parse
from volcenginesdkarkruntime import AsyncArk
from scripts.prompts import prompt_abstract_filter
from scripts.llm_info import api_key, model_abstract_filter

MAX_CONCURRENT_REQUESTS = 100
client = AsyncArk(api_key=api_key, timeout=3600 * 1)


async def fetch_model_response(session_id, content, semaphore, model, cycle_num=5):
    messages = [
        {
            "role": "system",
            "content": "你是一位癌症发病风险因素Meta分析摘要审查员。你的任务是阅读文献，提取信息，并确定摘要是否符合所需标准。"
        },
        {
            "role": "user",
            "content": prompt_abstract_filter.render(content=content)
        }
    ]

    async with semaphore:
        for i in range(5):
            try:
                completion = await client.batch_chat.completions.create(
                    model=model,
                    messages=messages,
                    temperature=0.01,
                    top_p=0.7,
                )

                response_content = ' '.join(
                    completion.choices[0].message.content.replace('，', ',').replace('：', ':').split()
                )
                response = json_parse(response_content)
                return session_id, response
            except Exception as e:
                print(f"[{i + 1}/{cycle_num}] Error in session {session_id}: {e}")
                if i + 1 == cycle_num:
                    response = {'Result': f'Error:{e}'}
        return session_id, response


# 定义异步函数来并发处理多个会话
async def handle_multiple_sessions(sessions, model, cycle_num=5):
    semaphore = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)
    tasks = [
        fetch_model_response(
            session_id, content, semaphore, model, cycle_num) for session_id, content in sessions.items()
    ]
    results = await asyncio.gather(*tasks)
    return results


async def main():
    abstract_file_name = sys.argv[1]
    output_file_name = sys.argv[2]

    if os.path.exists(output_file_name):
        sys.exit('Output file already exists.')

    df = pd.read_table(abstract_file_name, names=['session_id', 'content'])
    sessions = dict(zip(list(df['doi']), list(df['Text'])))
    results = await handle_multiple_sessions(sessions, model_abstract_filter)
    result_dict = dict(results)
    dfrst = pd.DataFrame(result_dict).T
    dfM = pd.merge(df, dfrst, left_on='session_id', right_index=True)
    dfM.to_csv(output_file_name, index=False)


if __name__ == '__main__':
    asyncio.run(main())
