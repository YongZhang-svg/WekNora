# Diagram Reference Guide

## 支持的图表类型

| 类型 | 最佳用途 | Mermaid 语法 |
|---|---|---|
| mindmap | 知识结构、总结汇报、读书笔记 | `mindmap` |
| flowchart | 流程、决策、逻辑分支 | `flowchart TD/LR` |
| graph LR | 架构、模块关系 | `graph LR` |
| sequenceDiagram | 交互时序、请求响应 | `sequenceDiagram` |
| swimlane | 跨角色/跨部门协作流程 | `flowchart TD` + subgraph |
| timeline | 项目里程碑、时间节点 | `timeline` |
| funnel | 筛选/转化流程 | `flowchart TD` 渐窄 |
| causal chain | 根因分析、因果传导 | `flowchart LR` |

## Mind map 模式

```mermaid
mindmap
  root((Topic))
    Branch A
      Detail A1
      Detail A2
    Branch B
      Detail B1
    Branch C
      Detail C1
      Detail C2
      Detail C3
```

## Flowchart 模式

```mermaid
flowchart TD
    A[Start] --> B[Process]
    B --> C{Decision}
    C -->|Yes| D[Success]
    C -->|No| E[Retry]
    E -.->|feedback| B
```

## Architecture 模式

```mermaid
graph LR
    User -->|main_flow| Gateway
    Gateway -->|branch_out| ServiceA
    Gateway -->|branch_out| ServiceB
    ServiceA -->|main_flow| Database
    ServiceB -->|main_flow| Cache
```

## Sequence 模式

```mermaid
sequenceDiagram
    participant U as User
    participant A as Agent
    participant S as SkillManager
    U->>A: Send request
    A->>S: Load skill
    S-->>A: Return instructions
    A-->>U: Send response
```

## Swimlane 模式

```mermaid
flowchart TD
    subgraph 用户侧
        A[提交需求] --> B[确认方案]
    end
    subgraph 开发侧
        C[技术评审] --> D[开发实现]
        D --> E[测试验收]
    end
    subgraph 运维侧
        F[部署上线] --> G[监控运维]
    end
    B --> C
    E --> F
```

## Timeline 模式

```mermaid
timeline
    title 项目里程碑
    2024-Q1 : 需求调研 : 竞品分析
    2024-Q2 : 方案设计 : 架构评审
    2024-Q3 : 开发测试 : 集成测试
    2024-Q4 : 上线运维 : 效果评估
```

## Funnel 模式

```mermaid
flowchart TD
    A[全部用户] --> B[访问落地页]
    B --> C[注册账号]
    C --> D[完成首单]
    D --> E[成为复购用户]
```

## Causal chain 模式

```mermaid
flowchart LR
    A[服务超时] --> B[线程池满]
    B --> C[数据库慢查询]
    C --> D[索引缺失]
    D --> E[数据量突增]
```

## 连线类型速查

| 类型 | 含义 | Mermaid | 使用场景 |
|---|---|---|---|
| main_flow | 主路径推进 | `A --> B` | 核心流程 |
| branch_out | 一处分多支 | `A --> B; A --> C` | 条件分支 |
| fan_in | 多处汇一 | `B --> D; C --> D` | 结果合并 |
| feedback | 反馈/回退 | `D -.-> A` | 循环/重试 |
| convergence | 收敛 | `B --> D; C --> D` + 标注 | 方案收敛 |

## 节点数量参考

| 图类型 | 建议最大节点数 | 超过时建议 |
|---|---|---|
| mindmap | 一级 4-6, 总计 ≤30 | 拆分为多张子图 |
| flowchart | ≤15 | 拆分为多阶段子图 |
| architecture | ≤12 | 按模块拆分 |
| swimlane | 泳道 ≤4, 每道 ≤5 步 | 拆分为概览+详图 |
| timeline | ≤10 节点 | 按阶段拆分 |

## 输出格式选择

| 用户需求 | 推荐输出 |
|---|---|
| 快速查看 | 纯 Mermaid 代码 |
| 汇报展示 | 结构化提纲 + Mermaid |
| XMind 编辑 | Markdown 大纲（# 层级） |
| 文档嵌入 | Mermaid 代码 + 渲染后 PNG |
| 动效/演示 | flow_spec + motion_timeline（需工具链支持） |
