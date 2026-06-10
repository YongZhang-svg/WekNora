<template>
  <MdEditor v-model="localContent" :toolbars="toolbars" style="height: 100%;" />
</template>

<script setup>
import { ref, watch } from 'vue';
import { MdEditor } from 'md-editor-v3';
import 'md-editor-v3/lib/style.css';

const props = defineProps({
  content: { type: String, default: '' }
});

const emit = defineEmits(['contentChange']);

const localContent = ref(props.content);

// 当 props.content 变化时同步到编辑区
watch(() => props.content, (val) => {
  localContent.value = val;
});

const toolbars = [
  'bold', 'italic', 'underline', 'strikeThrough',
  '-',
  'title', 'sub', 'sup',
  'quote', 'unorderedList', 'orderedList', 'task',
  '-',
  'codeRow', 'code', 'link', 'image', 'table',
  '-',
  'revoke', 'next', 'save',
  '=',
  'preview',
];

watch(localContent, (val) => {
  emit('contentChange', val);
});
</script>
