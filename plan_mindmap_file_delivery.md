# Mindmap 技能文件传递方案实施计划

## 1. 问题概述

mindmap 技能（`generate-mindmap`）在 sandbox 中执行 `generate_mindmap.py` 后，生成三种格式文件（HTML/SVG/XMind），保存在 `~/.openclaw/workspace/`（本地 sandbox 实际为 `/tmp/.openclaw/workspace/`）。但当前 `skill_execute.go` 只返回 stdout/stderr 文本到 `ToolResult`，不包含任何文件内容或下载信息，前端无法获取这些文件。

## 2. 现有架构分析

### 2.1 数据传递链路

```
LLM 调用 tool → ExecuteSkillScriptTool.Execute() → skillManager.ExecuteScript() → sandboxMgr.Execute()
    → ExecuteResult{Stdout, Stderr, ExitCode, ...}
    → ToolResult{Success, Output, Data, Error, Images}
    → act.go 发出 AgentToolResultData 事件
    → AgentStreamHandler.handleToolResult() → StreamEvent → SSE → 前端
```

### 2.2 关键结构体

| 结构体 | 文件 | 作用 |
|--------|------|------|
| `ExecuteResult` | `internal/sandbox/sandbox.go` | sandbox 执行结果，只有 Stdout/Stderr/ExitCode 等 |
| `ExecuteConfig` | `internal/sandbox/sandbox.go` | sandbox 执行配置，有 `OutputDir` 字段（Docker 专用） |
| `ToolResult` | `internal/types/agent.go` | tool 执行结果，有 `Images []string` 和 `Data map[string]interface{}` |
| `AgentToolResultData` | `internal/event/event_data.go` | SSE 事件数据，`Data` 字段传递结构化数据 |
| `FileService` | `internal/types/interfaces/file.go` | 文件存储服务，有 `SaveBytes` 方法返回 `provider://path` |
| `localFileService` | `internal/application/service/file/local.go` | 本地存储实现，`SaveBytes` 保存字节数据并返回 `local://path` |
| `ToolResultRenderer` | `frontend/.../ToolResultRenderer.vue` | 根据 `display_type` 选择渲染组件 |

### 2.3 前端渲染机制

- `AgentStreamDisplay.vue` 根据 `display_type` 决定使用 `ToolResultRenderer` 还是 raw output
- `ToolResultRenderer.vue` 根据 `display_type` 选择对应 Vue 子组件
- 当前已有的 `display_type`：`search_results`, `thinking`, `plan`, `database_query`, `web_search_results`, `web_fetch_results`, `grep_results`, `wiki_write_page` 等
- 没有 `display_type` 时，使用 fallback raw output 渲染

### 2.4 文件下载端点

- `/api/v1/files/presigned` — 已有的 presigned URL 下载端点
- `/api/v1/files?file_path=` — 已有的文件下载端点
- `FileService.GetFileURL()` — 返回下载 URL（local 模式返回 `local://path`，配置 externalURL 时返回 presigned HTTP URL）

### 2.5 Docker Sandbox 的 OutputDir

- `ExecuteConfig.OutputDir` 在 Docker sandbox 中会将宿主机目录挂载到容器 `/output`
- 但 `Manager.ExecuteScript()` 当前未设置 `OutputDir`
- 本地 sandbox 模式下 OutputDir 无意义（文件直接写在宿主机上）

## 3. 方案选择：文件存储 + 下载链接

### 核心思路

skill 脚本执行成功后，后端从 stdout 解析生成的文件路径，读取文件内容，通过 `FileService.SaveBytes()` 存储到持久化文件系统，然后将下载链接放入 `ToolResult.Data`，前端通过新增 `display_type = "skill_files"` 渲染组件展示下载卡片。

### 3.1 为什么选择此方案

| 对比项 | 方案A: FileService + 下载链接 | 方案B: ToolResult.Images (Base64) | 方案C: 直接内嵌内容 |
|--------|------------------------------|----------------------------------|-------------------|
| 大文件 | 无问题（XMind 可能几百KB） | SSE 事件过大，前端卡顿 | HTML 文件可能几MB |
| 可下载 | 原生支持 | 需前端额外转换 | 不支持 |
| 存储 | 持久化，可多次下载 | 一次性 | 一次性 |
| Docker sandbox | 需 OutputDir 挂载 | 需 OutputDir 挂载 | 需 OutputDir 挂载 |
| 实现复杂度 | 中等 | 低 | 低 |
| 用户体验 | 最佳（下载按钮、预览） | 中等（只看图片） | 差（大文本块） |

**结论**：方案A 最优，兼顾性能、可下载性和用户体验。

## 4. 详细实施步骤

### Task 1: 修改 `ExecuteSkillScriptTool`，注入 FileService 和 SessionID

**文件**：`internal/agent/tools/skill_execute.go`

**变更**：
1. `ExecuteSkillScriptTool` 结构体新增 `fileService interfaces.FileService` 和 `sessionID string` 字段
2. `NewExecuteSkillScriptTool()` 函数新增 `fileService` 和 `sessionID` 参数
3. 在 `Execute()` 方法中，sandbox 执行成功后，增加文件提取逻辑

```go
type ExecuteSkillScriptTool struct {
    BaseTool
    skillManager *skills.Manager
    fileService  interfaces.FileService  // 新增
    sessionID    string                   // 新增（用于 tenantID 查找）
}
```

**TenantID 获取**：从 `sessionID` 查找 session → 获取 TenantID（需要注入 sessionService 或在 Execute 中通过 ctx 传递 tenantID）

> **设计决策点**：tenantID 如何传入？
> - 选项1: ExecuteSkillScriptTool 注入 sessionService，从 sessionID 获取 tenantID
> - 选项2: 通过 context.Context 传递 tenantID（已有 `ctx.Value()` 机制）
> - 选项3: 在 NewExecuteSkillScriptTool 时传入 tenantID（但 agent 可能跨 session）
> 
> **推荐选项2**：在 act.go 的 tool 执行流程中，将 tenantID 写入 ctx，Execute 方法从 ctx 取出。

### Task 2: 在 `skill_execute.go` 的 Execute 中增加文件提取逻辑

**文件**：`internal/agent/tools/skill_execute.go`

**逻辑**：

1. sandbox 执行成功后（ExitCode=0），解析 stdout 中的文件路径
2. 文件路径格式为 `~/.openclaw/workspace/mindmap_xxx.ext`，本地 sandbox 实际为 `/tmp/.openclaw/workspace/mindmap_xxx.ext`
3. 逐个读取文件内容（`os.ReadFile`）
4. 通过 `FileService.SaveBytes()` 存储，获取 `provider://path` 格式的存储路径
5. 通过 `FileService.GetFileURL()` 获取下载 URL
6. 将文件信息列表放入 `ToolResult.Data`：

```go
// 提取的文件信息
type SkillFileInfo struct {
    FileName    string `json:"file_name"`    // mindmap_xxx.html
    Format      string `json:"format"`       // html/svg/xmind
    Size        int64  `json:"size"`         // 文件大小
    DownloadURL string `json:"download_url"` // 下载链接
    Description string `json:"description"`  // 用途描述
}

// ToolResult.Data 新增
resultData["display_type"] = "skill_files"
resultData["files"] = []SkillFileInfo{...}
```

**stdout 解析策略**：
- mindmap 脚本的 stdout 中包含文件路径信息（如表格中的路径）
- 使用正则或 JSON 解析从 stdout 提取路径
- **更可靠的方式**：让 skill 脚本以 JSON 格式输出文件路径（需修改 SKILL.md 的指令和 generate_mindmap.py）

> **设计决策点**：如何从 stdout 提取文件路径？
> - 选项A: 正则匹配 stdout 中的 `/tmp/.openclaw/workspace/xxx.ext` 路径
> - 选项B: 让脚本以 JSON 格式输出文件列表到 stdout 最后一行
> - 选项C: 使用标准化的 JSON 输出协议（新设计）
>
> **推荐选项B**：在 generate_mindmap.py 末尾增加一行 JSON 输出：
> ```json
> {"openclaw_output_files": [{"path": "/tmp/.openclaw/workspace/mindmap_xxx.html", "format": "html", "description": "浏览器打开"}, ...]}
> ```
> SKILL.md 中指导 LLM 传入 `--json-output` 参数，脚本在末尾输出此 JSON 行。
> `skill_execute.go` 从 stdout 最后一行解析此 JSON。

### Task 3: 处理 Docker Sandbox 模式下的文件输出

**文件**：`internal/agent/skills/manager.go`

**问题**：Docker sandbox 中文件写在容器内部，执行结束后容器销毁，文件丢失。

**解决**：在 `Manager.ExecuteScript()` 中设置 `ExecuteConfig.OutputDir`：

```go
func (m *Manager) ExecuteScript(ctx context.Context, skillName, scriptPath string, args []string, stdin string) (*sandbox.ExecuteResult, error) {
    // ...existing code...
    
    // 新增：为 Docker sandbox 设置 OutputDir
    // 创建宿主机临时目录，挂载到容器 /output
    outputDir, err := os.MkdirTemp("", "skill-output-*")
    if err != nil {
        return nil, fmt.Errorf("failed to create output dir: %w", err)
    }
    
    config := &sandbox.ExecuteConfig{
        Script:    file.Path,
        Args:      args,
        WorkDir:   basePath,
        Stdin:     stdin,
        OutputDir: outputDir,  // 新增：Docker sandbox 会挂载此目录到 /output
    }
    
    // ...existing code...
}
```

**同时修改 generate_mindmap.py**：让脚本支持 `--output-dir` 参数或环境变量 `OPENCLAW_OUTPUT_DIR`，在 Docker sandbox 时输出到 `/output` 目录。

> **注意**：本地 sandbox 模式下 OutputDir 不会被使用（文件直接写在宿主机上），但需要统一输出路径逻辑。

### Task 4: 修改 `generate_mindmap.py` 增加 JSON 输出协议

**文件**：`skills/preloaded/generate-mindmap/generate_mindmap.py`

**变更**：
1. 新增 `--json-output` 参数
2. 脚本在所有文件生成完成后，在 stdout 最后一行输出 JSON 格式的文件列表：

```python
if args.json_output:
    files_info = []
    for fmt, path in generated_files.items():
        files_info.append({
            "path": path,
            "format": fmt,
            "description": format_descriptions.get(fmt, "")
        })
    print(json.dumps({"openclaw_output_files": files_info}))
```

**文件**：`skills/preloaded/generate-mindmap/SKILL.md`

**变更**：在 SKILL.md 的执行指令中，要求 LLM 在调用 `execute_skill_script` 时添加 `--json-output` 参数：

```markdown
python3 {baseDir}/generate_mindmap.py \
  --output ~/.openclaw/workspace/标题.html --data "$DATA" --json-output
```

### Task 5: 修改 `act.go` 将 tenantID 写入 context

**文件**：`internal/agent/act.go`

**变更**：在 tool 执行流程中，将 tenantID 通过 context 传递给 tool：

```go
// 在 executeTools 或 executeTool 方法中
ctx = context.WithValue(ctx, types.ContextKeyTenantID, tenantID)
result, err := tool.Execute(ctx, args)
```

> **需检查**：tenantID 在 AgentEngine 中是否已经可用。如果是，则直接写入 ctx。

### Task 6: 修改 tool 注册注入 FileService

**文件**：`internal/agent/engine.go` 或 `internal/agent/tools/definitions.go`（取决于 tool 注册位置）

**变更**：在创建 `ExecuteSkillScriptTool` 时传入 `fileService`：

```go
skillExecTool := NewExecuteSkillScriptTool(skillManager, fileService)
```

**需检查**：`AgentEngine` 结构体是否已有 `fileService` 字段，如果没有则需新增。

### Task 7: 前端新增 `SkillFilesResult.vue` 渲染组件

**文件**：`frontend/src/views/chat/components/tool-results/SkillFilesResult.vue`（新建）

**内容**：
- 接收 `toolData.files` 数组
- 渲染为文件卡片列表，每个卡片显示：
  - 文件格式图标（HTML🌐 / SVG🖼️ / XMind📘）
  - 文件名
  - 文件大小
  - 用途描述
  - 下载按钮（链接到 `download_url`）
  - 对于 SVG：增加"预览"按钮（弹出 Modal 显示 SVG 内容）

**Vue 组件结构**：

```vue
<template>
  <div class="skill-files-result">
    <div class="files-header">
      <span class="files-title">{{ $t('agent.generatedFiles') }}</span>
    </div>
    <div class="files-list">
      <div v-for="file in files" :key="file.file_name" class="file-card">
        <div class="file-icon">{{ formatIcon(file.format) }}</div>
        <div class="file-info">
          <span class="file-name">{{ file.file_name }}</span>
          <span class="file-desc">{{ file.description }}</span>
          <span class="file-size">{{ formatSize(file.size) }}</span>
        </div>
        <div class="file-actions">
          <t-button theme="primary" size="small" @click="downloadFile(file)">
            {{ $t('agent.download') }}
          </t-button>
          <t-button v-if="file.format === 'svg'" size="small" @click="previewSvg(file)">
            {{ $t('agent.preview') }}
          </t-button>
        </div>
      </div>
    </div>
  </div>
</template>
```

### Task 8: 前端注册新的 display_type

**文件1**：`frontend/src/views/chat/components/ToolResultRenderer.vue`

**变更**：新增 `skill_files` 分支：

```vue
<!-- Skill Files Display -->
<SkillFilesResult
  v-else-if="displayType === 'skill_files'"
  :data="toolData as SkillFilesData"
/>
```

**文件2**：`frontend/src/types/tool-results.ts`

**变更**：新增 `SkillFilesData` 类型定义和 `'skill_files'` DisplayType。

### Task 9: 前端国际化文案

**文件**：`frontend/src/locales/zh-CN.ts` 和 `frontend/src/locales/en-US.ts`

**新增文案**：
- `agent.generatedFiles`: "生成的文件" / "Generated Files"
- `agent.download`: "下载" / "Download"
- `agent.preview`: "预览" / "Preview"

### Task 10: 文件提取逻辑的 fallback（通用 skill 文件输出支持）

**设计**：不仅支持 mindmap，还支持任何 skill 脚本输出文件。

**在 `skill_execute.go` 中**：
1. 优先从 stdout 最后一行解析 JSON（`openclaw_output_files` 协议）
2. 如果 JSON 解析失败，fallback 到正则匹配 stdout 中的文件路径（`/tmp/.openclaw/workspace/xxx.ext`）
3. 对于 Docker sandbox 模式，从 OutputDir 目录中扫描所有文件

### Task 11: 调整 Docker sandbox 模式下的脚本执行流程

**在 `Manager.ExecuteScript()` 中**：
1. 创建宿主机临时目录作为 OutputDir
2. Docker sandbox 将此目录挂载到 `/output`
3. 脚本需要在 Docker 内将文件输出到 `/output` 或 `~/.openclaw/workspace/`
4. 执行结束后，从 OutputDir 目录读取文件（如 OutputDir 已设置）

**修改 SKILL.md 的指令**：让 LLM 在 Docker sandbox 环境下传入 `--output /output/标题.html` 参数。

> **实际考虑**：当前部署环境使用 Docker sandbox，但 mindmap SKILL.md 中的指令使用 `~/.openclaw/workspace/` 作为输出路径。Docker 容器中 HOME=/tmp，所以 `~/.openclaw/workspace/` = `/tmp/.openclaw/workspace/`，执行结束后文件丢失。
>
> **解决方案**：
> - 在 Manager.ExecuteScript 中设置 OutputDir
> - 修改 SKILL.md 指令，使用 `--output /output/标题.html` 作为输出路径
> - 但这要求 SKILL.md 知晓当前是 Docker sandbox 还是 Local sandbox
> 
> **更优雅的方案**：让脚本支持环境变量 `OPENCLAW_OUTPUT_DIR`，在 Docker sandbox 中设置为 `/output`，Local sandbox 中不设置（使用默认 `~/.openclaw/workspace/`）。Manager.ExecuteScript 在创建 ExecuteConfig 时将此环境变量传入。

## 5. 文件修改清单

| 序号 | 文件路径 | 修改类型 | 说明 |
|------|---------|---------|------|
| 1 | `internal/agent/tools/skill_execute.go` | 修改 | 注入 FileService，增加文件提取逻辑 |
| 2 | `internal/agent/skills/manager.go` | 修改 | 设置 OutputDir 和 OPENCLAW_OUTPUT_DIR 环境变量 |
| 3 | `internal/agent/act.go` | 修改 | 将 tenantID 写入 context |
| 4 | `internal/agent/engine.go` | 修改 | 传入 FileService 到 ExecuteSkillScriptTool |
| 5 | `skills/preloaded/generate-mindmap/generate_mindmap.py` | 修改 | 增加 --json-output 参数和 JSON 输出协议 |
| 6 | `skills/preloaded/generate-mindmap/SKILL.md` | 修改 | 更新执行指令，添加 --json-output 和环境变量支持 |
| 7 | `frontend/src/views/chat/components/tool-results/SkillFilesResult.vue` | 新建 | 文件卡片渲染组件 |
| 8 | `frontend/src/views/chat/components/ToolResultRenderer.vue` | 修改 | 注册 skill_files display_type |
| 9 | `frontend/src/types/tool-results.ts` | 修改 | 新增 SkillFilesData 类型 |
| 10 | `frontend/src/locales/zh-CN.ts` | 修改 | 新增国际化文案 |
| 11 | `frontend/src/locales/en-US.ts` | 修改 | 新增国际化文案 |

## 6. 实施优先级和依赖关系

```
Task 1 (skill_execute.go 注入) ─→ Task 2 (文件提取逻辑) ─→ Task 10 (fallback 逻辑)
                                                              │
Task 5 (act.go tenantID) ─────────────────────────────────────┤
                                                              │
Task 6 (engine.go 注册) ─────────────────────────────────────┤
                                                              │
Task 3 (Docker OutputDir) ─→ Task 11 (Docker 环境变量) ──────┤
                                                              │
Task 4 (generate_mindmap.py) ────────────────────────────────┤
                                                              ↓
Task 7 (SkillFilesResult.vue) ─→ Task 8 (ToolResultRenderer) ─→ Task 9 (国际化)
```

**建议实施顺序**：
1. 先做后端（Task 1-6），可独立测试通过
2. 再做脚本修改（Task 4），确保输出协议正确
3. 最后做前端（Task 7-9），验证完整链路
4. Docker sandbox 支持（Task 3, 11）可后续迭代

## 7. 风险和注意事项

1. **安全**：`FileService.SaveBytes()` 内部已有安全校验（SafeFileName），无需额外处理
2. **文件大小**：XMind 文件可能较大（几百KB），但通过 FileService 存储后只传 URL，不影响 SSE 性能
3. **tenantID 传递**：需确认 AgentEngine 中 tenantID 的获取方式，避免引入循环依赖
4. **Docker sandbox**：当前可能使用 local sandbox（WEKNORA_SANDBOX_MODE=local），先确保 local 模式可用，Docker 模式作为后续迭代
5. **向后兼容**：新增 `display_type` 不影响现有工具，`openclaw_output_files` JSON 解析失败时 fallback 到原有行为
6. **清理**：生成文件保存在 FileService 的持久化存储中，不会自动清理。可在后续版本增加 TTL 机制

## 8. 验证计划

1. **后端单元测试**：验证 stdout JSON 解析、文件路径提取、FileService 存储流程
2. **集成测试**：启动服务，通过 API 调用 mindmap skill，检查 ToolResult.Data 中是否包含 files 和 download_url
3. **前端验证**：在聊天界面触发 mindmap skill，确认文件卡片正确渲染，下载按钮可用