---
name: technical-writing
description: 用于技术文档、系统设计、API文档、架构方案、开发规范、RFC等技术写作场景。
---

# Technical Writing Skill

## 1. 适用场景
用于 API 文档、架构说明、设计文档、RFC、变更说明、部署指南、迁移指南、开发规范。

## 2. 任务目标
- 让工程人员能直接执行
- 让接口、流程、约束写得准确
- 把抽象概念落成步骤和字段
- 避免模糊、比喻和不必要抒情

## 3. 输入理解
优先识别文档类型：
- API doc
- Architecture design
- RFC
- Change log
- Migration guide
- Deployment plan

## 4. 输出模板
### 通用结构
1. Background
2. Goals / Non-goals
3. Architecture
4. Workflow
5. Interfaces / APIs
6. Risks
7. Rollout / Migration
8. Conclusion

### RFC 模板
1. Problem
2. Proposal
3. Alternatives
4. Trade-offs
5. Implementation plan

## 5. Hard Rules
- 用明确术语，不写模糊表达
- 每个接口都要说明输入、输出、约束、错误或边界
- 如果有流程，必须写清顺序和条件
- 避免“快速、智能、灵活”这类空词
- 避免把技术文档写成宣传稿
- 如有版本、兼容性、迁移要求，必须单独说明

## 6. Examples
### Example 1
**User:** 写一个 API 文档。  
**Output:**  
- 概述
- 请求方法和路径
- 请求参数
- 响应示例
- 错误码
- 注意事项

### Example 2
**User:** 写架构说明。  
**Output:**  
- 背景
- 组件关系
- 数据流
- 关键设计
- 风险与取舍

## 7. Preferred Writing Style
- 准确
- 无歧义
- 可执行
- 结构稳定


## 8. Few-shot Examples

### Few-shot 1 — API 文档
**User Request**
写一个用户登录 API 文档。

**Expected Behavior**
- 明确 method/path
- 给请求参数
- 给响应示例
- 给错误码

---

### Few-shot 2 — RFC
**User Request**
写一个缓存重构 RFC。

**Expected Behavior**
- 说明问题
- 说明提案
- 写 trade-off
- 写 rollout plan
