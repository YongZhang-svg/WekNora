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
                    <!-- 格式化工具栏 -->
                    <div class="format-toolbar" style="display:flex !important;visibility:visible !important;opacity:1 !important;background:#e8f5e9 !important;border:2px solid #4caf50 !important;padding:6px 8px !important;margin-bottom:8px !important;border-radius:6px !important;">
                        <button class="toolbar-btn" style="display:inline-flex !important;min-width:30px;height:28px;padding:0 6px;border:1px solid #ccc;border-radius:4px;background:white;color:#333;font-size:12px;cursor:pointer;align-items:center;justify-content:center;" @click.stop="formatText('h1')" title="标题1">H1</button>
                        <button class="toolbar-btn" style="display:inline-flex !important;min-width:30px;height:28px;padding:0 6px;border:1px solid #ccc;border-radius:4px;background:white;color:#333;font-size:12px;cursor:pointer;align-items:center;justify-content:center;" @click.stop="formatText('h2')" title="标题2">H2</button>
                        <button class="toolbar-btn" style="display:inline-flex !important;min-width:30px;height:28px;padding:0 6px;border:1px solid #ccc;border-radius:4px;background:white;color:#333;font-size:12px;cursor:pointer;align-items:center;justify-content:center;" @click.stop="formatText('h3')" title="标题3">H3</button>
                        <button class="toolbar-btn" style="display:inline-flex !important;min-width:30px;height:28px;padding:0 6px;border:1px solid #ccc;border-radius:4px;background:white;color:#333;font-size:12px;cursor:pointer;align-items:center;justify-content:center;" @click.stop="formatText('p')" title="正文">P</button>
                        <span style="width:1px;height:18px;background:#ccc;margin:0 4px;display:inline-block !important;flex-shrink:0;"></span>
                        <button class="toolbar-btn" style="display:inline-flex !important;min-width:30px;height:28px;padding:0 6px;border:1px solid #ccc;border-radius:4px;background:white;color:#333;font-size:12px;cursor:pointer;align-items:center;justify-content:center;" @click.stop="formatText('bold')" title="加粗"><b>B</b></button>
                        <button class="toolbar-btn" style="display:inline-flex !important;min-width:30px;height:28px;padding:0 6px;border:1px solid #ccc;border-radius:4px;background:white;color:#333;font-size:12px;cursor:pointer;align-items:center;justify-content:center;" @click.stop="formatText('italic')" title="斜体"><i>I</i></button>
                        <button class="toolbar-btn" style="display:inline-flex !important;min-width:30px;height:28px;padding:0 6px;border:1px solid #ccc;border-radius:4px;background:white;color:#333;font-size:12px;cursor:pointer;align-items:center;justify-content:center;" @click.stop="formatText('underline')" title="下划线"><u>U</u></button>
                        <span style="width:1px;height:18px;background:#ccc;margin:0 4px;display:inline-block !important;flex-shrink:0;"></span>
                        <button class="toolbar-btn" style="display:inline-flex !important;min-width:30px;height:28px;padding:0 6px;border:1px solid #ccc;border-radius:4px;background:white;color:#333;font-size:12px;cursor:pointer;align-items:center;justify-content:center;" @click.stop="formatText('insertUnorderedList')" title="无序列表">&#8226; L</button>
                        <button class="toolbar-btn" style="display:inline-flex !important;min-width:30px;height:28px;padding:0 6px;border:1px solid #ccc;border-radius:4px;background:white;color:#333;font-size:12px;cursor:pointer;align-items:center;justify-content:center;" @click.stop="formatText('insertOrderedList')" title="有序列表">1. L</button>
                        <span style="width:1px;height:18px;background:#ccc;margin:0 4px;display:inline-block !important;flex-shrink:0;"></span>
                        <div style="position:relative;display:inline-flex !important;">
                            <button class="toolbar-btn" style="display:inline-flex !important;min-width:30px;height:28px;padding:0 6px;border:1px solid #ccc;border-radius:4px;background:white;color:#333;font-size:12px;cursor:pointer;align-items:center;justify-content:center;" title="字体颜色">A<span style="display:block;height:2px;background:red;margin-top:-2px;"></span></button>
                            <div style="display:none;position:absolute;top:100%;left:0;z-index:1000;padding:6px;background:white;border:1px solid #ddd;border-radius:6px;box-shadow:0 4px 16px rgba(0,0,0,0.12);margin-top:4px;">
                                <button v-for="color in textColors" :key="color.value" style="display:flex;align-items:center;gap:6px;padding:4px 8px;border:none;border-radius:4px;background:transparent;font-size:12px;cursor:pointer;white-space:nowrap;width:100%;" :style="{ color: color.value, backgroundColor: color.value === '#000000' ? '#eee' : 'white' }" @click.stop="handleColorChange(color.value)">{{ color.label }}</button>
                            </div>
                        </div>
                        <div style="position:relative;display:inline-flex !important;">
                            <button class="toolbar-btn" style="display:inline-flex !important;min-width:30px;height:28px;padding:0 6px;border:1px solid #ccc;border-radius:4px;background:white;color:#333;font-size:12px;cursor:pointer;align-items:center;justify-content:center;" title="背景高亮">&#9632;<span style="display:block;height:2px;background:yellow;margin-top:-2px;"></span></button>
                            <div style="display:none;position:absolute;top:100%;left:0;z-index:1000;padding:6px;background:white;border:1px solid #ddd;border-radius:6px;box-shadow:0 4px 16px rgba(0,0,0,0.12);margin-top:4px;">
                                <button v-for="color in bgColors" :key="color.value" style="display:flex;align-items:center;gap:6px;padding:4px 8px;border:none;border-radius:4px;background:transparent;font-size:12px;cursor:pointer;white-space:nowrap;width:100%;" :style="{ backgroundColor: color.value === 'transparent' ? '#eee' : color.value, border: color.value === 'transparent' ? '1px solid #ccc' : 'none' }" @click.stop="handleBgColorChange(color.value)">{{ color.label === '无' ? '清除' : color.label }}</button>
                            </div>
                        </div>
                    </div>
                    <!-- 可编辑内容区域 -->
                    <div 
                        ref="editableContent"
                        class="editable-content markdown-content"
                        contenteditable="true"
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

// 切换编辑模式
const handleToggleEdit = () => {
    console.log('handleToggleEdit called, current isEditing:', isEditing.value);
    if (isEditing.value) {
        // 保存编辑
        isEditing.value = false;
        MessagePlugin.success('内容已保存');
    } else {
        // 进入编辑模式
        isEditing.value = true;
        editedContent.value = props.content || props.session?.content || '';
        // 等待 DOM 更新后设置初始内容
        nextTick(() => {
            console.log('nextTick - isEditing:', isEditing.value, 'editableContent:', editableContent.value);
            // 检查 format-toolbar 是否存在
            const toolbar = document.querySelector('.format-toolbar');
            console.log('format-toolbar element:', toolbar, 'display:', toolbar?.style?.display);
            if (editableContent.value) {
                editableContent.value.innerHTML = editedContent.value;
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
const handleExportWord = () => {
    const content = getActualContent();
    if (!content) {
        MessagePlugin.warning(t('chat.emptyContentWarning'));
        return;
    }
    const title = 'AI回复内容';
    
    // 判断内容是否为 HTML 格式
    const isHTML = /<(h[1-6]|p|ul|ol|li|strong|em|b|i|div|table|tr|td|th|br)[\s>]/i.test(content);
    
    let bodyContent;
    if (isHTML) {
        // 如果已经是 HTML 格式，直接使用，但清理空标签
        bodyContent = content
            // 移除空的段落标签
            .replace(/<p>\s*<\/p>/gi, '')
            // 移除空的列表项
            .replace(/<li>\s*<\/li>/gi, '')
            // 移除只有空白字符和换行符的 div
            .replace(/<div>\s*<\/div>/gi, '')
            // 移除连续的空行（多个 <br>）
            .replace(/(<br\s*\/?>\s*){3,}/gi, '<br/><br/>')
            // 清理标签内多余空白
            .replace(/>\s+</g, '><');
    } else {
        // 如果是 Markdown/纯文本，转换为简单 HTML，去掉空行
        bodyContent = `<div>${content
            .split('\n')
            .filter(line => line.trim() !== '')  // 过滤空行
            .join('<br/>')}</div>`;
    }
    
    const fullHtml = `<!DOCTYPE html>
<html xmlns:v="urn:schemas-microsoft-com:vml" xmlns:o="urn:schemas-microsoft-com:office:office" xmlns:w="urn:schemas-microsoft-com:office:word">
<head><meta charset="utf-8"><title>${title}</title>
<!--[if gte mso 9]>
<xml>
  <w:WordDocument>
    <w:View>Print</w:View>
    <w:Zoom>100</w:Zoom>
    <w:DoNotOptimizeForBrowser/>
  </w:WordDocument>
</xml>
<style>
@page Section1 {
  size: 595.3pt 841.9pt;
  margin: 72.0pt 72.0pt 72.0pt 72.0pt;
  mso-page-orientation: portrait;
}
div.Section1 { page: Section1; }
</style>
<![endif]-->
<style>
body{font-family:SimSun,'宋体',serif;font-size:12pt;color:#000;word-wrap:break-word;overflow-wrap:break-word;}
p{margin:0 0 6pt 0;line-height:1.5;text-indent:2em;text-indent:24pt;}
h1{font-size:20pt;font-weight:bold;margin:12pt 0 8pt 0;text-align:center;}
h2{font-size:16pt;font-weight:bold;margin:10pt 0 6pt 0;text-indent:0;}
h3{font-size:14pt;font-weight:bold;margin:8pt 0 4pt 0;text-indent:0;}
ul,ol{margin:4pt 0;padding-left:40pt;}
li{margin:2pt 0;line-height:1.5;text-indent:2em;list-style-position:outside;}
ul ul,ol ol,ul ol,ol ul{margin:2pt 0;padding-left:36pt;}
li ul,li ol{margin:2pt 0;}
strong,b{font-weight:bold;}
em,i{font-style:italic;}
u{text-decoration:underline;}
span{line-height:1.5;}
table{border-collapse:collapse;margin:8pt 0;width:100%;word-wrap:break-word;overflow-wrap:break-word;}
th,td{border:1px solid #000;padding:6pt 8pt;text-align:left;word-wrap:break-word;overflow-wrap:break-word;}
th{background:#f0f0f0;font-weight:bold;}
</style>
</head>
<body>
<div class="Section1">
${bodyContent}
</div>
</body></html>`;
    
    const blob = new Blob([fullHtml], { type: 'application/msword' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${title}.doc`;
    a.click();
    URL.revokeObjectURL(url);
    MessagePlugin.success('Word 导出成功');
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
