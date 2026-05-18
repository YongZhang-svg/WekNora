<template>
  <div class="doc-parser-page">
    <div class="doc-parser-empty">
      <img src="@/assets/img/docparser.svg" alt="DocParser" class="doc-parser-icon" />
      <h2>{{ t('docParser.title') }}</h2>
      <p>{{ t('docParser.description') }}</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useI18n } from 'vue-i18n'

const { t } = useI18n()
</script>

<style scoped>
.doc-parser-page {
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--td-bg-color-container);
}

.doc-parser-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  color: var(--td-text-color-secondary);
}

.doc-parser-icon {
  width: 48px;
  height: 48px;
  opacity: 0.5;
}

.doc-parser-empty h2 {
  margin: 0;
  font-size: 18px;
  font-weight: 500;
  color: var(--td-text-color-primary);
}

.doc-parser-empty p {
  margin: 0;
  font-size: 14px;
}
</style>
