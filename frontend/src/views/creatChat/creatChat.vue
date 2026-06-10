<template>
    <div class="dialogue-wrap">
        <div class="dialogue-answers">
            <div class="dialogue-title" style="--wails-draggable: drag">
                <div class="title-icon" style="--wails-draggable: drag">
                    <t-icon name="edit-2" size="24px" />
                </div>
                <span style="--wails-draggable: drag">{{ getAgentName(settingsStore.selectedAgentId) }}</span>
            </div>
            <WritingAssistantTabs
                :activeAgentId="settingsStore.selectedAgentId"
                @select="handleTabSelect"
            />
            <InputField ref="inputFieldRef" :hideAgentSelector="true" :hideWebSearch="true" @send-msg="sendMsg"></InputField>
        </div>
    </div>
    
    <!-- 知识库编辑器（创建/编辑统一组件） -->
    <KnowledgeBaseEditorModal 
      :visible="uiStore.showKBEditorModal"
      :mode="uiStore.kbEditorMode"
      :kb-id="uiStore.currentKBId || undefined"
      :initial-type="uiStore.kbEditorType"
      @update:visible="(val) => val ? null : uiStore.closeKBEditor()"
      @success="handleKBEditorSuccess"
    />
</template>
<script setup lang="ts">
import { ref, onMounted } from 'vue';
import InputField from '@/components/Input-field.vue';
import WritingAssistantTabs from '@/components/WritingAssistantTabs.vue';

import { createSessions } from "@/api/chat/index";
import { useMenuStore } from '@/stores/menu';
import { useSettingsStore } from '@/stores/settings';
import { useUIStore } from '@/stores/ui';
import { useRoute, useRouter } from 'vue-router';
import { MessagePlugin, Icon as TIcon } from 'tdesign-vue-next';
import { useI18n } from 'vue-i18n';
import KnowledgeBaseEditorModal from '@/views/knowledge/KnowledgeBaseEditorModal.vue';
import { useKnowledgeBaseCreationNavigation } from '@/hooks/useKnowledgeBaseCreationNavigation';
import { listAgents } from '@/api/agent';

const router = useRouter();
const route = useRoute();
const usemenuStore = useMenuStore();
const settingsStore = useSettingsStore();
const uiStore = useUIStore();

// 所有智能体列表（从 API 加载）
const allAgents = ref<any[]>([]);

// 加载智能体列表
onMounted(async () => {
  try {
    const res = await listAgents();
    const data = (res as { data?: any[] }).data || [];
    allAgents.value = data;
  } catch (e) {
    console.error('Failed to load agents:', e);
  }
});

// 根据 agentId 获取智能体显示名称（从后端返回的数据中查找）
const getAgentName = (id: string): string => {
  const agent = allAgents.value.find((a: any) => a.id === id);
  return agent ? agent.name : '写作助手';
};
const { t } = useI18n();
const { navigateToKnowledgeBaseList } = useKnowledgeBaseCreationNavigation();

// 写作助手选项卡选择处理
const handleTabSelect = (agentId: string) => {
  settingsStore.selectAgent(agentId);
};

const inputFieldRef = ref();

// 选项卡选择处理


const sendMsg = (value: string, modelId: string, mentionedItems: any[], imageFiles: any[] = [], attachmentFiles: any[] = []) => {
    createNewSession(value, modelId, mentionedItems, imageFiles, attachmentFiles);
}

async function createNewSession(value: string, modelId: string, mentionedItems: any[] = [], imageFiles: any[] = [], attachmentFiles: any[] = []) {
    const selectedKbs = settingsStore.settings.selectedKnowledgeBases || [];
    const selectedFiles = settingsStore.settings.selectedFiles || [];

    // 构建 session 数据，包含 Agent 配置
    const sessionData: any = {};
    
    // 添加 Agent 配置（知识库信息在 agent_config 中）
    sessionData.agent_config = {
        enabled: true,
        max_iterations: settingsStore.agentConfig.maxIterations,
        temperature: settingsStore.agentConfig.temperature,
        knowledge_bases: selectedKbs,  // 所有选中的知识库
        knowledge_ids: selectedFiles,  // 所有选中的普通知识/文件
        allowed_tools: settingsStore.agentConfig.allowedTools
    };

    try {
        const res = await createSessions(sessionData);
        if (res.data && res.data.id) {
            await navigateToSession(res.data.id, value, modelId, mentionedItems, imageFiles, attachmentFiles);
        } else {
            console.error('[createChat] Failed to create session');
            MessagePlugin.error(t('createChat.messages.createFailed'));
        }
    } catch (error) {
        console.error('[createChat] Create session error:', error);
        MessagePlugin.error(t('createChat.messages.createError'));
    }
}

const navigateToSession = async (sessionId: string, value: string, modelId: string, mentionedItems: any[], imageFiles: any[] = [], attachmentFiles: any[] = []) => {
    const now = new Date().toISOString();
    let obj = { 
        title: t('createChat.newSessionTitle'), 
        path: `chat/${sessionId}`, 
        id: sessionId, 
        isMore: false, 
        isNoTitle: true,
        created_at: now,
        updated_at: now
    };
    usemenuStore.updataMenuChildren(obj);
    usemenuStore.changeIsFirstSession(true);
    usemenuStore.changeFirstQuery(value, mentionedItems, modelId, imageFiles, attachmentFiles);
    router.push(`/platform/chat/${sessionId}`);
}

const handleKBEditorSuccess = (kbId: string) => {
    navigateToKnowledgeBaseList(kbId)
}

</script>
<style lang="less" scoped>
.chat-agent-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--td-text-color-primary);
  padding: 8px 4px 4px;
}

.dialogue-wrap {
    flex: 1;
    display: flex;
    justify-content: center;
    align-items: center;
}

.dialogue-answers {
    display: flex;
    flex-flow: column;
    align-items: center;
    width: 100%;
    max-width: 800px;

    :deep(.answers-input) {
        position: static;
        transform: translateX(0);
    }
}

.dialogue-title {
    display: flex;
    color: var(--td-text-color-primary);
    font-family: var(--app-font-family);
    font-size: 28px;
    font-weight: 600;
    align-items: center;
    margin-bottom: 30px;
    gap: 12px;

    .title-icon {
        display: flex;
        width: 40px;
        height: 40px;
        justify-content: center;
        align-items: center;
        border-radius: 10px;
        background: linear-gradient(135deg, #e8f5e9 0%, #c8e6c9 100%);
        color: #2e7d32;
        box-shadow: 0 2px 8px rgba(46, 125, 50, 0.15);
    }
}

@media (max-width: 1250px) and (min-width: 1045px) {
    .answers-input {
        transform: translateX(-329px);
    }

    :deep(.t-textarea__inner) {
        width: 654px !important;
    }
}

@media (max-width: 1045px) {
    .answers-input {
        transform: translateX(-250px);
    }

    :deep(.t-textarea__inner) {
        width: 500px !important;
    }
}
@media (max-width: 750px) {
    .answers-input {
        transform: translateX(-250px);
    }

    :deep(.t-textarea__inner) {
        width: 340px !important;
    }
}
@media (max-width: 600px) {
    .answers-input {
        transform: translateX(-250px);
    }

    :deep(.t-textarea__inner) {
        width: 300px !important;
    }
}

</style>
<style lang="less">
.del-menu-popup {
    z-index: 99 !important;

    .t-popup__content {
        width: 100px;
        height: 40px;
        line-height: 30px;
        padding-left: 14px;
        cursor: pointer;
        margin-top: 4px !important;

    }
}
</style>