<template>
  <div class="ppt-generation-page">
    <div class="ppt-generation-empty">
      <img src="@/assets/img/ppt.svg" alt="PPT" class="ppt-generation-icon" />
      <h2>{{ t('pptGeneration.title') }}</h2>
      <p>{{ t('pptGeneration.description') }}</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useI18n } from 'vue-i18n'

const { t } = useI18n()
</script>

<style scoped>
.ppt-generation-page {
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--td-bg-color-container);
}

.ppt-generation-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  color: var(--td-text-color-secondary);
}

.ppt-generation-icon {
  width: 48px;
  height: 48px;
  opacity: 0.5;
}

.ppt-generation-empty h2 {
  margin: 0;
  font-size: 18px;
  font-weight: 500;
  color: var(--td-text-color-primary);
}

.ppt-generation-empty p {
  margin: 0;
  font-size: 14px;
}
</style>
