---
name: meeting-summary
description: 用于生成会议纪要、讨论总结、行动项整理、决策记录等结构化会议文档。
---

# Meeting Summary Skill

## 1. 适用场景
用于会议纪要、讨论总结、项目例会记录、行动项跟踪、决策记录。

## 2. 任务目标
- 记录“发生了什么、决定了什么、谁来做、什么时候做”
- 避免流水账
- 让会议结果可追踪、可执行

## 3. 输入理解
先判断会议类型：
- 例会
- 评审会
- 决策会
- 沟通会
- 项目推进会

## 4. 输出模板
### 标准模板
1. 会议背景
2. 核心讨论
3. 关键决策
4. Action Items
5. 责任人
6. 时间节点

### 会议纪要增强模板
- 议题
- 讨论要点
- 结论 / 决策
- 待办事项
- Owner
- Deadline

## 5. Hard Rules
- 必须提取决策和待办
- 必须尽量标明责任人和时间节点
- 不把讨论过程写成长篇转录
- 同类观点合并表达
- 若没有明确决策，应标注“待确认”
- 用列表优先于长段落

## 6. Examples
### Example 1
**User:** 整理一次项目周会纪要。  
**Output:**  
- 本周进展
- 当前阻塞
- 决策
- 待办
- 负责人
- 截止时间

### Example 2
**User:** 把会议内容整理成可执行纪要。  
**Output:**  
- 重点结论
- 风险
- 行动项
- 责任归属

## 7. Preferred Writing Style
- 简洁
- 结构化
- 可追踪
- 易执行


## 8. Few-shot Examples

### Few-shot 1 — 周会纪要
**User Request**
整理项目周会。

**Expected Behavior**
- 提炼重点
- 给 action items
- 标责任人和时间

---

### Few-shot 2 — 决策会
**User Request**
整理一次架构评审会。

**Expected Behavior**
- 分清讨论和决策
- 标注待确认事项
