import os
import sys
import asyncio
import pandas as pd
from scripts.base import json_parse
from volcenginesdkarkruntime import AsyncArk
from scripts.prompts import prompt_full_text_filter
from scripts.llm_info import api_key, model_full_text_filter

MAX_CONCURRENT_REQUESTS = 30
client = AsyncArk(api_key=api_key, timeout=3600 * 1)


async def fetch_model_response(session_id, content, semaphore, model, cycle_num=5):
    messages = [
        {
            "role": "system",
            "content": prompt_full_text_filter
        },
        {
            "role": "user",
            "content": content
        }
    ]
    async with semaphore:
        for i in range(cycle_num):
            try:
                completion = await client.chat.completions.create(
                    model=model,
                    messages=messages,
                    temperature=0.1,
                    # top_p=0.7,
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
    file_path = sys.argv[1]
    output_file_name = sys.argv[2]

    if os.path.exists(output_file_name):
        sys.exit('Output file already exists.')

    df = pd.read_table(file_path, header=None)
    df.rename(
        columns={
            0: 'session_id',
            1: 'text_path'
        },
        inplace=True
    )

    file_path_dict = dict(zip(list(df['session_id']), list(df['text_path'])))
    sessions = {}
    for file_id, file in file_path_dict.items():
        try:
            with open(file) as f:
                file_content = f.read()
            sessions[file_id] = file_content
        except:
            print(f'Can not read file: {file_id}')

    results = await handle_multiple_sessions(sessions, model_full_text_filter)

    result_dict = {}
    for session_id, response in results:
        result_dict[session_id] = response

    dfrst = pd.DataFrame(result_dict).T
    dfM = pd.merge(df, dfrst, left_on='session_id', right_index=True)
    dfM.to_csv(output_file_name, index=False, sep='\t', header=False)


if __name__ == '__main__':
    asyncio.run(main())
