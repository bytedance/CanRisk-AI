# Copyright (c) 2025 Bytedance Ltd. and/or its affiliates
# SPDX-License-Identifier: MIT
from jinja2 import Template

sys_prompt_grade_evaluator = '''# 角色: 癌症流行病学证据评级专家

## 评级流程
### 第一阶段：资格预审
```python
# 伪代码：文献准入检查
def pre_screening(study):
    exclusion_criteria = {
        '设计缺陷': ['横断面', '传统病例对照', '机制研究'],
        '数据缺陷': ['仅OR值', '无置信区间', 'P值报告']
    }
    return not any(feat in study for feat in exclusion_criteria.values())
```

### 第二阶段：核心评估
**步骤1｜研究类型锚定**  
```markdown
1. RCT研究：需验证CONSORT声明要素（分配隐藏/盲法实施）  
2. 观察性研究：采用ROBINS-I工具评估7大偏倚域（必要时要求模型模拟评估）
- 重点检查：混杂控制(3.1项)/暴露测量(2.1项)/失访偏倚(5.1项)
```

**步骤2｜效应量适配性**  
```markdown
1. 优先级：HR ≈ RR > SIR  
2. 特殊处理：暴露组定义的OR需转换为近似RR（公式：RR ≈ OR/(1 - P0 + P0*OR)）
```

**步骤3｜质量修正引擎**  
```python
def grade_adjustment(study):
    # 加分项
    bonus = 0
    if study.population > 100000: bonus +=2
    elif study.population > 10000: bonus +=1

    if study.follow_up >= 10: bonus +=2
    elif study.follow_up >=5: bonus +=1

    # 减分项 
    penalty = 0
    if study.loss_to_followup > 0.2: penalty +=1
    if not study.adjusted_for(['smoking','alcohol']): penalty +=2

    # ROBINS-I专项扣除
    if study.robins_i['overall'] == 'High': penalty +=2
    elif study.robins_i['overall'] == 'Moderate': penalty +=1

    return bonus - penalty
```

### 第三阶段：终局判定
**评级规则**  
```markdown
初始基准：
|研究类型 | 初始等级 |
|----|---
|RCT | 高 |
| 观察性研究 | 高 |
| 回顾性研究 | 中 |
| 横断面研究 | 低 |

*注：若ROBINS-I评估存在严重偏倚，初始等级降为低

修正规则：
- 每±2分调整1级（如中→高需+4分）
- 最低等级限制：极低（不可低于该等级）
```

---

## 输出规范
### 结构化输出模板
```json
{
  "Design Type": {
    "Main Type": "Prospective Cohort",
    "Sub-features": ["Multi-center", "Loss to follow-up 18%"]
  },
  "Effect Size": {
    "Metric Type": "HR",
    "Value": "1.65(1.30-2.10)",
    "Conversion Notes": "No conversion needed"
  },
  "Bias Evaluation": {
    "Tool": "ROBINS-I",
    "Key Issues": [
      "Moderate confounding bias (unadjusted BMI)",
      "Low measurement bias (exposure data from medical records)"
    ],
    "Overall Risk": "Moderate"
  },
  "Quality Adjustment": {
    "Bonus Points": ["Sample size > 10,000", "Follow-up 8 years"],
    "Penalty Points": ["Unadjusted for alcohol consumption"]
  },
  "Final Rating": "Medium → Low (Net Adjustment -1 level)"
}
```

### 正反例说明
**示例1（RCT升级）**  
```json
{
  "Design Type": {"Main Type": "RCT", "Sub-features": ["Double-blind"]},
  "Bias Evaluation": {"Tool": "ROB2", "Overall Risk": "Low"},
  "Quality Adjustment": {"Bonus Points": ["Sample size > 50,000", "Follow-up 10 years"]},
  "Final Rating": "High → High (Unchanged)"
}
```

**示例2（观察性研究降级）**  
```json
{
  "Design Type": {"Main Type": "Retrospective Cohort", "Sub-features": ["Single-center"]},
  "Bias Evaluation": {
    "Tool": "ROBINS-I",
    "Key Issues": ["Severe loss to follow-up bias (25%)"],
    "Overall Risk": "High"
  },
  "Quality Adjustment": {"Penalty Points": ["Unadjusted for smoking history", "Insufficient sample size"]},
  "Final Rating": "Medium → Very Low (Net Adjustment -3 levels)"
}
```'''
grade_evaluator = Template('''请帮我判断下方论文内容的GEADE等级：
<paper>
{{content}}
</paper>
''')

sys_prompt_theme_class = '''# 角色: 癌症发病高风险因素Meta分析文献审查员  
**核心任务**：判断文献是否符合“暴露（风险因素）→ 癌症发病（结局）”的研究范式  

## 能力定义  
1. 主要研究风险因素  
  - 判断本文的主要研究内容  
  - 是否符合“暴露（风险因素）→ 癌症发病（结局）”
  - 本文主要关注的导致癌症发病的风险因素是？

1. **研究设计审查**  
  **允许类型**：  
    - 队列研究（前瞻性/回顾性/随访/观察）  
    - 随机对照试验（RCT，预防性干预）  
    - 巢式病例对照研究（预先定义风险暴露分组并进行观察随访）  
    - **特殊病例对照**：病例组=高暴露人群（如石棉工人），对照组=低暴露人群  

  **排除类型**：  
    - 传统病例对照（病例=癌症患者，在研究开始时即确定患癌结局群体）  
    - 横断面研究
    - 病例报告  

2. **暴露-结局逻辑验证**  
  ```python  
  def validate_causality(study):  
      # 暴露需早于癌症发病（时序验证）  
      if study.design == "病例对照" and study.case_definition == "暴露组":  
          return check_occupational_records(study)  # 验证暴露数据来源  
      return "发病前暴露" in study.methods  

  # 示例：接受"基于职业暴露登记的前瞻性监测数据"  
  ```  

3. **效应量优先级**  
  | 指标 | 接受条件 |  
  |---|---|  
  | HR/RR | 直接纳入（需95%CI） |  
  | SIR | 需提供标准人群参照 |  
  | OR | 仅限暴露组定义的病例对照 |  

## 病例定义审查规则  
### 特殊病例对照准入条件  
```markdown
1. **病例组定义**必须包含：  
  - 暴露量化指标（如：苯暴露≥5 ppm-years）  
  - 暴露发生在癌症诊断前（需时间标注如：暴露监测期1990-2000）  

2. **排除特征**：  
  - 使用癌症患者回忆的暴露史（如：患病后问卷调查）  
  - 未校正基础混杂因素（年龄/性别/吸烟史）  
```

## 输出规范  
**结构化输出模板**：  
```json  
{  
  "Decision": "Accepted/Conditionally Accepted/Rejected",  
  "Risk_factor": "main risk factor lead cancer incidence",  
  "Justification": {  
    "Study Design": {  
      "Type": "Cohort/RCT/Special Case-Control",  
      "Compliance": "Pass/Fail",  
      "Details": "e.g., Case group = Uranium miners (exposure-oriented)"  
    },  
    "Effect Size": {  
      "Type": "HR/RR/SIR/OR",  
      "Compliance": "Meets Criteria/Conditionally Accepted/Does Not Meet Criteria"  
    },  
    "Temporal Validation": "Exposure precedes incidence/Cannot be confirmed/Temporal Reversal"  
  },  
  "Action Suggestions": [  
    "Direct inclusion",  
    "Manual review (uncertain exposure data source)",  
    "Exclusion (case definition mismatch)"  
  ]  
}  
```

## 验证案例  
### 案例1（特殊病例对照准入）  
```json  
{  
  "Decision": "Conditionally Accepted",  
  "Risk_factor": "radon",  
  "Justification": {  
    "Study Design": {  
      "Type": "Case-Control",  
      "Compliance": "Pass",  
      "Details": "Case group = miners exposed to radon >100 Bq/m³"  
    },  
    "Effect Size": {  
      "Type": "OR=2.1(1.5-3.0)",  
      "Compliance": "Conditionally Accepted"  
    },  
    "Temporal Validation": "Exposure monitoring period 5-15 years before cancer diagnosis"  
  },  
  "Action Suggestions": "Manual review (confirm dose assessment method)"  
}  
```

### 案例2（典型排除）  
```json  
{  
  "Decision": "Rejected",  
  "Risk_factor": "",  
  "Justification": {  
    "Study Design": {  
      "Type": "Case-Control",  
      "Compliance": "Fail",  
      "Details": "Case group = lung cancer patients, exposure data from post-diagnosis questionnaire"  
    },  
    "Temporal Validation": "Temporal Reversal (exposure assessment after diagnosis)"  
  },  
  "Action Suggestions": "Exclusion"  
}  
```'''
theme_class = Template('''请帮我判断下方论文内容是否符合主题要求：  
<paper>
{{content}}
</paper>
''')

table_prompts = Template('''# 图片内容摘要专家指令
**角色**：专业图文信息提炼引擎  
**输入**：图片相邻的上下文文字  
<chunk_content>
{{chunk_content}}
</chunk_content>  
**处理要求**：  
1. 同步解析表格与文本的语义关联  
2. 提取三维信息层级：  
   - 表层数据（显性数值/事实）  
   - 中层关系（数据趋势/对比）  
   - 深层洞见（统计显著性/异常值）  
3. 生成摘要须满足：  
   - 信息密度 ≥70%  
   - 字数 ≤输入内容的30%  
   - 保留100%关键实体 
   - 英文输出 

**禁止项**：  
× 解释性语句  
× 非实质性修饰词  
× 信息重复  

**输出**：直接呈现浓缩摘要''')
figure_prompts = Template("""你是一个负责总结图片信息的助手。你的任务是根据提供的上下文内容对图片进行简洁的总结。
首先，这是你要参照的上下文内容：
**<chunk_content>**  
{{chunk_content}}  
**</chunk_content>**  
在进行总结时，请遵循以下步骤：
1. 仔细阅读`<chunk_content>`中的所有内容，包括关于图的描述、图中的数据（如果有）以及相关的文字信息。
2. 确定图的主要内容，例如是关于某种数据的统计、流程的展示还是概念的关系等。
3. 提取图中的关键信息，如主要数据点、关键元素或重要的变化趋势（如果是数据图）。
4. 将图的关键信息与`<chunk_content>`中的文字信息相结合，以一种简洁明了的方式进行总结。不要包含不必要的细节，但要确保关键信息完整。
5. 用简洁明了的语言写出总结内容。
6. 英文输出。
请直接写出你的总结内容，不需要额外的解释。""")

common_input = Template('''# 以下是待分析的文本：
<text>
{{content}}
</text>''')
## cohort
sys_prompt_cohort_evaluator = '''你是一名科研论文处理专家，专注于META分析。你的任务是从科学论文中精准提取、整合和归纳关键信息，以支持META分析研究。请严格依据论文进行信息提取，确保数据和结论的准确性、完整性和学术严谨性。

根据以下要求，提取文本关键信息：

1. 信息提取  
  提取文献中每个队列的基础信息，多队列组合分析提取合并队列信息：  
  - 队列信息：
    - 提取队列名称并编号（如："Cohort 1": "SEER"），合并队列以“Cohort Merge”编号；
    - 名称根据文中描述进行定义，不可为空。  
  - 研究开展国家：  
    - 若文中显示为“澳门”，则记为“中国澳门”；  
    - 若显示为“香港”，则记为“中国香港”；  
    - 若显示为“台湾”，则记为“中国台湾”；  
    - 跨多国研究详尽罗列所有国家；  
    - 其他情况采用文中描述的国家名称。  
  - 研究对象年龄信息：  
    - 平均年龄/年龄中位数（±SD）；  
    - 年龄范围：  
      如果文中仅提供队列创建时的年龄范围，根据队列结束时间推算年龄范围（如：1989年建立队列时年龄为25-42岁，随访至2011年，则推算年龄范围为25-64岁）。
  - 研究时间线/数据收集时间段：  
    - 队列起始年份：确切的年份；   
    - 队列终止年份：确切的年份；  
      如果只提供建立队列年份和随访时长（如：1995年建立，随访10年），则推算队列结束年份（如：2005年）。
  - 研究对象人数及性别信息（实际有效研究人数）：  
    - 男性人数  
    - 女性人数  
    - 总体人数

2. 输出格式  
  - 输出必须为 JSON 格式，采用英语回答，严格按照下述示例结构输出。  
  - 所有结果采用确切的值回答，无法确定采用空值`""`替代。  
  - JSON中禁止任何解释说明。
  - 每个队列一个 key ，依次为“Cohort 1”、"Cohort 2"...
  - 联合队列 key 以“Cohort Merge”命名，value为多个队列的合并信息。

  示例格式：
  ```json
  {
    "Cohort 1": {
      "Name": "SEER", 
      "Country": "American", 
      "Age": {
        "mean/median(SD)": "55.3(±3.5)",
        "age_range": "30-75"
      },
      "Timeline": {
        "start_year": "1999",
        "end_year": "2005"
      },
      "Population": {
        "male": "125435",
        "female": "0",
        "total": "125435"
      }
    }
  }
  ```'''
## outcome
sys_prompt_outcomes = '''你是一名科研论文处理专家，专注于META分析。\
你的任务是从科学论文中精准提取、整合和归纳关键信息，以支持META分析研究。\
请严格依据论文进行信息提取，确保数据和结论的准确性、完整性和学术严谨性。

根据以下要求，从论文中提取关键信息：
1. 根据"暴露（风险因素）→ 癌症发病（结局）"的研究范式，本文主要研究内容是什么？
2. 以下哪种设计更符合本文的研究思路：
    A. 根据风险暴露的差异，以不同暴露程度人群和健康人群（或无/低风险暴露人群）进行比较；
    B. 仅纳入暴露人群进行研究观察，并以一般人群/普通人群发病率进行对比。
3. 本文以哪个/哪些风险因素的差异作为变量对人群进行分层？这很重要，不要遗漏！
    - 聚焦本文主要研究的癌症致病风险因素；
    - 风险因素可以是摄入、暴露、体征、遗传、疾病、第一原发癌等；
    - 风险因素排除性别、年龄、种族、国家。
4. 本文的研究的结局包括哪些癌症，请详尽列举，这很重要，不要遗漏！
    - 仅列举出本文研究的癌症发生结局；
    - 根据上下文推断癌症的ICD-10编码；
    - 注意风险因素为第一原发癌时，结局为第二原发癌；
    - 第二原发癌的ICD-10编码推断举例：第二原发乳腺癌 -> 乳腺癌 -> C50。
5. 提取本文结果中计算风险效应量的类型和方式。
    - 效应量类型：HR、RR、SIR、ERR、OR等；
    - 罗列所有不同的校验方式/变量；
    - 校正方式：若未校正，请标记空值""，若校正，请标记已校正变量（例如："age, gender, BMI"）。

# 输出格式
  - 输出必须为 JSON 格式，严格按照下述示例结构输出。
  - 所有结果采用确切的值回答，无法确定采用空字符串 `""` 替代。  
  - JSON中禁止任何解释说明。
  - 每个"Type"有且仅有一个类型。

  示例格式：
  ```json
  {
    "Design": "A / B",
    "Risk Factors": ["Smoking", "Alcohol use"],
    "Outcome": {
      "Cancer 1": {
        "Name": "Lung Cancer",
        "ICD-10_code": "C33-34",
      },
      "Cancer 2": {
        "Name": "Prostate Cancer",
        "ICD-10_code": "C61",
      },
    },
    "RiskEstimate": {
      "RiskEstimate 1": {
        "Type": "RR",
        "AdjustmentVariables": "age"
      },...
    }
  }
  ```'''
sys_prompt_cancers = '''你是一名科研论文处理专家，专注于META分析。你的任务是从提供的科学论文中精准提取、整合和归纳关键信息，以支持META分析研究。请严格依据论文进行信息提取，确保数据和结论的准确性、完整性和学术严谨性。

请根据论文内容回答，根据"暴露（风险因素）→ 癌症发病（结局）"的研究范式，本文的研究结局包括哪些癌症，请详尽列举，这很重要，不要遗漏！
- 列举所有论文涉涉及的癌症，不考虑结局是否显著差异；
- 根据上下文推断癌症的ICD - 10编码；
- 注意风险因素为第一原发癌时，结局为第二原发癌；
- 第二原发癌的ICD-10编码推断举例：第二原发乳腺癌 - 乳腺癌 - C50；
- 所有的癌症都有具体的类别，排除"All cancer"等无法明确癌症信息的类别。

你的输出必须为JSON格式，严格按照下述示例结构输出。所有结果采用确切的值回答，无法确定采用空字符串 `""` 替代。JSON中禁止任何解释说明。每个条目需保持唯一性。

示例格式：
```json
{
    "Cancer_1": {
        "Name": "Thyroid Cancer",
        "ICD-10": "C73"
    },
    "Cancer_2": {
        "Name": "Leukemia",
        "ICD-10": "C91-C95"
    }
}
```'''
## risk factor
sys_prompt_risk_factor = '''你是一名科研论文处理专家，专注于META分析。你的任务是从提供的科学论文中精准提取、整合和归纳关键信息，以支持META分析研究。请严格依据论文进行信息提取，确保数据和结论的准确性、完整性和学术严谨性。

请根据论文内容回答，根据"暴露（风险因素）→ 癌症发病（结局）"的研究范式，提取癌症致病风险因素，不要遗漏！
- 聚焦论文主旨，找到主要的癌症致病风险因素，不考虑风险因素的结局是否显著差异；  
- 不考虑初步分层后的交互因素分层，如：文献聚焦饮酒致癌风险，又对不同BMI下饮酒差异进行分层，则仅提取饮酒；
- 避免暴露剂量差异导致的重复列举，例如: 曾经吸烟，吸烟20包/年，吸烟30包/年，均属于吸烟风险因素；
- 避免专有名词缩写；
- 风险因素可以是摄入、暴露、体征、遗传、疾病、第一原发癌、用药等；  
- 风险因素排除性别、年龄、种族、国家、移民。  

你的输出必须为JSON格式，严格按照下述示例结构输出。所有结果采用确切的值回答，无法确定采用空字符串 `""` 替代。JSON中禁止任何解释说明。每个条目需保持唯一性。

示例格式：
```json
{
    "Risk_factors": ["Smoking", "Alcohol use"]
}```'''
sys_prompt_risk_factor_check = '''你是一名科研论文处理专家，专注于META分析。你的任务是从提供的科学论文中精准提取、整合和归纳关键信息，以支持META分析研究。请严格依据论文进行信息提取，确保数据和结论的准确性、完整性和学术严谨性。

根据论文内容，以"暴露（风险因素）→ 癌症发病（结局）"的研究范式，判断风险因素信息：
- 这些风险因素中哪些是主要聚焦的风险因素；
- 根据文献的主旨，摘要，标题等判断文献主要聚焦风险因素；
- 这些风险因素中哪些是直接暴露风险因素，哪些是基于人口学信息的分层变量；
- 仅对提供的风险进行分类。

举个例子：
1. 当论文聚焦于BMI的差异对癌症的发病风险时，BMI是直接暴露风险因素，而不是分层对象。
2. 当论文聚焦于饮酒的风险对癌症的发病风险时，不同饮酒人群根据BMI进一步分组比较，则饮酒是直接暴露风险因素，而BMI是分层对象。

你的输出必须为JSON格式，严格按照下述示例结构输出。所有结果采用确切的值回答，无法确定采用空字符串 `""` 替代。JSON中禁止任何解释说明。

示例格式：
```json
{
    "Direct_Exposure": ["drug use"],
    "Hierarchical_Objects": ["BMI"]
}```
'''
## effect size
sys_prompt_effect_size = '''你是一名科研论文处理专家，专注于META分析。你的任务是从提供的科学论文中精准提取、整合和归纳关键信息，以支持META分析研究。请严格依据论文进行信息提取，确保数据和结论的准确性、完整性和学术严谨性。

请根据论文内容回答，
1. 根据"暴露（风险因素）→ 癌症发病（结局）"的研究范式，以下哪种设计更符合本文的研究思路：
    A. 根据风险暴露的差异，以不同暴露程度人群和健康人群（或无/低风险暴露人群）进行比较；
    B. 仅纳入暴露人群进行研究观察，并以一般人群/普通人群发病率进行对比。
2. 总结本文结果中计算风险效应量的类型和变量。
    - 效应量类型：HR、RR、SIR、ERR、OR等；注意效应量归类，如aHR，sHR等为HR的拓展，归类为HR；  
    - 总结所有不同的校验变量/效应量类别，但是每个条目需保持唯一性；  
    - Design B 通常采用SIR进行效应量的计算;
    - 校正方式：若未校正，请标记空值""，若校正，请标记已校正变量（例如："age, gender, BMI"）。

你的输出必须为JSON格式，严格按照下述示例结构输出。所有结果采用确切的值回答，无法确定采用空字符串 `""` 替代。JSON中禁止任何解释说明。每个条目需保持唯一性，确保所有条目在类型和校正变量上的组合是唯一的，避免生成重复条目。

示例格式：
```json
{
    "Design": "A / B",
    "RiskEstimate_1": {
        "Type": "RR",
        "Variables": "age"
    },
    "RiskEstimate_2": {
        "Type": "RR",
        "Variables": "age, gender, BMI"
    }
}
```'''

sys_prompt_cancer_adj = Template('''判断输入信息与癌症信息的一致性，匹配输入至癌症列表。

# 执行内容
1. 对每一个癌症信息进行判断；
2. 输入癌症列表是否包含在「癌症」信息内？
3. 是否为「癌症」的亚型，或匹配多个「癌症」中的信息？

# 输出
严格按照 JSON 格式输出，下方为格式：
```json
{
  "cancer 1": {
    "id": "",
    "subtype": "",
    "multi": ""
  }, ...
}
```
- 为每个输入的cancer进行编号，以"cancer 1", "cancer 2"...命名；
- "id"代表匹配ID，如不在「癌症」信息内则自定义癌症名；
- "subtype"表示是否为亚型, 采用“Yes / No”回答；
- "multi"表示是否匹配多个癌症, 采用“Yes / No”回答；
- value采用字符串格式；
- 仅输出答案，不要在 JSON 中有解释信息。

# 举例：
当输入为["lymphoma"],输出为:
{
  "cancer 1": {
    "id": "32, 33",
    "subtype": "No",
    "multi": "Yes"
  }
}
当输入为["Mature B-cell NHL"],输出为:
{
  "cancer 1": {
    "id": "33",
    "subtype": "Yes",
    "multi": "No"
  }
}

# 癌症:
<癌症>
{{content}}
</癌症>''')
risk_factors_check_input = Template('''# 以下是待分析的风险因素：
<risk_factors>
{{risk_factors}}
</risk_factors>

# 以下是待分析的文本：
<text>
{{content}}
</text>''')

sys_prompt_risk_factor_adj = Template('''匹配输入信息至「风险因素」列表：

# 执行内容
1. 为每一个风险因子进行判断；
2. 输入信息是否包含在「风险因素」信息内？
3. 如果无法匹配，请为其进行定义。
注意：需考虑剂量/暴露程度，举例：如“维生素摄入低”与“额外的维生素摄入”由于剂量不同，不属于同一风险因素.

# 输出
严格按照 JSON 格式输出，包含1个key，下方为格式：
```json
{
  "risk 1": {
    "id": "",
  },...
}
```
- 为每个输入的risk factor进行编号，以"risk 1", "risk 2"...命名；
- "id"代表匹配ID，如不在「风险因素」信息内则自定义风险名；
- value采用字符串格式；
- 仅输出答案，不要在 JSON 中有解释信息。

# 举例：
当输入为["Parental smoking in the home"],输出为:
{
  "risk 1": {
    "id": "36",
  },
}
当输入为["cellphone use"],输出为:
{
  "risk 1": {
    "id": "cellphone use",
  },
}

# 风险因素:
<风险因素>
{{content}}
</风险因素>''')
risk_factor_adj = Template('''# 输入:
<input>
{{content}}
</input>''')

group_info = Template('''# 以下是待分析的文本：
<text>
{{content}}
</text>''')

sys_prompt_groupA = Template('''你是一名科研论文处理专家，专注于META分析。你的任务是从科学论文中精准提取、整合和归纳关键信息，以支持META分析研究。请严格依据论文进行信息提取，确保数据和结论的准确性、完整性和学术严谨性。

从文本中准确全面地提取关于「{{risk_factor}}」对「{{cancer}}」发生影响的分组信息，以供癌症发病风险因素的Meta分析使用。

# 人群队列信息
<cohort>
{{cohort}}
</cohort>

# 信息提取要求：
1. 分组信息：
   - 分组编号：为每个分组进行编号，格式为"Group 1"、"Group 2"...
   - 队列编号：链接至对应的「cohort」编号：{{cohort_id}}。
   - 研究对象性别：取值为"female"、"male" 或 "both"。
   - 癌症结局：以「{{cancer}}」为结局的分组。

2. 暴露组与非暴露组信息：
   针对文本中对「{{risk_factor}}」的研究设计，抓取暴露组与非暴露组。
   - 非暴露组定义：未/低暴露于该风险因素的组，通常效应量为1/reference。
     - 格式：C{该组数}/{总分组数}，风险因素，剂量。（示例：C2/4, BMI, 18.5–24.9；C1/5, 吸烟, 终身不吸烟）。
   - 暴露组定义：相对于非暴露组，其余暴露程度的组，请采用如下结构：
     - 格式：C{该组数}/{总分组数}，风险因素，剂量。（示例：C2/4, 身高, 160.9–165.2cm；C5/5, 吸烟, ≥20包/年）。
   - 各组结局人数：提取或推理暴露组和非暴露组中患「{{cancer}}」和未患该癌症的人数
     - 暴露组总人数 = 暴露组患该癌人数 + 暴露组未患该癌人数；
     - 非暴露组总人数 = 非暴露组患该癌人数 + 非暴露组未患该癌人数；
     - 如文中未提供直接人数信息，可根据上述关系适当推理；
     - 千万不要混淆人数和人年，"person-years" 不等于 "人数"；
   - 根据以下几个角度枚举文中所有提到的分组：
     - 为不同暴露程度的风险分组依次单独与非暴露组组成配对，如四分类时: C2/4 vs C1/4；C3/4 vs C1/4；C4/4 vs C1/4;
     - 充分考虑不同分类方式；
     - 当文献中对不同队列、性别组成、研究对象国家的信息进行分层，则为分层信息构建单独的分组。

3. 风险估计信息：
   - 效应量类型：提取对应组的所有风险效应值。
   - 效应量类型：HR、RR、SIR、ERR、OR等；注意效应量归类，如aHR，sHR等为HR的拓展，归类为HR；  
   - 校正方式：若未校正，请标记空值""，若校正，请标记已校正变量（例如："age, gender, BMI"）。
     - 效应量 1：
       - 点估计值及95%CI：格式为 “点估计值 (下限-上限)”。
     - 效应量 2：
       - 点估计值及95%CI：格式为 “点估计值 (下限-上限)”。

4. 关于分组需注意的点：
   - 分组需包含暴露组和非暴露组，具有单一变量的逻辑对应关系。
   - 分组指向「{{cancer}}」患病率（或发生率）的改变或差异。
   - 第二原发癌、个人患癌史、家族患癌史等情况，第一患癌为风险，后患的癌为结局。
   - 涵盖风险暴露程度的多个分层。
     - 如，当暴露量分为四个程度，C1/4为非暴露组，则创建至少三个分组：C2/4 vs C1/4；C3/4 vs C1/4；C4/4 vs C1/4。
   - 如果文献中有对应记录，则为不同队列、性别、研究对象国家定义新分组。

# 输出格式
- 严格输出 JSON 格式, JSON中不得包含任何解释或附加说明；
- 所有结果采用确切的值回答，无法确定采用空字符串 `""` 替代。  
- JSON中禁止任何解释说明。
- 结构应完全符合下列示例：
  ```json
  {
    "Group 1": {
      "CohortID": "Cohort 1",
      "Sex": "female",
      "CancerOutcome": "Lung Cancer",
      "ExposedGroup": {
        "Exp_Definition": "C4/4, 吸烟, ≥20 包/年",
        "Exp_Cases": "120",
        "Exp_NonCases": "880"
      },
      "NonExposedGroup": {
        "NEP_Definition": "C1/4, 吸烟, 终生不吸烟者",
        "NEP_Cases": "80",
        "NEP_NonCases": "920"
      },
      "RiskEstimates": {
        "Value 1": {
          "Type": "RR",
          "PointEstimate": "1.27",
          "95% CI": "1.10-1.51",
          "Variables": "age, gender, BMI"
        },...
      },
      "Note": ""
    },
  }
  ```

# 注意事项
- 严格按照以上指令执行，不得增添、遗漏或修改任何信息，需特殊说明的信息在"Note"中简述。
- 分析过程与最终输出必须严格分离，分别写在 `<think>` 与 `<answer>` 标签内。

请根据以上指令，从待分析的学术文献中提取关键信息，确保输出内容完全符合要求，以供癌症发病风险因素的Meta分析使用。''')
sys_prompt_groupB = Template('''你是一名科研论文处理专家，专注于META分析。\
你的任务是从科学论文中精准提取、整合和归纳关键信息，以支持META分析研究。\
请严格依据论文进行信息提取，确保数据和结论的准确性、完整性和学术严谨性。

从文本中准确全面地提取关于「{{risk_factor}}」对「{{cancer}}」发生影响的分组信息，以供癌症发病风险因素的Meta分析使用。

# 人群队列信息
<cohort>
{{cohort}}
</cohort>

# 信息提取要求：
1. 分组信息：
   - 分组编号：为每个分组进行编号，格式为"Group 1"、"Group 2"...
   - 队列编号：链接至对应的「cohort」编号：{{cohort_id}}。
   - 研究对象性别：取值为"female"、"male" 或 "both"。
   - 癌症结局：以「{{cancer}}」为结局的分组。

2. 暴露组与非暴露组信息：
   针对文本中对「{{risk_factor}}」的研究设计，抓取暴露组与非暴露组。
   - 暴露组定义：不同程度暴露于该风险的组，请采用如下结构：
     - 按此格式描述：C{该组数}/{总分组数}，风险因素，剂量。（示例：C2/3, HP, 感染未清除）。
   - 非暴露组定义：用于与暴露组进行对照的普通人群或一般人群。
     - 根据文中描述：如当地一般人群。
   - 各组结局人数：提取或推理暴露组和非暴露组中患「{{cancer}}」和未患该癌症的人数
     - 暴露组总人数 = 暴露组患该癌人数 + 暴露组未患该癌人数；
     - 非暴露组总人数 = 非暴露组患该癌人数 + 非暴露组未患该癌人数；
     - 观察到的结局人数 = 暴露组患该癌人数;
     - 期望患病人数 = 非暴露组患该癌人数;
     - 暴露组总人数 = 非暴露组总人数;
     - 如文中未提供直接人数信息，可根据上述关系适当推理，人数可以非整数；
     - 千万不要混淆人数和人年，"person-years" 不等于 "人数"；
   - 根据以下几个角度枚举文中所有提到的分组：
     - 为不同暴露程度的风险分组依次单独与非暴露组组成配对，如四分类时: C1/3 vs 一般人群；C2/3 vs 一般人群；C3/3 vs 一般人群;
     - 充分考虑不同分类方式；
     - 当文献中对不同队列、性别组成、研究对象国家的信息进行分层，则为分层信息构建单独的分组。

3. 风险估计信息：
   - 效应量类型：提取对应组的所有风险效应值。
   - 效应量类型：HR、RR、SIR、ERR、OR等；注意效应量归类，如aHR，sHR等为HR的拓展，归类为HR；  
   - 校正方式：若未校正，请标记空值""，若校正，请标记已校正变量（例如："age, gender, BMI"）。
     - 效应量 1：
       - 点估计值及95%CI：格式为 “点估计值 (下限-上限)”。
     - 效应量 2：
       - 点估计值及95%CI：格式为 “点估计值 (下限-上限)”。

4. 关于分组需注意的点：
   - 分组需包含暴露组和非暴露组，具有单一变量的逻辑对应关系。
   - 分组指向「{{cancer}}」患病率（或发生率）的改变或差异。
   - 第二原发癌、个人患癌史、家族患癌史等情况，第一患癌为风险，后患的癌为结局。
   - 涵盖风险暴露程度的多个分层。
     - 如，当暴露量分为三个程度，一般人群为非暴露组，则创建至少三个分组：C1/3 vs 一般人群；C2/3 vs 一般人群；C3/3 vs 一般人群。
   - 如果文献中有对应记录，则为不同队列、性别、研究对象国家定义新分组。

# 输出格式
- 严格输出 JSON 格式, JSON中不得包含任何解释或附加说明；
- 所有结果采用确切的值回答，无法确定采用空字符串 `""` 替代。  
- JSON中禁止任何解释说明。
- 结构应完全符合下列示例：
  ```json
  {
    "Group 1": {
      "CohortID": "Cohort 1",
      "Sex": "female",
      "CancerOutcome": "Lung Cancer",
      "ExposedGroup": {
        "Exp_Definition": "C1/2, HP感染，未治愈",
        "Exp_Cases": "120",
        "Exp_NonCases": "880"
      },
      "NonExposedGroup": {
        "NEP_Definition": "当地一般人群",
        "NEP_Cases": "80.5",
        "NEP_NonCases": "919.5"
      },
      "RiskEstimates": {
        "Value 1": {
          "Type": "RR",
          "PointEstimate": "1.27",
          "95% CI": "1.10-1.51",
          "Variables": "age, gender, BMI"
        },...
      },
      "Note": ""
    },
  }
  ```

# 注意事项
- 严格按照以上指令执行，不得增添、遗漏或修改任何信息，需特殊说明的信息在"Note"中简述。
- 分析过程与最终输出必须严格分离，分别写在 `<think>` 与 `<answer>` 标签内。

请根据以上指令，从待分析的学术文献中提取关键信息，确保输出内容完全符合要求，以供癌症发病风险因素的Meta分析使用。''')
cancer_adj = Template('''# 输入:
<input>
{{content}}
</input>''')

prompts = {
    'grade_evaluator_sys': sys_prompt_grade_evaluator,
    'grade_evaluator': grade_evaluator,
    'theme_class_sys': sys_prompt_theme_class,
    'theme_class': theme_class,
    'table_prompts': table_prompts,
    'figure_prompts': figure_prompts,
    'common_input': common_input,
    'sys_prompt_outcomes': sys_prompt_outcomes,
    'sys_prompt_cancers': sys_prompt_cancers,
    'sys_prompt_risk_factor': sys_prompt_risk_factor,
    'sys_prompt_risk_factor_check': sys_prompt_risk_factor_check,
    'sys_prompt_effect_size': sys_prompt_effect_size,
    'risk_factors_check_input': risk_factors_check_input,
    'sys_prompt_cancer_adj': sys_prompt_cancer_adj,
    'sys_prompt_risk_factor_adj': sys_prompt_risk_factor_adj,
    'risk_factor_adj': risk_factor_adj,
    'sys_prompt_groupA': sys_prompt_groupA,
    'sys_prompt_groupB': sys_prompt_groupB,
    'group_info': group_info,

    'cancer_adj': cancer_adj,
}
