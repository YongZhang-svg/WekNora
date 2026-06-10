<template>
    <div class="bot_msg" :class="{ 'is-embedded': embeddedMode }">
        <div style="display: flex;flex-direction: column; gap:8px">
            <!-- 显示@的知识库和文件（非 Agent 模式下显示） -->
            <div v-if="!session.isAgentMode && mentionedItems && mentionedItems.length > 0" class="mentioned_items">
                <span
                    v-for="item in mentionedItems"
                    :key="item.id"
                    class="mentioned_tag"
                    :class="[
                      item.type === 'kb' ? (item.kb_type === 'faq' ? 'faq-tag' : 'kb-tag') : 'file-tag'
                    ]"
                >
                    <span class="tag_icon">
                        <t-icon v-if="item.type === 'kb'" :name="item.kb_type === 'faq' ? 'chat-bubble-help' : 'folder'" />
                        <t-icon v-else name="file" />
                    </span>
                    <span class="tag_name">{{ item.name }}</span>
                </span>
            </div>
            <docInfo :session="session"></docInfo>
            <AgentStreamDisplay :session="session" :user-query="userQuery" v-if="session.isAgentMode"></AgentStreamDisplay>
            <deepThink :deepSession="session" v-if="session.showThink && !session.isAgentMode"></deepThink>
        </div>
        <!-- 非 Agent 模式下才显示传统的 markdown 渲染 -->
        <div ref="parentMd" v-if="!session.hideContent && !session.isAgentMode">
            <!-- 直接渲染完整内容，避免切分导致的问题，样式与 thinking 一致 -->
            <!-- 只有当有实际内容时才显示包围框 -->
            <div class="content-wrapper" v-if="hasActualContent">
                <!-- 编辑模式 -->
                <div v-show="isEditing" class="editing-container">
                    <div 
                        ref="editableContent"
                        class="editable-content markdown-content"
                        contenteditable="true" spellcheck="false"
                        @input="handleContentEdit"
                    ></div>
                </div>
                <!-- 只读模式 -->
                <div v-show="!isEditing" class="ai-markdown-template markdown-content" v-html="renderedHTML">
                </div>
            </div>
            <!-- Streaming indicator (non-Agent mode) -->
            <div v-if="hasActualContent && !session.is_completed" class="loading-indicator">
                <div class="loading-typing">
                    <span></span>
                    <span></span>
                    <span></span>
                </div>
            </div>
            <!-- 复制和添加到知识库按钮 - 非 Agent 模式下显示 -->
            <div v-if="session.is_completed && (content || session.content)" class="answer-toolbar">
                <t-button size="small" variant="outline" shape="round" @click.stop="handleCopyAnswer" :title="$t('agent.copy')">
                    <t-icon name="copy" />
                </t-button>
                <t-button size="small" variant="outline" shape="round" @click.stop="handleAddToKnowledge" :title="$t('agent.addToKnowledgeBase')">
                    <t-icon name="add" />
                </t-button>
                <t-button size="small" variant="outline" shape="round" @click.stop="handleToggleEdit" :title="isEditing ? '保存' : '编辑'">
                    <t-icon :name="isEditing ? 'check' : 'edit-2'" />
                </t-button>
                <t-button size="small" variant="outline" shape="round" @click.stop="handleExportWord" title="导出 Word">
                    <t-icon name="download" />
                </t-button>
                <!-- Fallback 提示图标 -->
                <t-tooltip v-if="session.is_fallback" :content="$t('chat.fallbackHint')" placement="top">
                    <t-button size="small" variant="outline" shape="round" class="fallback-icon-btn">
                        <t-icon name="info-circle" />
                    </t-button>
                </t-tooltip>
            </div>
            <div v-if="isImgLoading" class="img_loading"><t-loading size="small"></t-loading><span>{{ $t('common.loading') }}</span></div>
        </div>
        <picturePreview :reviewImg="reviewImg" :reviewUrl="reviewUrl" @closePreImg="closePreImg"></picturePreview>
    </div>
</template>
<script setup>
import { onMounted, onBeforeUnmount, watch, computed, ref, reactive, defineProps, nextTick, onUpdated } from 'vue';
import { marked } from 'marked';
import markedKatex from 'marked-katex-extension';
import 'katex/dist/katex.min.css';
import docInfo from './docInfo.vue';
import deepThink from './deepThink.vue';
import AgentStreamDisplay from './AgentStreamDisplay.vue';
import picturePreview from '@/components/picture-preview.vue';
import { sanitizeHTML, safeMarkdownToHTML, createSafeImage, isValidImageURL, hydrateProtectedFileImages } from '@/utils/security';
import { useI18n } from 'vue-i18n';
import { MessagePlugin } from 'tdesign-vue-next';
import { useUIStore } from '@/stores/ui';
import {
    buildManualMarkdown,
    copyTextToClipboard,
    formatManualTitle,
    replaceIncompleteImageWithPlaceholder
} from '@/utils/chatMessageShared';
import {
    createMermaidCodeRenderer,
    ensureMermaidInitialized,
    renderMermaidInContainer
} from '@/utils/mermaidShared';
import { Document, Packer, Paragraph, TextRun, HeadingLevel, AlignmentType, Table, TableRow, TableCell, WidthType, BorderStyle } from 'docx';
import { saveAs } from 'file-saver';

marked.use({
    breaks: true,  // 全局启用单个换行支持
});

marked.use(markedKatex({ throwOnError: false, nonStandard: true }));

const preprocessMathDelimiters = (rawText) => {
    if (!rawText || typeof rawText !== 'string') {
        return '';
    }
    return rawText
        .replace(/\\\[([\s\S]*?)\\\]/g, '$$$$$1$$$$')
        .replace(/\\\(([\s\S]*?)\\\)/g, '$$$1$$');
};

ensureMermaidInitialized();

const emit = defineEmits(['scroll-bottom'])
const { t } = useI18n()
const uiStore = useUIStore();
const renderer = new marked.Renderer();
let parentMd = ref()
let reviewUrl = ref('')
let reviewImg = ref(false)
let isImgLoading = ref(false);
let isEditing = ref(false);
let editedContent = ref('');
let editableContent = ref(null);

// 文本颜色选项
const textColors = [
    { label: '黑色', value: '#000000' },
    { label: '深灰', value: '#333333' },
    { label: '红色', value: '#FF0000' },
    { label: '蓝色', value: '#0066CC' },
    { label: '绿色', value: '#009900' },
    { label: '橙色', value: '#FF6600' },
    { label: '紫色', value: '#9900CC' },
];

// 背景颜色选项
const bgColors = [
    { label: '无', value: 'transparent' },
    { label: '黄色', value: '#FFFF00' },
    { label: '浅绿', value: '#CCFFCC' },
    { label: '浅蓝', value: '#CCCCFF' },
    { label: '浅粉', value: '#FFCCCC' },
    { label: '浅灰', value: '#F0F0F0' },
];
const props = defineProps({
    // 必填项
    content: {
        type: String,
        required: false
    },
    session: {
        type: Object,
        required: false
    },
    userQuery: {
        type: String,
        required: false,
        default: ''
    },
    isFirstEnter: {
        type: Boolean,
        required: false
    },
    embeddedMode: {
        type: Boolean,
        default: false
    }
});

const preview = (url) => {
    nextTick(() => {
        reviewUrl.value = url;
        reviewImg.value = true
    })
}

const closePreImg = () => {
    reviewImg.value = false
    reviewUrl.value = '';
}

// 创建自定义渲染器实例
const customRenderer = new marked.Renderer();
// 覆盖图片渲染方法
customRenderer.image = function({href, title, text}){
    if (!isValidImageURL(href)) {
        return `<p>${t('error.invalidImageLink')}</p>`;
    }
    return createSafeImage(href, text || '', title || '');
};

// 覆盖代码块渲染方法，支持 Mermaid
customRenderer.code = createMermaidCodeRenderer('mermaid-botmsg');

// 计算属性：将 Markdown 文本转换为 tokens
const mentionedItems = computed(() => {
    return props.session?.mentioned_items || [];
});

// 单次渲染整个 Markdown 内容（替代 token-by-token，修复 KaTeX 公式在 streaming 时闪烁消失的问题）
const renderedHTML = computed(() => {
    const text = props.content || props.session?.content || '';
    if (!text || typeof text !== 'string') return '';
    const processed = replaceIncompleteImageWithPlaceholder(text);
    const safeText = preprocessMathDelimiters(processed);
    const safeMarkdown = safeMarkdownToHTML(safeText);
    const html = marked.parse(safeMarkdown, { renderer: customRenderer, breaks: true });
    return sanitizeHTML(html);
});

// 计算属性：判断是否有实际内容（非空且不只是空白）
const hasActualContent = computed(() => {
    const text = props.content || props.session?.content || '';
    return text && text.trim().length > 0;
});

// 获取实际内容
const getActualContent = () => {
    return (props.content || props.session?.content || '').trim();
};

// 复制回答内容
const handleCopyAnswer = async () => {
    const content = getActualContent();
    if (!content) {
        MessagePlugin.warning(t('chat.emptyContentWarning'));
        return;
    }

    try {
        await copyTextToClipboard(content);
        MessagePlugin.success(t('chat.copySuccess'));
    } catch (err) {
        console.error('复制失败:', err);
        MessagePlugin.error(t('chat.copyFailed'));
    }
};

// 添加到知识库
const handleAddToKnowledge = () => {
    const content = getActualContent();
    if (!content) {
        MessagePlugin.warning(t('chat.emptyContentWarning'));
        return;
    }

    const question = (props.userQuery || '').trim();
    const manualContent = buildManualMarkdown(question, content);
    const manualTitle = formatManualTitle(question);
``
    uiStore.openManualEditor({
        mode: 'create',
        title: manualTitle,
        content: manualContent,
        status: 'draft',
    });

    MessagePlugin.info(t('chat.editorOpened'));
};

// 从内容中提取 outline 包裹的部分
const extractOutlineContent = (content) => {
    const match = content?.match(/```outline\s*\n?([\s\S]*?)```/);
    return match ? match[1].trim() : content;
};

// 存储原始完整内容（含 outline 标记）
let originalFullContent = '';

// 切换编辑模式
const handleToggleEdit = () => {
    console.log('handleToggleEdit called, current isEditing:', isEditing.value);
    if (isEditing.value) {
        // 保存编辑：将编辑后的内容拼回原始内容
        const newContent = editableContent.value?.innerText || editedContent.value;
        if (originalFullContent) {
            const restored = originalFullContent.replace(/```outline\s*\n?([\s\S]*?)```/, '```outline\n' + newContent + '\n```');
            if (props.session) {
                props.session.content = restored;
            }
        } else if (props.session) {
            props.session.content = newContent;
        }
        isEditing.value = false;
        MessagePlugin.success('内容已保存');
    } else {
        const content = props.content || props.session?.content || '';
        const outlineMatch = content.match(/```outline\s*\n?([\s\S]*?)```/);
        // 触发编辑弹窗（有 outline 标记则提取中间内容，否则使用全部内容）
        window.dispatchEvent(new CustomEvent('open-outline-dialog', {
            detail: { content: outlineMatch ? outlineMatch[1].trim() : content, fullContent: content, isOutline: !!outlineMatch, session: props.session }
        }));
        return;
        // 进入编辑模式
        isEditing.value = true;
        originalFullContent = content;
        editedContent.value = extractOutlineContent(content);
        // 等待 DOM 更新后设置初始内容
        nextTick(() => {
            console.log('nextTick - isEditing:', isEditing.value, 'editableContent:', editableContent.value);
            // 检查 format-toolbar 是否存在
            const toolbar = document.querySelector('.format-toolbar');
            console.log('format-toolbar element:', toolbar, 'display:', toolbar?.style?.display);
            if (editableContent.value) {
                editableContent.value.innerHTML = marked(editedContent.value);
            }
        });
        MessagePlugin.info('进入编辑模式，点击内容即可编辑');
    }
};

// 处理内容编辑
const handleContentEdit = (event) => {
    editedContent.value = event.target.innerHTML;
    // 更新 session 内容
    if (props.session) {
        props.session.content = event.target.innerHTML;
    }
};

// 格式化文本
const formatText = (command) => {
    if (editableContent.value) {
        editableContent.value.focus();
        if (command.startsWith('h') || command === 'p') {
            // 处理标题和段落
            document.execCommand('formatBlock', false, `<${command}>`);
        } else {
            // 处理其他命令（加粗、斜体等）
            document.execCommand(command, false);
        }
        // 触发更新
        handleContentEdit({ target: editableContent.value });
    }
};

// 处理字体颜色变化
const handleColorChange = (color) => {
    if (!color) return;
    if (editableContent.value) {
        editableContent.value.focus();
        document.execCommand('foreColor', false, color);
        handleContentEdit({ target: editableContent.value });
    }
};

// 处理背景颜色变化
const handleBgColorChange = (color) => {
    if (!color) return;
    if (editableContent.value) {
        editableContent.value.focus();
        if (color === 'transparent') {
            document.execCommand('removeFormat', false);
        } else {
            document.execCommand('hiliteColor', false, color);
        }
        handleContentEdit({ target: editableContent.value });
    }
};

// 导出为 Word 文档
const handleExportWord = async () => {
    const rawContent = getActualContent();
    if (!rawContent) {
        MessagePlugin.warning(t('chat.emptyContentWarning'));
        return;
    }
    // 如果有 ```outline 标记，只导出中间的内容
    const outlineMatch = rawContent.match(/```outline\s*\n?([\s\S]*?)```/);
    const content = outlineMatch ? outlineMatch[1].trim() : rawContent;
    const title = 'AI回复内容';
    
    try {
        // 判断内容是否为 HTML 格式
        const isHTML = /<(h[1-6]|p|ul|ol|li|strong|em|b|i|div|table|tr|td|th|br)[\s>]/i.test(content);
        
        let htmlContent;
        if (isHTML) {
            htmlContent = content;
        } else {
            // 如果是 Markdown/纯文本，使用 marked 转换为 HTML
            htmlContent = marked(content);
        }
        
        // 解析 HTML 内容并转换为 docx 文档元素
        const docChildren = [];
        
        // 创建临时 DOM 来解析 HTML
        const tempDiv = document.createElement('div');
        tempDiv.innerHTML = htmlContent;
        
        // 递归处理 DOM 节点
        const processNode = (node, format = {}) => {
            const results = [];
            
            if (node.nodeType === Node.TEXT_NODE) {
                const text = node.textContent.trim();
                if (text) {
                    results.push(new TextRun({ text, size: 24, font: '方正仿宋_GBK', ...format })); // 12pt = 24 half-points
                }
            } else if (node.nodeType === Node.ELEMENT_NODE) {
                const tagName = node.tagName.toLowerCase();
                
                // 处理标题
                if (tagName.match(/^h[1-6]$/)) {
                    const level = parseInt(tagName[1]);
                    const fontSizes = [48, 40, 32, 28, 24, 24]; // h1-h6 的字体大小
                    const headingLevels = [
                        HeadingLevel.HEADING_1,
                        HeadingLevel.HEADING_2,
                        HeadingLevel.HEADING_3,
                        HeadingLevel.HEADING_4,
                        HeadingLevel.HEADING_5,
                        HeadingLevel.HEADING_6
                    ];
                    
                    const textRuns = Array.from(node.childNodes).flatMap((child) => processNode(child, { color: '000000' }));
                    if (textRuns.length > 0) {
                        results.push(new Paragraph({
                            heading: headingLevels[level - 1],
                            children: textRuns,
                            alignment: level === 1 ? AlignmentType.CENTER : undefined,
                            spacing: { before: 200, after: 100 }
                        }));
                    }
                }
                // 处理段落
                else if (tagName === 'p' || tagName === 'div') {
                    const textRuns = Array.from(node.childNodes).flatMap((child) => processNode(child));
                    if (textRuns.length > 0) {
                        results.push(new Paragraph({
                            children: textRuns,
                            spacing: { after: 120 },
                            indent: { firstLineChars: 200 } // 首行缩进 2 字符
                        }));
                    }
                }
                // 处理列表
                else if (tagName === 'ul' || tagName === 'ol') {
                    let index = 0;
                    Array.from(node.children).forEach((child) => {
                        if (child.tagName.toLowerCase() === 'li') {
                            index++;
                            const textRuns = Array.from(child.childNodes).flatMap((c) => processNode(c));
                            if (textRuns.length > 0) {
                                const marker = tagName === 'ol' ? `${index}. ` : '• ';
                                results.push(new Paragraph({
                                    children: [
                                        new TextRun({
                                            text: marker.padStart(4),
                                            size: 24,
                                            font: '方正仿宋_GBK'
                                        }),
                                        ...textRuns
                                    ],
                                    indent: { left: 720, hanging: 360 },
                                    spacing: { before: 30, after: 30 }
                                }));
                            }
                        }
                    });
                }
                // 处理表格
                else if (tagName === 'table') {
                    const rows = [];
                    const firstRow = node.querySelector('tr');
                    const colCount = firstRow ? firstRow.children.length : 1;
                    const colWidth = Math.floor(100 / colCount);
                    Array.from(node.querySelectorAll('tr')).forEach((tr) => {
                        const cells = [];
                        Array.from(tr.children).forEach((cell) => {
                            const isHeader = cell.tagName.toLowerCase() === 'th';
                            const textRuns = Array.from(cell.childNodes).flatMap((c) => processNode(c));
                            cells.push(new TableCell({
                                children: [new Paragraph({
                                    children: textRuns,
                                    spacing: { after: 60 }
                                })],
                                width: { size: colWidth, type: WidthType.PERCENTAGE },
                                shading: isHeader ? { fill: 'F0F0F0', type: 'clear' } : undefined
                            }));
                        });
                        rows.push(new TableRow({ children: cells }));
                    });
                    
                    if (rows.length > 0) {
                        results.push(new Table({
                            rows,
                            width: { size: 100, type: WidthType.PERCENTAGE }
                        }));
                    }
                }
                // 处理文本格式标签
                else if (tagName === 'strong' || tagName === 'b') {
                    results.push(...Array.from(node.childNodes).flatMap((child) => processNode(child, { ...format, bold: true })));
                }
                else if (tagName === 'em' || tagName === 'i') {
                    results.push(...Array.from(node.childNodes).flatMap((child) => processNode(child, { ...format, italics: true })));
                }
                else if (tagName === 'br') {
                    results.push(new TextRun({ text: '', break: 1, font: '方正仿宋_GBK' }));
                }
                // 其他标签，处理子节点
                else {
                    results.push(...Array.from(node.childNodes).flatMap((child) => processNode(child, format)));
                }
            }
            
            return results;
        };
        
        // 处理顶层节点
        Array.from(tempDiv.children).forEach((child) => {
            docChildren.push(...processNode(child));
        });
        
        // 如果没有解析出任何内容，使用纯文本
        if (docChildren.length === 0) {
            docChildren.push(new Paragraph({
                children: [new TextRun({ text: content, size: 24, font: '方正仿宋_GBK' })],
                spacing: { after: 120 }
            }));
        }
        
        // 创建 docx 文档
        const doc = new Document({
            sections: [{
                properties: {},
                children: docChildren
            }]
        });
        
        // 生成并下载文件
        const blob = await Packer.toBlob(doc);
        saveAs(blob, `${title}.docx`);
        MessagePlugin.success('Word 导出成功');
    } catch (error) {
        console.error('Word 导出失败:', error);
        MessagePlugin.error('Word 导出失败，请重试');
    }
};

// 处理 markdown-content 中图片的点击事件
const handleMarkdownImageClick = (e) => {
    const target = e.target;
    if (target && target.tagName === 'IMG') {
        const src = target.getAttribute('src');
        if (src) {
            e.preventDefault();
            e.stopPropagation();
            preview(src);
        }
    }
};

// 渲染 Mermaid 图表的函数
const renderMermaidDiagrams = async () => {
  await renderMermaidInContainer(parentMd.value);
};

// 监听内容变化并渲染 Mermaid - 只在会话完成后渲染
onUpdated(() => {
    nextTick(async () => {
        await hydrateProtectedFileImages(parentMd.value);
        // 只在会话完成后渲染 mermaid
        if (props.session?.is_completed) {
            renderMermaidDiagrams();
        }
    });
});

onMounted(async () => {
    // 为 markdown-content 中的图片添加点击事件
    nextTick(async () => {
        if (parentMd.value) {
            parentMd.value.addEventListener('click', handleMarkdownImageClick, true);
        }
        await hydrateProtectedFileImages(parentMd.value);
        // 初始渲染 Mermaid 图表
        renderMermaidDiagrams();
    });
});

onBeforeUnmount(() => {
    if (parentMd.value) {
        parentMd.value.removeEventListener('click', handleMarkdownImageClick, true);
    }
});
</script>
<style lang="less" scoped>
@import '../../../components/css/markdown.less';
@import '../../../components/css/chat-message-shared.less';

.bot_msg {
    &.is-embedded {
        width: 100%;
        
        :deep(.agent-stream-display) {
            width: 100%;
        }
    }
}

// 内容包装器 - 与 Agent 模式的 answer 样式一致
.content-wrapper {
    background: var(--td-bg-color-container);
    border-radius: 6px;
    padding: 8px 0px;
    transition: all 0.2s ease;
}

.mentioned_items {
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
    justify-content: flex-start;
    max-width: 100%;
    margin-bottom: 2px;
}

.mentioned_tag {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    padding: 3px 8px;
    border-radius: 4px;
    font-size: 12px;
    font-weight: 500;
    max-width: 200px;
    cursor: default;
    transition: all 0.15s;
    background: rgba(7, 192, 95, 0.06);
    border: 1px solid rgba(7, 192, 95, 0.2);
    color: var(--td-text-color-primary);

    &.kb-tag {
        .tag_icon {
            color: var(--td-brand-color);
        }
    }

    &.faq-tag {
        .tag_icon {
            color: var(--td-warning-color);
        }
    }

    &.file-tag {
        .tag_icon {
            color: var(--td-text-color-secondary);
        }
    }

    .tag_icon {
        font-size: 13px;
        display: flex;
        align-items: center;
    }

    .tag_name {
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
        color: currentColor;
    }
}

.fallback-icon-btn {
    color: var(--td-text-color-disabled) !important;
    border-color: var(--td-component-stroke) !important;

    &:hover {
        color: var(--td-text-color-placeholder) !important;
        border-color: var(--td-component-border) !important;
    }
}

@keyframes fadeInUp {
    from {
        opacity: 0;
        transform: translateY(8px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}

.ai-markdown-template {
    font-size: 15px;
    color: var(--td-text-color-primary);
    line-height: 1.6;
}

.editable-content {
    font-size: 15px;
    color: var(--td-text-color-primary);
    line-height: 1.6;
    min-height: 100px;
    padding: 12px;
    border: 2px solid var(--td-brand-color);
    border-radius: 6px;
    background: var(--td-bg-color-container);
    outline: none;
    cursor: text;
    transition: all 0.2s ease;
    
    &:hover {
        border-color: var(--td-brand-color-hover);
        box-shadow: 0 0 0 2px rgba(7, 192, 95, 0.1);
    }
    
    &:focus {
        border-color: var(--td-brand-color);
        box-shadow: 0 0 0 3px rgba(7, 192, 95, 0.15);
        background: var(--td-bg-color-container-hover);
    }
}

.editing-container {
    position: relative;
}

.format-toolbar {
    display: flex;
    align-items: center;
    gap: 2px;
    padding: 6px 8px;
    margin-bottom: 8px;
    background: #e8f5e9;
    border: 2px solid #4caf50;
    border-radius: 6px;
    flex-wrap: wrap;
    
    .toolbar-btn {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        min-width: 30px;
        height: 28px;
        padding: 0 6px;
        border: 1px solid #ccc;
        border-radius: 4px;
        background: white;
        color: #333;
        font-size: 12px;
        cursor: pointer;
        transition: all 0.15s ease;
        line-height: 1;
        font-family: inherit;
        
        &:hover {
            background: rgba(7, 192, 95, 0.08);
            border-color: rgba(7, 192, 95, 0.2);
        }
        
        &:active {
            background: rgba(7, 192, 95, 0.15);
        }
    }
    
    .toolbar-btn-icon {
        font-size: 13px;
        font-weight: 500;
        
        b { font-weight: 700; }
        i { font-style: italic; }
        u { text-decoration: underline; }
    }
    
    .toolbar-separator {
        width: 1px;
        height: 18px;
        background: var(--td-component-stroke);
        margin: 0 4px;
        flex-shrink: 0;
    }
    
    .toolbar-dropdown {
        position: relative;
        display: inline-flex;
        
        &:hover .toolbar-dropdown-menu {
            display: flex;
        }
        
        .toolbar-dropdown-menu {
            display: none;
            position: absolute;
            top: 100%;
            left: 0;
            z-index: 1000;
            flex-direction: column;
            gap: 2px;
            padding: 6px;
            background: var(--td-bg-color-container);
            border: 1px solid var(--td-component-stroke);
            border-radius: 6px;
            box-shadow: 0 4px 16px rgba(0,0,0,0.12);
            min-width: 80px;
            margin-top: 4px;
            
            .color-option {
                display: flex;
                align-items: center;
                gap: 6px;
                padding: 4px 8px;
                border: none;
                border-radius: 4px;
                background: transparent;
                font-size: 12px;
                cursor: pointer;
                transition: all 0.15s ease;
                font-family: inherit;
                white-space: nowrap;
                
                &:hover {
                    background: rgba(7, 192, 95, 0.08);
                }
            }
        }
    }
}

.markdown-content {
    :deep(p) {
        margin: 6px 0;
        line-height: 1.6;
    }

    :deep(code) {
        background: var(--td-bg-color-secondarycontainer);
        padding: 2px 5px;
        border-radius: 3px;
        font-family: var(--app-font-family-mono);
        font-size: 11px;
    }

    :deep(pre) {
        background: var(--td-bg-color-secondarycontainer);
        padding: 10px;
        border-radius: 4px;
        overflow-x: auto;
        margin: 6px 0;

        code {
            background: none;
            padding: 0;
        }
    }

    :deep(ul), :deep(ol) {
        margin: 6px 0;
        padding-left: 20px;
    }

    :deep(li) {
        margin: 3px 0;
    }

    :deep(blockquote) {
        border-left: 2px solid var(--td-brand-color);
        padding-left: 10px;
        margin: 6px 0;
        color: var(--td-text-color-secondary);
    }

    :deep(h1), :deep(h2), :deep(h3), :deep(h4), :deep(h5), :deep(h6) {
        margin: 10px 0 6px 0;
        font-weight: 600;
        color: var(--td-text-color-primary);
    }

    :deep(a) {
        color: var(--td-brand-color);
        text-decoration: none;

        &:hover {
            text-decoration: underline;
        }
    }

    :deep(table) {
        border-collapse: collapse;
        margin: 6px 0;
        font-size: 11px;
        width: 100%;

        th, td {
            border: 1px solid var(--td-component-stroke);
            padding: 5px 8px;
            text-align: left;
        }

        th {
            background: var(--td-bg-color-secondarycontainer);
            font-weight: 600;
        }

        tbody tr:nth-child(even) {
            background: var(--td-bg-color-secondarycontainer);
        }
    }

    :deep(img) {
        max-width: 80%;
        max-height: 300px;
        width: auto;
        height: auto;
        border-radius: 8px;
        display: block;
        margin: 8px 0;
        border: 0.5px solid var(--td-component-stroke);
        object-fit: contain;
        cursor: pointer;
        transition: transform 0.2s ease;

        &:hover {
        }
    }

    // Mermaid 图表样式
    :deep(.mermaid) {
        margin: 16px 0;
        padding: 16px;
        background: var(--td-bg-color-secondarycontainer);
        border-radius: 8px;
        overflow-x: auto;
        text-align: center;

        svg {
            max-width: 100%;
            height: auto;
        }
    }
}

.ai-markdown-img {
    max-width: 80%;
    max-height: 300px;
    width: auto;
    height: auto;
    border-radius: 8px;
    display: block;
    cursor: pointer;
    object-fit: contain;
    margin: 8px 0 8px 16px;
    border: 0.5px solid var(--td-component-stroke);
    transition: transform 0.2s ease;

    &:hover {
        transform: scale(1.02);
    }
}

.bot_msg {
    // background: var(--td-bg-color-container);
    border-radius: 4px;
    color: var(--td-text-color-primary);
    font-size: 16px;
    // padding: 10px 12px;
    margin-right: auto;
    max-width: 100%;
    box-sizing: border-box;
}

.botanswer_laoding_gif {
    width: 24px;
    height: 18px;
    margin-left: 16px;
}

.thinking-loading {
    padding: 8px 0;
}

.loading-indicator {
    padding: 8px 0;
}

.loading-typing {
    display: flex;
    align-items: center;
    gap: 4px;
    
    span {
        width: 6px;
        height: 6px;
        border-radius: 50%;
        background: var(--td-brand-color);
        animation: typingBounce 1.4s ease-in-out infinite;
        
        &:nth-child(1) {
            animation-delay: 0s;
        }
        
        &:nth-child(2) {
            animation-delay: 0.2s;
        }
        
        &:nth-child(3) {
            animation-delay: 0.4s;
        }
    }
}

@keyframes typingBounce {
    0%, 60%, 100% {
        transform: translateY(0);
    }
    30% {
        transform: translateY(-8px);
    }
}

.img_loading {
    background: var(--td-bg-color-container-hover);
    height: 230px;
    width: 230px;
    color: var(--td-text-color-placeholder);
    display: flex;
    align-items: center;
    justify-content: center;
    flex-direction: column;
    font-size: 12px;
    gap: 4px;
    margin-left: 16px;
    border-radius: 8px;
}

:deep(.t-loading__gradient-conic) {
    background: conic-gradient(from 90deg at 50% 50%, #fff 0deg, #676767 360deg) !important;

}
</style>
