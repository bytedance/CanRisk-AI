# CanRIsk-AI: An AI pipline for CanRisk-DB

---
## introduction
CanRisk-DB是一个基于AI构建的癌症风险因素数据库，而CanRisk-AI则是实现该数据库的pipeline。[CanRisk-DB](https://www.canrisk-ai.com/)可通过网页访问。
CanRisk-AI的pipeline的整体包括摘要过滤，全文过滤，GRAG构建，多智能体构建。
整个pipeline如下：

![img.png](imgs/img.png)

## install

---
本项目代码基于python构建，请采用python 3.10及以上版本。

### Dependencies
- volcengine-python-sdk 
```
pip install -U 'volcengine-python-sdk[ark]'
```
- pandas
- json_repair
- llm2json
- jinja2
- lightrag (1.2.7, 注意，lightrag的更新很快，且版本间的接口也差异较大，新版本的lightrag会导致脚本不适用)

## step
0. 说明
本项目所有的大模型调用来自火山引擎的平台，采用Ark进行调用。相应信息请访问[火山方舟](https://www.volcengine.com/product/ark)。

1. 摘要过滤  
   - 本项目中的摘要来自PubMed、Cochrane和Embase。检索式信息将在文章发表后展示于附件中。
   - 输入文件为`tsv`格式，无需列名，第一列为无重复的摘要编号（可以自行定义），第二列为摘要内容。
   ```shell
   python 1.Abstract_filter.py input_file.tsv output_file.tsv
   ```
2. pdf解析  
   - 有很有优秀的pdf解析工具，如[Dolphin](https://github.com/bytedance/Dolphin), [docling](https://github.com/docling-project/docling),
[LlamaParse](https://cloud.llamaindex.ai/)等。受限于计算资源，以及对中间文件的利用（尤其是figures in literature），本研究采用[MinerU](https://github.com/opendatalab/MinerU)进行全文解析。
3. 全文过滤  
   - 输入文件为`tsv`格式，无需列名，第一列为无重复的摘要编号（可以自行定义），第二列为文献对应的 pdf 解析文件路径。
   - 注意 pdf 解析文件请采用txt格式（可以是markdown格式）。
   ```shell
   python 2.Full_text_filter.py input_file.tsv output_file.tsv
   ```
4. GRAG构建
5. 多智能体构建
6. 数据库构建


## citation

--- 
相关工作已经被ESMO接收，学术论文也正在审稿中。


## License

---
This project is licensed under the MIT License - see the LICENSE file for details.

