<template>
  <div class="empty-state">
    <strong>{{ title }}</strong>
    <span>{{ description || message }}</span>
  </div>
</template>

<script setup>
defineProps({
  title: { type: String, default: '暂无数据' },
  message: { type: String, default: '当前条件下没有可显示的记录。' },
  description: { type: String, default: '' }
});
</script>
