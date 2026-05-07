<template>
  <header class="page-header">
    <div>
      <p>{{ eyebrow }}</p>
      <h1>{{ title }}</h1>
    </div>
    <slot />
  </header>
</template>

<script setup>
defineProps({
  eyebrow: { type: String, default: 'Admin' },
  title: { type: String, required: true }
});
</script>
