<template>
  <div class="excel-process-page">
    <div class="excel-process-empty">
      <img src="@/assets/img/excel.svg" alt="Excel" class="excel-process-icon" />
      <h2>{{ t('excelProcess.title') }}</h2>
      <p>{{ t('excelProcess.description') }}</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useI18n } from 'vue-i18n'

const { t } = useI18n()
</script>

<style scoped>
.excel-process-page {
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--td-bg-color-container);
}

.excel-process-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  color: var(--td-text-color-secondary);
}

.excel-process-icon {
  width: 48px;
  height: 48px;
  opacity: 0.5;
}

.excel-process-empty h2 {
  margin: 0;
  font-size: 18px;
  font-weight: 500;
  color: var(--td-text-color-primary);
}

.excel-process-empty p {
  margin: 0;
  font-size: 14px;
}
</style>
