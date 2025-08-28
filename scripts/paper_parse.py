# Copyright (c) 2025 Bytedance Ltd. and/or its affiliates
# SPDX-License-Identifier: MIT
import re
import os
import json
import asyncio
from .llm import async_chat_with_image
from .base import encode_image, get_image_pixel_size


def find_image_paths(data, paths=None):
    """
    递归查找JSON数据中的'image_path'和对应的'type'，当'type' == 'table'时保存。

    :param data: 当前的JSON数据，可以是字典、列表或其他类型
    :param paths: 用于存储找到的(type, image_path)元组
    :return: 包含符合条件的(type, image_path)的列表
    """
    if paths is None:
        paths = []

    if isinstance(data, dict):
        # 如果当前数据是字典，检查其中是否有 'image_path' 和 'type'
        image_path = data.get("image_path")
        item_type = data.get("type")
        # 当 'type' 为 'table' 且有 'image_path' 时，保存该路径
        if item_type == "table" and image_path:
            paths.append((item_type, image_path))
        if item_type == "image" and image_path:
            paths.append(('figure', image_path))
        # 递归遍历字典中的所有子项
        for key, value in data.items():
            find_image_paths(value, paths)
    elif isinstance(data, list):
        # 如果当前数据是列表，遍历列表中的每一项
        for item in data:
            find_image_paths(item, paths)
    return paths


def reference_clean(content):
    img_patter = r'\!\[.*?\]\((.*?)\)'
    if '# References\n' in content:
        ref_split = content.split('# References\n')
    elif '# REFERENCES\n' in content:
        ref_split = content.split('# REFERENCES\n')
    else:
        print(f"未监测到“references”，跳过reference清理。")
        return content
    if len(ref_split) > 2:
        print('监测到多个“references”，跳过reference清理。')
        return content
    else:
        matches = re.findall(img_patter, ref_split[1])
        if matches:
            return ref_split[0] + matches[0] + ref_split[1].split(matches[0])[1]
        else:
            # logging.info("REF: Table/figure not found in reference.")
            return ref_split[0]


def paper_str_parse(file, middle_json, ref_clean=True):
    '''
    从论文的md文件中获取论文信息，包括论文的文本、表格和图片。
    :param file: 论文的md文件路径
    :param middle_json: 论文的中间json文件路径
    :return: 论文的文本、表格和图片
    '''
    raw_text_content = open(file, 'r', encoding='utf-8').read()
    raw_text_content = raw_text_content.replace(
        '\xa0', ' ').replace(
        '\u202f', ' ').replace(
        '\u2002', ' ').replace(
        '\u2009', ' ')
    raw_text_content = re.sub(' +', ' ', raw_text_content)
    raw_text_content = re.sub(' +\n', '\n', raw_text_content)
    if ref_clean:
        raw_text_content = reference_clean(raw_text_content)

    text_content_list = []
    for chunk in raw_text_content.split('\n\n'):
        text_content_list.append(chunk.strip())

    text_content = '\n\n'.join(text_content_list)

    with open(middle_json, "r", encoding="utf-8") as file:
        json_data = json.load(file)

    image_paths_raw = find_image_paths(json_data)
    image_paths = []
    [image_paths.append(i) for i in image_paths_raw if i not in image_paths]

    return text_content, image_paths


async def mul_modal_summary(text_content, image_paths, images_base_path, model, lang='ch'):
    if lang == 'en':
        from .prompts_en import prompts
    else:
        from .prompts_zh import prompts
    prompt_session = {}
    prompt_dict = {
        'table': prompts['table_prompts'],
        'figure': prompts['figure_prompts'],
    }
    for idx, (img_type, img_name) in enumerate(image_paths):
        image_path = os.path.join(images_base_path, img_name)
        height, width, channels = get_image_pixel_size(image_path)
        if height < 75 and width < 75:
            continue
        if len(text_content.split(f'![](images/{img_name}')) == 2:
            [chunk_up, chunk_down] = text_content.split(f'![](images/{img_name}')
            chunk_use = chunk_up.split('\n\n')[-2:]
            chunk_use += chunk_down.split('\n\n')[:2]
        else:
            [chunk_up] = text_content.split(f'![](images/{img_name}')
            chunk_use = chunk_up.split('\n\n')[-2:]
        # chunk_use += chunk_down.split('\n\n')[:2]
        chunk_content = "\n".join(chunk_use)
        prompt_session[idx] = {
            'img_id': img_name.split('.')[0],
            'img_type': img_type,
            'img_base64': encode_image(image_path),
            'prompt': prompt_dict[img_type].render(chunk_content=chunk_content)
        }

    if len(prompt_session) == 0:
        return {}

    tasks = []
    for session_id, session in prompt_session.items():
        tasks.append(async_chat_with_image(session['prompt'], session['img_base64'], model))
    summarys = await asyncio.gather(*tasks)

    summarys_dict = dict(zip(prompt_session.keys(), summarys))
    for k, v in summarys_dict.items():
        raw_value = prompt_session[k]
        raw_value.update({'summary': v})
        prompt_session[k] = raw_value

    return prompt_session


def mul_modal_chunk(prompt_session, base_path):
    summary_chunks = []
    for _id, v in prompt_session.items():
        summary = v['summary'].replace('\n\n', '\n')
        img_id = v['img_id']
        if v['img_type'] == 'table':
            try:
                table_md = open(os.path.join(base_path, f'table_parse/{img_id}.md'), 'r', encoding='utf-8').read()
            except:
                continue
            table_md = table_md.replace('\n\n', '\n').strip('```')
            table_chunk = f'''<summary of table id="{img_id}">
    {summary.strip()}
    </summary of table id="{img_id}">
    <table id="{img_id}">
    {table_md.strip()}
    </table id="{img_id}">'''
            summary_chunks.append(table_chunk)
        else:
            table_chunk = f'''<summary of figure id="{img_id}">
    {summary.strip()}
    </summary of figure id="{img_id}">'''
            summary_chunks.append(table_chunk)
    return summary_chunks
