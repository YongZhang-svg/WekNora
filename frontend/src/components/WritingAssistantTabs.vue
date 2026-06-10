<template>
  <div class="wa-tabs">
    <div class="wa-tabs-bar">
      <div
        v-for="tab in visibleTabs"
        :key="tab.id"
        class="wa-tab"
        :class="{ 'wa-tab--active': activeAgentId === tab.id }"
        @click="handleTabClick(tab)"
      >
        <span v-if="tab.avatar" class="wa-tab__avatar">{{ tab.avatar }}</span>
        <t-icon v-else :name="tab.icon" size="16px" class="wa-tab__icon" />
        <span class="wa-tab__label">{{ tab.label }}</span>
      </div>
      <!-- 更多下拉 -->
      <t-popup v-if="moreTabs.length > 0" placement="bottom" trigger="click" :overlay-inner-class-name="'wa-tabs-dropdown-popup'">
        <div class="wa-tab wa-tab--more" :class="{ 'wa-tab--active': isMoreActive }">
          <t-icon name="ellipsis" size="16px" />
        </div>
        <template #content>
          <div class="wa-tabs-dropdown">
            <div
              v-for="tab in moreTabs"
              :key="tab.id"
              class="wa-tabs-dropdown-item"
              :class="{ 'wa-tabs-dropdown-item--active': activeAgentId === tab.id }"
              @click="handleTabClick(tab)"
            >
              <span v-if="tab.avatar" class="wa-tabs-dropdown-item__avatar">{{ tab.avatar }}</span>
              <t-icon v-else :name="tab.icon" size="16px" class="wa-tabs-dropdown-item__icon" />
              <span class="wa-tabs-dropdown-item__label">{{ tab.label }}</span>
            </div>
          </div>
        </template>
      </t-popup>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, onMounted } from 'vue';
import { Icon as TIcon, Popup as TPopup } from 'tdesign-vue-next';
import { listAgents, type CustomAgent } from '@/api/agent';

interface TabItem {
  id: string;
  label: string;
  icon: string;
  avatar?: string;
}

const props = defineProps<{
  activeAgentId: string;
}>();

const emit = defineEmits<{
  (e: 'select', agentId: string): void;
}>();

// 所有内置智能体（平铺显示，不区分主/更多）
const builtinTabs: TabItem[] = [
  { id: 'builtin-unlimited', label: '不限', icon: 'chat' },
  { id: 'builtin-brief', label: '汇报', icon: 'chart-bar' },
  { id: 'builtin-tech-doc', label: '技术文档', icon: 'file-code' },
  { id: 'builtin-polish', label: '润色', icon: 'edit-1' },
  { id: 'builtin-mindmap', label: '思维导图', icon: 'root-list' },
  { id: 'builtin-report', label: '报告', icon: 'file-icon' },
];

// 自定义智能体列表（从 API 加载）
const customAgents = ref<CustomAgent[]>([]);

// 将自定义智能体转换为 TabItem 格式
const customAgentTabs = computed<TabItem[]>(() =>
  customAgents.value.map(agent => ({
    id: agent.id,
    label: agent.name,
    icon: 'app',
    avatar: agent.avatar || undefined,
  }))
);

// 合并所有选项卡（内置 + 自定义）
const allTabs = computed<TabItem[]>(() => [
  ...customAgentTabs.value,
  ...builtinTabs,
]);

// 前4个显示，其余放入更多下拉
const MAX_VISIBLE = 4;
const visibleTabs = computed(() => allTabs.value.slice(0, MAX_VISIBLE));
const moreTabs = computed(() => allTabs.value.slice(MAX_VISIBLE));
const moreTabIds = computed(() => new Set(moreTabs.value.map(t => t.id)));
const isMoreActive = computed(() => moreTabIds.value.has(props.activeAgentId));

const handleTabClick = (tab: TabItem) => {
  emit('select', tab.id);
};

// 加载自定义智能体列表
const loadCustomAgents = async () => {
  try {
    const res = await listAgents();
    const data = (res as { data?: CustomAgent[] }).data || [];
    // 只取自定义智能体（非内置）
    customAgents.value = data.filter(a => !a.is_builtin);
  } catch (error) {
    console.error('Failed to load custom agents for WritingAssistantTabs:', error);
  }
};

onMounted(() => {
  loadCustomAgents();
});
</script>

<style lang="less" scoped>
.wa-tabs {
  width: 100%;
}

.wa-tabs-bar {
  display: flex;
  align-items: stretch;
  gap: 0;
  white-space: nowrap;
}

.wa-tab {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
  padding: 8px 14px;
  cursor: pointer;
  transition: all 0.2s ease;
  white-space: nowrap;
  user-select: none;
  flex: 1;
  min-width: 0;
  height: 36px;
  box-sizing: border-box;
  background: var(--td-bg-color-container, #fff);
  color: var(--td-text-color-secondary, #999);
  border: 1px solid var(--td-component-stroke, #e7e9eb);
  font-size: 13px;

  &:not(:first-child) {
    border-left: none;
  }

  &:first-child {
    border-radius: 8px 0 0 8px;
  }

  &:last-child {
    border-radius: 0 8px 8px 0;
  }

  &--more:last-child {
    border-radius: 0 8px 8px 0;
  }

  &__icon,
  &__avatar {
    flex-shrink: 0;
    font-size: 14px;
    width: 14px;
    height: 14px;
    display: flex;
    align-items: center;
    justify-content: center;
  }

  &__label {
    line-height: 1.4;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  &:hover {
    background: var(--td-brand-color-light, #eefdf5);
    color: var(--td-text-color-primary, #222);
  }

  &--active {
    background: #e8f5e9;
    color: #000;
    border-color: #c8e6c9;
    font-weight: 500;

    & + .wa-tab {
      border-left-color: #c8e6c9;
    }

    &:hover {
      background: #dcedc8;
      border-color: #aed581;
      color: #000;
    }
  }

  &--more {
    flex: none;
    padding: 8px 12px;
    height: 36px;
    box-sizing: border-box;
  }
}

/* 下拉菜单样式 */
.wa-tabs-dropdown {
  padding: 4px 0;
  min-width: 120px;
}

.wa-tabs-dropdown-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  cursor: pointer;
  font-size: 13px;
  color: var(--td-text-color-primary, #222);
  transition: background 0.15s ease;

  &__icon, &__avatar {
    flex-shrink: 0;
    font-size: 14px;
    width: 14px;
    height: 14px;
    display: flex;
    align-items: center;
    justify-content: center;
    color: var(--td-text-color-secondary, #666);
  }

  &__label {
    line-height: 1.4;
    white-space: nowrap;
  }

  &:hover {
    background: var(--td-bg-color-container-hover, #f6f8f7);
  }

  &--active {
    color: #000;
    font-weight: 500;
  }
}

.wa-tabs-dropdown-popup {
  &.t-popup__content {
    background: var(--td-bg-color-container, #fff) !important;
    border: 1px solid var(--td-component-border, #e7e9eb) !important;
    border-radius: 8px !important;
    box-shadow: var(--td-shadow-2, 0 6px 28px rgba(15, 23, 42, 0.08)) !important;
    padding: 4px 0 !important;
  }
}
</style>


