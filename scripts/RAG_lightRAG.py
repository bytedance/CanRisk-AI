import asyncio
import numpy as np
from openai import AsyncOpenAI
from lightrag.utils import EmbeddingFunc
from lightrag import LightRAG, QueryParam
from lightrag.kg.shared_storage import initialize_pipeline_status
from lightrag.llm.openai import openai_complete_if_cache, openai_embed
from .llm_info import model_embed, model_rag, api_key, chat_base_url
from lightrag.utils import setup_logger

setup_logger("lightrag", level="INFO")

entities = ["Cancers", "Risk Factors", "Risk Values", "Cohort Information", "Adjustment Methods", "Timeline", "Groups",
            "Demographics", "Geography", "Data Sources", "Risk Groups", "Control Groups", "Population", "Events",
            "References", "Methods", "Results", "Discussion", "Conclusion", "Acknowledgments", 'Author Information']


async def llm_model_func(
        prompt, system_prompt=None, history_messages=[], keyword_extraction=False, **kwargs
) -> str:
    return await openai_complete_if_cache(
        model_rag,
        prompt,
        system_prompt=system_prompt,
        history_messages=history_messages,
        api_key=api_key,
        base_url=chat_base_url,
        **kwargs
    )


async def embedding_func(texts: list[str]) -> np.ndarray:
    return await openai_embed(
        texts,
        model=model_embed,
        api_key=api_key,
        base_url=chat_base_url,
    )


# async def embedding_func(
#     texts: list[str],
#     model: str = embedding_model,
#     base_url: str = chat_base_url,
#     api_key: str = chat_api_key,
# ) -> np.ndarray:
#
#     openai_async_client = (
#         AsyncOpenAI(
#             # default_headers=default_headers,
#             api_key=api_key)
#         if base_url is None
#         else AsyncOpenAI(
#             base_url=base_url,
#             # default_headers=default_headers,
#             api_key=api_key
#         )
#     )
#     response = await openai_async_client.embeddings.create(
#         model=model, input=texts, encoding_format="float"
#     )
#     return np.array([dp.embedding for dp in response.data])


async def initialize_rag(WORKING_DIR):
    rag = LightRAG(
        working_dir=WORKING_DIR,
        llm_model_func=llm_model_func,
        embedding_func=EmbeddingFunc(
            embedding_dim=4096,
            max_token_size=8192,
            func=embedding_func
        ),
        # enable_llm_cache=False,
        # embedding_batch_num=12,
        # chunk_token_size=4096,
        addon_params={
            "entity_types": entities
        }
    )

    await rag.initialize_storages()
    await initialize_pipeline_status()

    return rag

async def rag_search(rag, query, mode="hybrid", top_k=5):
    chunks = rag.query(query, param=QueryParam(mode=mode, top_k=top_k, only_need_prompt=True))
    chunks = chunks.split('---Data Sources---')[1].split('---Response Requirements---')[0].strip()
    return chunks