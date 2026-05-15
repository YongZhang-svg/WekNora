---
name: academic-writing
description: 用于论文写作、Related Work、Methodology、实验分析、学术综述、研究报告等正式学术场景。适用于严谨、结构化、低口语化写作任务。
---

# Academic Writing Skill

## 1. 适用场景
用于论文、研究计划、综述、实验分析、方法描述、结果讨论、学术表达优化。

## 2. 任务目标
- 保持学术严谨
- 建立清晰论证链
- 保持术语一致
- 避免主观和夸张表达
- 让结论能被证据支撑

## 3. 输入理解
重点识别：
- 论文哪个部分
- 是否需要改写已有段落
- 是否需要更正式、更学术的表达
- 是否需要强调结果、限制或贡献

## 4. 输出模板
### 论文通用结构
1. Introduction
2. Related Work
3. Methodology
4. Experiments
5. Results
6. Discussion / Limitations
7. Conclusion

### 段落写作模板
- Claim
- Evidence
- Interpretation
- Limitation

## 5. Hard Rules
- 每个结论尽量对应证据
- 避免“非常重要”“显著领先”这类无证据形容
- 避免口语化和宣传式措辞
- 避免“我们认为”式弱化表达，改为直接陈述或规范学术表达
- 引用、数字、实验结果不得随意改写
- 结果和讨论要分开，不要混成一段

## 6. Examples
### Example 1
**User:** 优化 related work 段落。  
**Output:**  
- 按主题聚类相关工作
- 说明已有方法的不足
- 引出本文方法的定位

### Example 2
**User:** 写实验结果分析。  
**Output:**  
- 先写结果现象
- 再解释原因
- 最后说明局限与启示

## 7. Preferred Writing Style
- 正式
- 克制
- 逻辑清晰
- 证据优先


## 8. Few-shot Examples

### Few-shot 1 — Related Work
**User Request**
帮我写 related work。

**Expected Behavior**
- 按主题组织
- 不是逐篇论文罗列
- 指出研究缺口

**Preferred Pattern**
- Topic A
- Topic B
- Existing limitations
- Our positioning

---

### Few-shot 2 — 实验分析
**User Request**
分析实验结果。

**Expected Behavior**
- 先写观察
- 再写原因
- 最后写限制

**Avoid**
- “效果非常好”
- “显著领先”但无数据
