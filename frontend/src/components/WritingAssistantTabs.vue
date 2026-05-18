<template>
  <div class="wa-tabs">
    <div
      v-for="tab in mainTabs"
      :key="tab.id"
      class="wa-tab"
      :class="{ 'wa-tab--active': activeAgentId === tab.id }"
      @click="handleTabClick(tab)"
    >
      <t-icon :name="tab.icon" size="16px" class="wa-tab__icon" />
      <span class="wa-tab__label">{{ tab.label }}</span>
    </div>
    <!-- 更多下拉 -->
    <t-popup
      placement="bottom"
      trigger="click"
      :overlay-inner-class-name="'wa-tabs-dropdown-popup'"
    >
      <div class="wa-tab wa-tab--more" :class="{ 'wa-tab--active': isMoreActive }">
        <t-icon name="ellipsis" size="16px" class="wa-tab__icon" />
      </div>
      <template #content>
        <div class="wa-tabs-dropdown">
          <div
            v-for="item in moreTabs"
            :key="item.id"
            class="wa-tabs-dropdown-item"
            :class="{ 'wa-tabs-dropdown-item--active': activeAgentId === item.id }"
            @click="handleMoreItemClick(item)"
          >
            <t-icon :name="item.icon" size="16px" class="wa-tabs-dropdown-item__icon" />
            <span class="wa-tabs-dropdown-item__label">{{ item.label }}</span>
          </div>
        </div>
      </template>
    </t-popup>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { Icon as TIcon, Popup as TPopup } from 'tdesign-vue-next';

interface TabItem {
  id: string;
  label: string;
  icon: string;
}

const props = defineProps<{
  activeAgentId: string;
}>();

const emit = defineEmits<{
  (e: 'select', agentId: string): void;
}>();

const mainTabs: TabItem[] = [
  { id: 'builtin-unlimited', label: '不限', icon: 'chat' },
  { id: 'builtin-brief', label: '汇报', icon: 'chart-bar' },
  { id: 'builtin-tech-doc', label: '技术文档', icon: 'file-code' },
  { id: 'builtin-polish', label: '润色', icon: 'edit-1' },
];

const moreTabs: TabItem[] = [
  { id: 'builtin-mindmap', label: '思维导图', icon: 'root-list' },
  { id: 'builtin-report', label: '报告', icon: 'file-icon' },
];

// 判断"..."选项卡是否高亮（当前选中项在下拉菜单中）
const isMoreActive = computed(() => {
  return moreTabs.some(item => item.id === props.activeAgentId);
});

const handleTabClick = (tab: TabItem) => {
  emit('select', tab.id);
};

const handleMoreItemClick = (item: TabItem) => {
  emit('select', item.id);
};
</script>

<style lang="less" scoped>
.wa-tabs {
  display: flex;
  align-items: center;
  gap: 0;
  margin-bottom: 16px;
  width: 100%;
}

.wa-tab {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 8px 0;
  cursor: pointer;
  transition: all 0.2s ease;
  white-space: nowrap;
  user-select: none;
  background: var(--td-bg-color-container, #fff);
  color: var(--td-text-color-secondary, #999);
  border: 1px solid var(--td-component-stroke, #e7e9eb);
  font-size: 13px;
  // 五个选项卡等宽，用 flex:1 平分
  flex: 1;
  min-width: 0;

  &:not(:first-child) {
    border-left: none;
  }

  &:first-child {
    border-radius: 8px 0 0 8px;
  }

  &:last-child {
    border-radius: 0 8px 8px 0;
  }

  &__icon {
    flex-shrink: 0;
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
    // "..."选项卡也需要等宽
    flex: 1;
  }
}

.wa-tabs-dropdown {
  padding: 4px 0;
  min-width: 140px;
}

.wa-tabs-dropdown-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  cursor: pointer;
  transition: background 0.15s ease;
  font-size: 13px;
  color: var(--td-text-color-primary, #222);

  &__icon {
    flex-shrink: 0;
    color: var(--td-text-color-secondary, #666);
  }

  &__label {
    line-height: 1.4;
  }

  &:hover {
    background: var(--td-bg-color-container-hover, #f6f8f7);
  }

  &--active {
    background: #e8f5e9;
    color: #000;
    font-weight: 500;

    .wa-tabs-dropdown-item__icon {
      color: #000;
    }

    &:hover {
      background: #dcedc8;
    }
  }
}
</style>

<style lang="less">
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
