# CanRIsk-AI: An AI pipline for CanRisk-DB

---

[English](./README.md) | [简体中文](./README_zh.md)
## introduction

[CanRisk-DB](https://www.canrisk-ai.com/) is a cancer risk factor database built on AI,
while CanRisk-AI is the pipeline for implementing this database.
CanRisk-DB is accessible via a web browser. The overall pipeline of CanRisk-AI includes abstract filtering,
full-text filtering, and multi-agent information extraction.
The entire pipeline is as follows:
![img.png](imgs/img.png)

## install

---
The code of this project is built on Python, and Python 3.10 or a higher version is required.

### Dependencies

- volcengine-python-sdk

```
pip install -U 'volcengine-python-sdk[ark]'
```

- pandas
- numpy
- cv2
- jinja2
- lightrag (1.2.7, Please note that LightRAG is updated very frequently,
  and there are significant differences in interfaces between versions.
  Newer versions of LightRAG may render the script incompatible)
- nest_asyncio
- openai
- json_repair
- llm2json

## step

0. About LLM  
   All large model calls in this project are from Volcengine's platform and are implemented using Ark.
   For relevant information, please visit [Volcano Ark](https://www.volcengine.com/product/ark).

1. Abstract screening
    - The abstracts in this project are sourced from PubMed, Cochrane, and Embase.
      The search strategy information will be presented in the supplementary materials after the article is published.
    - The input file is in `tsv` format and does not require column names.
      The first column contains unique abstract IDs (which can be defined by the user),
      and the second column contains the abstract content.
   ```shell
   python 1.Abstract_filter.py input_file.tsv output_file.tsv
   ```

2. pdf parsing
    - There are many excellent PDF parsing tools available,
      such as [Dolphin](https://github.com/bytedance/Dolphin), [docling](https://github.com/docling-project/docling),
      [LlamaParse](https://cloud.llamaindex.ai/), and more.
      Due to constraints on computing resources and considerations regarding the utilization of intermediate files (
      especially figures in literature),
      this study adopts [MinerU](https://github.com/opendatalab/MinerU) for full-text parsing.

3. full-text screening
   - The input file is in `tsv` format and does not require column names. The first column contains unique paper IDs (which can be defined by the user), and the second column contains the file paths of the PDF parsed files corresponding to the literature.
   - Note that the PDF parsed files should be in TXT format (Markdown format is also acceptable).
   ```shell
   python 2.Full_text_filter.py input_file.tsv output_file.tsv
   ```

4. multi agent for CanRisk-DB
   -i: Input directory, which supports the output results after MinerU parsing
   -o: Output directory
   -r: RAG directory, which supports the location of the knowledge graph constructed by LightRAG. If it does not exist, it will be automatically created in the output directory
   ```shell
   python 3.Multi_agent.py -i input_dir -o output_dir -r rag_dir
   ```

## citation

--- 
The related work has been accepted by ESMO, and the academic paper is currently under review.

## License

---
This project is licensed under the MIT License - see the LICENSE file for details.

