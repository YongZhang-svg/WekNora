<template>
  <div style="height: 100%;">
    <MilkdownEditorInner :content="content" @content-change="(v) => $emit('contentChange', v)" />
  </div>
</template>

<script setup>
import MilkdownEditorInner from './MilkdownEditorInner.vue';

defineProps({
  content: { type: String, default: '' }
});

defineEmits(['contentChange']);
</script>
