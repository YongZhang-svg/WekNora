<template>
  <div class="text2video-page">
    <div class="text2video-empty">
      <img src="@/assets/img/text2video.svg" alt="Text2Video" class="text2video-icon" />
      <h2>{{ t('text2video.title') }}</h2>
      <p>{{ t('text2video.description') }}</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useI18n } from 'vue-i18n'

const { t } = useI18n()
</script>

<style scoped>
.text2video-page {
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--td-bg-color-container);
}

.text2video-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  color: var(--td-text-color-secondary);
}

.text2video-icon {
  width: 48px;
  height: 48px;
  opacity: 0.5;
}

.text2video-empty h2 {
  margin: 0;
  font-size: 18px;
  font-weight: 500;
  color: var(--td-text-color-primary);
}

.text2video-empty p {
  margin: 0;
  font-size: 14px;
}
</style>
