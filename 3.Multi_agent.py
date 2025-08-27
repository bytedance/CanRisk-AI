#!/bin/env python3
# -*- coding: utf-8 -*-
# auther: shiyuan tong
# email: tongshiyuan@bytedance.com
import os
import json
import asyncio
from lightrag import QueryParam
from scripts.grade_agent import grade_agent
from scripts.RAG_lightRAG import initialize_rag
from scripts.theme_class_agent import theme_classifier_agent
from scripts.base import FileInfoCollector, merge_chunks
from scripts.llm_info import model_vison, model_rag, model_agent
from scripts.paper_parse import paper_str_parse, mul_modal_summary, mul_modal_chunk
from scripts.level1_agents import cohort_agent, outcome_agent, cancer_agent, risk_factor_agent, group_agent


def get_args():
    # 定义外部传参函数
    import argparse
    parser = argparse.ArgumentParser(description='multi agent for CanRisk-DB')
    parser.add_argument('-i', '--input_dir', type=str, required=True, help='The path to the input file.')
    parser.add_argument('-o', '--out_dir', type=str, default='.', help='The path of the output files.')
    parser.add_argument('-r', '--rag_dir', type=str, default='', help='rag path of paper.')
    parser.add_argument('--theme_class', action='store_true', help='Use theme class.')
    parser.add_argument('--grade', action='store_true', help='Use grade.')
    parser.add_argument('-l', '--lang', default='en', help='use English(en) or Chinese(ch) prompt.')
    args = parser.parse_args()
    return args


async def main():
    # 参数读取
    args = get_args()
    input_dir = args.input_dir
    out_path = args.out_dir
    lang = args.lang
    paper = FileInfoCollector(input_dir)
    theme = args.theme_class
    grade = args.grade

    if args.rag_dir:
        db_path = args.rag_dir
        is_rag = True
    else:
        db_path = os.path.join(out_path, 'paper_db')
        if not os.path.exists(db_path):
            os.makedirs(db_path)
        is_rag = False

    text_content, image_paths = paper_str_parse(paper.md_files, paper.json_files)
    with open(f'{out_path}/text_parse.md', 'w') as file:
        file.write(text_content)
    prompt_session = await mul_modal_summary(
        text_content, image_paths, paper.image_path, model=model_vison, lang=lang)
    if prompt_session:
        with open(f'{out_path}/image_parse.json', 'w') as f:
            json.dump(prompt_session, f, indent=4, ensure_ascii=False)
        summary_chunks = mul_modal_chunk(prompt_session, paper.directory)
    else:
        summary_chunks = []
    text_chunks = merge_chunks(text_content.split('\n\n'))
    chunks = text_chunks + summary_chunks
    chunks_not_empty = []
    for i in chunks:
        i = i.strip()
        if i:
            chunks_not_empty.append(i)
    content = '\n\n'.join(chunks_not_empty)
    with open(f'{out_path}/chunks.txt', 'w', encoding='utf-8') as file:
        file.write(content)

    # 2. 推理论文是否符合主题
    if theme:
        theme_class = await theme_classifier_agent(text_content, model_agent, lang)
        if theme_class['Decision'] == 'Rejected':
            print('paper is not related to cancer risk.')
            print(theme_class)
            return

    # 3.1 grade等级判断
    if grade:
        grade_evaluator = await grade_agent(text_content, model_agent, lang)
        with open(f'{out_path}/grade_evaluator.json', 'w', encoding='utf-8') as file:
            json.dump(grade_evaluator, file, indent=4, ensure_ascii=False)

    # 3.3 构建多模态RAG
    # print(len(chunks))
    rag = await initialize_rag(db_path)
    if not is_rag:
        import nest_asyncio
        nest_asyncio.apply()
        rag.insert(content, '\n\n', True)

    # 3.2 level 1 信息提取
    max_tokens = 12288

    # 3.2.1 队列信息
    cohort_info = await cohort_agent(content=content, model=model_agent, lang=lang, max_tokens=max_tokens, rag=None)
    print('cohort:', cohort_info)
    with open(f'{out_path}/cohort_info.json', 'w', encoding='utf-8') as file:
        json.dump(cohort_info, file, indent=4, ensure_ascii=False)

    # 3.2.2-4 结局信息 & 风险因素信息 & 风险效应量提取
    outcome_info = await outcome_agent(content=content, model=model_agent, lang=lang, max_tokens=max_tokens, rag=None)
    print('info:', outcome_info)
    with open(f'{out_path}/outcome_info.json', 'w', encoding='utf-8') as file:
        json.dump(outcome_info, file, indent=4, ensure_ascii=False)

    # 3.2.2.1 结局信息解析与判断 & 风险因素信息解析与判断
    cancer_content = outcome_info['Outcome']
    risk_factor_content = outcome_info['Risk Factors']
    if not risk_factor_content:
        risk_factor_content = ['本文主要致癌风险因素']
    abs_path = os.path.split(os.path.realpath(__file__))[0]
    cancer_list = await cancer_agent(content=cancer_content, abs_path=abs_path, model=model_agent, lang=lang,
                                     max_tokens=max_tokens)
    print('cancer:', cancer_list)
    with open(f'{out_path}/cancer_adj.json', 'w', encoding='utf-8') as file:
        json.dump(cancer_list, file, indent=4, ensure_ascii=False)
    risk_factor_list = await risk_factor_agent(content=risk_factor_content, abs_path=abs_path, model=model_agent, lang=lang,
                                               max_tokens=max_tokens)
    print('risk factor:', risk_factor_list)
    with open(f'{out_path}/risk_factor_adj.json', 'w', encoding='utf-8') as file:
        json.dump(risk_factor_list, file, indent=4, ensure_ascii=False)

    # 3.2 获得组合分组信息 & 4.1 根据组合分组信息和RAG对人数和效应量提取
    risk_stimate = outcome_info['RiskEstimate']
    design = outcome_info['Design']
    group_dict = {}
    for cid, cinfo in cancer_content.items():
        for risk_factor in risk_factor_content:
            cancer = cinfo['Name']
            import nest_asyncio
            nest_asyncio.apply()
            raw_chunk = rag.query(
                f"「{cancer}」和「{risk_factor}」的分组信息、人数信息、方法、结果、图表？",
                param=QueryParam(mode='mix', top_k=10, only_need_context=True)
            )
            kg_context = raw_chunk.get('kg_context', '')
            if not kg_context:
                kg_context = ''
            vector_context = raw_chunk.get('vector_context', '')
            if not vector_context:
                vector_context = ''
            chunk = f'{kg_context}\n\n{vector_context}'
            cohort = json.dumps(cohort_info, ensure_ascii=False)
            cohort_id = ', '.join(cohort_info.keys())
            group_info = await group_agent(
                chunk=chunk, outcome=cancer, risk_Factors=risk_factor, cohort=cohort, risk_class=risk_stimate,
                cohort_id=cohort_id, design=design, model=model_agent, lang=lang, max_tokens=max_tokens)
            group_dict[f'{cid}:{risk_factor}'] = group_info
    with open(f'{out_path}/group_info.json', 'w', encoding='utf-8') as file:
        json.dump(group_dict, file, indent=4, ensure_ascii=False)
    # print(group_dict)


if __name__ == "__main__":
    asyncio.run(main())
