---
name: rewrite-polish
description: 用于对已有文本进行润色、改写、扩写、压缩、正式化、学术化或商务化处理。适用于提升文本可读性、逻辑性和专业度。
---

# Rewrite Polish Skill

## 1. 适用场景
用于已有文本的润色、改写、扩写、压缩、正式化、学术化、商务化、语气调整。

## 2. 任务目标
- 保持原意
- 提高可读性
- 调整语气和文体
- 减少重复
- 优化逻辑和节奏

## 3. 输入理解
重点识别用户想要的改写方向：
- 更正式
- 更学术
- 更商务
- 更简洁
- 更自然
- 更有说服力

## 4. 输出模板
### 通用流程
1. 保留核心意思
2. 重组表达顺序
3. 压缩重复信息
4. 优化衔接与节奏
5. 输出可直接使用的版本

### 常见改写模式
- concise
- formal
- academic
- business
- executive-summary
- persuasive

## 5. Hard Rules
- 不改变原始事实
- 不擅自增加新信息
- 不改变数字、专有名词、引用、代码
- 不把一句改成另一种意思
- 不为了“更像人”而丢失原文重点
- 若用户要求保留原风格，应尽量保留原风格

## 6. Examples
### Example 1
**User:** 把这段话改得更正式。  
**Output:**  
- 保留原意
- 改成正式书面语
- 压缩重复表达

### Example 2
**User:** 把这段内容压缩成摘要。  
**Output:**  
- 提取核心观点
- 去掉细节重复
- 保持逻辑顺序

## 7. Preferred Writing Style
- 准确
- 流畅
- 自然
- 不做无意义扩写


## 8. Few-shot Examples

### Few-shot 1 — 正式化
**User Request**
把这段话改正式一点。

**Expected Behavior**
- 保持原意
- 去口语化
- 压缩重复

---

### Few-shot 2 — 学术化
**User Request**
把这段改成论文风格。

**Expected Behavior**
- 用正式术语
- 减少主观表达
- 增强逻辑连接
