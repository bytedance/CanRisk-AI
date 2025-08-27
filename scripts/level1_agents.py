import os
import re
import json
import pandas as pd
from .llm import async_respone
from .RAG_lightRAG import rag_search


async def cohort_agent(content, model, lang, max_tokens, cycle=5, rag=None):
    if lang == 'en':
        from .prompts_en import prompts
    else:
        from .prompts_zh import prompts

    if rag:
        chunks = await rag_search(rag, prompts['sys_prompt_cohort_evaluator'])
        content = chunks

    messages = [
        {"role": "system", "content": prompts['sys_prompt_cohort_evaluator']},
        {"role": "user", "content": prompts['common_input'].render(content=content)}
    ]
    respone = {}
    for i in range(cycle):
        try:
            respone = await async_respone(
                messages, model, temperature=0.01, top_p=0.7, max_tokens=max_tokens, cycle=5)
            if respone.get('Run status', '') == "System Error":
                return respone
            for k, v in respone.items():
                if k:
                    assert 'Name' in v.keys()
                    assert 'Country' in v.keys()
                    assert 'Age' in v.keys()
                    assert 'Timeline' in v.keys()
                    assert 'start_year' in v['Timeline'].keys()
                    assert 'end_year' in v['Timeline'].keys()
                    assert 'Population' in v.keys()
            return respone
        except Exception as e:
            print(f"[{i}/{cycle}] Worker failed with error: {e}")
            if i == cycle - 1:
                respone = {"Run status": "System Error", "Error message": str(e)}
                return respone


async def outcome_agent(content, model, lang, max_tokens, cycle=5, rag=None):
    if lang == 'en':
        from .prompts_en import prompts
    else:
        from .prompts_zh import prompts
    if rag:
        chunks = await rag_search(rag, prompts['sys_prompt_outcomes'])
        content = chunks

    messages = [
        {"role": "system", "content": prompts['sys_prompt_outcomes']},
        {"role": "user", "content": prompts['common_input'].render(content=content)}
    ]
    respone = {}
    for i in range(cycle):
        try:
            respone = await async_respone(
                messages, model, temperature=0.01, top_p=0.7, max_tokens=max_tokens, cycle=5)
            if respone.get('Run status', '') == "System Error":
                return respone
            assert 'Design' in respone.keys()
            assert 'Outcome' in respone.keys()
            assert 'Risk Factors' in respone.keys()
            assert 'RiskEstimate' in respone.keys()
            return respone
        except Exception as e:
            print(f"[{i}/{cycle}] Worker failed with error: {e}")
            if i == cycle - 1:
                respone = {"Run status": "System Error", "Error message": str(e)}
                return respone


async def l1_cancer_agent(content, model, lang, max_tokens, cycle=5, rag=None):
    if lang == 'en':
        from .prompts_en import prompts
    else:
        from .prompts_zh import prompts
    if rag:
        chunks = await rag_search(rag, prompts['sys_prompt_cancers'])
        content = chunks
    messages = [
        {"role": "system", "content": prompts['sys_prompt_cancers']},
        {"role": "user", "content": prompts['common_input'].render(content=content)}
    ]
    respone = {}
    for i in range(cycle):
        try:
            respone = await async_respone(
                messages, model, temperature=0.01, top_p=0.7, max_tokens=max_tokens, cycle=5)
            if respone.get('Run status', '') == "System Error":
                return respone
            for k, v in respone.items():
                if k:
                    for _k in ['Name', 'ICD-10']:
                        assert _k in v.keys()
            return respone
        except Exception as e:
            print(f"[{i}/{cycle}] Worker failed with error: {e}")
            if i == cycle - 1:
                respone = {"Run status": "System Error", "Error message": str(e)}
                return respone


async def l1_risk_factor_agent(content, model, lang, max_tokens, cycle=5, rag=None):
    if lang == 'en':
        from .prompts_en import prompts
    else:
        from .prompts_zh import prompts
    if rag:
        chunks = await rag_search(rag, prompts['sys_prompt_risk_factor'])
        content = chunks
    messages = [
        {"role": "system", "content": prompts['sys_prompt_risk_factor']},
        {"role": "user", "content": prompts['common_input'].render(content=content)}
    ]
    respone = {}
    for i in range(cycle):
        try:
            respone = await async_respone(
                messages, model, temperature=0.01, top_p=0.7, max_tokens=max_tokens, cycle=5)
            if respone.get('Run status', '') == "System Error":
                return respone
            assert 'Risk_factors' in respone.keys()
            assert isinstance(respone['Risk_factors'], list)
            return respone
        except Exception as e:
            print(f"[{i}/{cycle}] Worker failed with error: {e}")
            if i == cycle - 1:
                respone = {"Run status": "System Error", "Error message": str(e)}
                return respone


async def l1_risk_factor_check_agent(content, risk_factors, model, lang, max_tokens, cycle=5, rag=None):
    if lang == 'en':
        from .prompts_en import prompts
    else:
        from .prompts_zh import prompts
    if rag:
        chunks = await rag_search(rag, prompts['sys_prompt_risk_factor_check'])
        content = chunks
    messages = [
        {"role": "system", "content": prompts['sys_prompt_risk_factor_check']},
        {"role": "user", "content": prompts['risk_factors_check_input'].render(
            content=content, risk_factors=risk_factors)}
    ]
    for i in range(cycle):
        try:
            respone = await async_respone(
                messages, model, temperature=0.01, top_p=0.7, max_tokens=max_tokens, cycle=5)
            if respone.get('Run status', '') == "System Error":
                return respone
            assert 'Direct_Exposure' in respone.keys()
            assert isinstance(respone['Direct_Exposure'], list)
            assert 'Hierarchical_Objects' in respone.keys()
            assert isinstance(respone['Hierarchical_Objects'], list)
            return respone
        except Exception as e:
            print(f"[{i}/{cycle}] Worker failed with error: {e}")
            if i == cycle - 1:
                respone = {"Run status": "System Error", "Error message": str(e)}
                return respone


async def l1_effect_size_agent(content, model, lang, max_tokens, cycle=5, rag=None):
    if lang == 'en':
        from .prompts_en import prompts
    else:
        from .prompts_zh import prompts
    if rag:
        chunks = await rag_search(rag, prompts['sys_prompt_effect_size'])
        content = chunks
    messages = [
        {"role": "system", "content": prompts['sys_prompt_effect_size']},
        {"role": "user", "content": prompts['common_input'].render(content=content)}
    ]
    respone = {}
    for i in range(cycle):
        try:
            respone = await async_respone(
                messages, model, temperature=0.01, top_p=0.7, max_tokens=max_tokens, cycle=5)
            if respone.get('Run status', '') == "System Error":
                return respone
            assert 'Design' in respone.keys()
            assert respone['Design'] in ['A', 'B']
            for k, v in respone.items():
                if k and k != 'Design':
                    for _k in ['Type', 'Variables']:
                        assert _k in v.keys()
            return respone
        except Exception as e:
            print(f"[{i}/{cycle}] Worker failed with error: {e}")
            if i == cycle - 1:
                respone = {"Run status": "System Error", "Error message": str(e)}
                return respone


async def cancer_agent(content, abs_path, model, lang, max_tokens, cycle=5):
    if lang == 'en':
        from .prompts_en import prompts
    else:
        from .prompts_zh import prompts
    cancers = pd.read_table(os.path.join(abs_path, './lib/cancers.tsv'), index_col=0)
    dict_output = cancers.to_dict(orient='index')
    content = json.dumps(content, ensure_ascii=False)

    messages = [
        {"role": "system", "content": prompts['sys_prompt_cancer_adj'].render(content=dict_output)},
        {"role": "user", "content": prompts['cancer_adj'].render(content=content)}
    ]
    respone = {}
    for i in range(cycle):
        try:
            respone = await async_respone(
                messages, model, temperature=0.01, top_p=0.7, max_tokens=max_tokens, cycle=5)
            if respone.get('Run status', '') == "System Error":
                return respone
            for k, v in respone.items():
                if k:
                    assert 'id' in v.keys()
                    assert 'subtype' in v.keys()
                    assert 'multi' in v.keys()
            return respone
        except Exception as e:
            print(f"[{i}/{cycle}] Worker failed with error: {e}")
            if i == cycle - 1:
                respone = {"Run status": "System Error", "Error message": str(e)}
                return respone


async def risk_factor_agent(content, abs_path, model, lang, max_tokens, cycle=5):
    if lang == 'en':
        from .prompts_en import prompts
    else:
        from .prompts_zh import prompts
    risk_factors = pd.read_table(os.path.join(abs_path, './lib/risk_factors.tsv'), index_col=0)
    dict_output = dict(zip(risk_factors['ID'].to_list(), risk_factors['risk factor2'].to_list()))
    content = str(content)

    messages = [
        {"role": "system", "content": prompts['sys_prompt_risk_factor_adj'].render(content=dict_output)},
        {"role": "user", "content": prompts['risk_factor_adj'].render(content=content)}
    ]
    respone = {}
    for i in range(cycle):
        try:
            respone = await async_respone(
                messages, model, temperature=0.01, top_p=0.7, max_tokens=max_tokens, cycle=5)
            if respone.get('Run status', '') == "System Error":
                return respone
            for k, v in respone.items():
                if k:
                    assert 'id' in v.keys()
            return respone
        except Exception as e:
            print(f"[{i}/{cycle}] Worker failed with error: {e}")
            if i == cycle - 1:
                respone = {"Run status": "System Error", "Error message": str(e)}
                return respone


async def group_agent(
        chunk, outcome, risk_Factors, cohort, cohort_id, risk_class, design, model, lang, max_tokens, cycle=5):
    if lang == 'en':
        from .prompts_en import prompts
    else:
        from .prompts_zh import prompts
    if design == 'A':
        prompt = prompts['sys_prompt_groupA']
    elif design == 'B':
        prompt = prompts['sys_prompt_groupB']
    else:
        print('design maybe error')
        prompt = prompts['sys_prompt_groupA']
    df = pd.DataFrame(risk_class).T
    df['ID'] = df.index.to_list()
    risk_class = re.sub(' +', ' ', df[['ID', 'Type', 'Variables']].to_markdown(index=False))
    messages = [
        {
            "role": "system", "content": prompt.render(
            risk_factor=risk_Factors, cancer=outcome, cohort=cohort,
            # RiskClass=risk_class,
            cohort_id=cohort_id
        )
        },
        {
            "role": "user", "content": prompts['group_info'].render(
            content=chunk)
        }
    ]
    respone = {}
    for i in range(cycle):
        try:
            respone = await async_respone(
                messages, model, temperature=0.01, top_p=0.7, max_tokens=max_tokens, cycle=5)
            if respone.get('Run status', '') == "System Error":
                return respone
            for k, v in respone.items():
                if k:
                    for _k in ['CohortID', 'Sex', "CancerOutcome", "ExposedGroup", "NonExposedGroup", "RiskEstimates"]:
                        assert _k in v.keys()
                    for _k in ["Exp_Definition", "Exp_Cases", "Exp_NonCases"]:
                        assert _k in v['ExposedGroup'].keys()
                    for _k in ["NEP_Definition", "NEP_Cases", "NEP_NonCases"]:
                        assert _k in v['NonExposedGroup'].keys()
            return respone
        except Exception as e:
            print(f"[{i}/{cycle}] Worker failed with error: {e}")
            if i == cycle - 1:
                respone = {"Run status": "System Error", "Error message": str(e)}
            return respone


async def group_check_agent(
        chunk, outcome, risk_Factors, cohort, cohort_id, risk_class, design, model, lang, max_tokens, cycle=5, rag=None):
    if lang == 'en':
        from .prompts_en import prompts
    else:
        from .prompts_zh import prompts
    if design == 'A':
        prompt = prompts['sys_prompt_groupA']
    elif design == 'B':
        prompt = prompts['sys_prompt_groupB']
    else:
        print('design maybe error')
        prompt = prompts['sys_prompt_groupA']
    df = pd.DataFrame(risk_class).T
    df['ID'] = df.index.to_list()
    risk_class = re.sub(' +', ' ', df[['ID', 'Type', 'Variables']].to_markdown(index=False))
    messages = [
        {
            "role": "system", "content": prompt.render(
            risk_factor=risk_Factors, cancer=outcome, cohort=cohort, RiskClass=risk_class, cohort_id=cohort_id
        )
        },
        {
            "role": "user", "content": prompts['group_info'].render(
            content=chunk)
        }
    ]
    respone = {}
    for i in range(cycle):
        try:
            respone = await async_respone(
                messages, model, temperature=0.01, top_p=0.7, max_tokens=max_tokens, cycle=5)
            if respone.get('Run status', '') == "System Error":
                return respone
            for k, v in respone.items():
                if k:
                    for _k in ['CohortID', 'Sex', "CancerOutcome", "ExposedGroup", "NonExposedGroup", "RiskEstimates"]:
                        assert _k in v.keys()
                    for _k in ["Exp_Definition", "Exp_Cases", "Exp_NonCases"]:
                        assert _k in v['ExposedGroup'].keys()
                    for _k in ["NEP_Definition", "NEP_Cases", "NEP_NonCases"]:
                        assert _k in v['NonExposedGroup'].keys()
            return respone
        except Exception as e:
            print(f"[{i}/{cycle}] Worker failed with error: {e}")
            if i == cycle - 1:
                respone = {"Run status": "System Error", "Error message": str(e)}
                return respone
