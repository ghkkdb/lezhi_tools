<template>
  <section>
    <PageHeader eyebrow="Events" title="事件日志">
      <button type="button" class="ghost-btn" @click="load">刷新</button>
    </PageHeader>

    <form class="toolbar" @submit.prevent="load">
      <input v-model.trim="query.event_type" placeholder="事件名，如 task_start" />
      <button type="submit" class="ghost-btn">查询</button>
    </form>

    <p v-if="error" class="notice error">{{ error }}</p>

    <div class="log-list">
      <article v-for="item in rows" :key="item.id" class="log-item">
        <span class="log-level">{{ item.event_type }}</span>
        <div>
          <strong>{{ item.license_key || item.machine_id || 'anonymous' }}</strong>
          <p>{{ item.payload || '-' }}</p>
          <small>{{ item.ip || '-' }} | {{ item.created_at || '-' }}</small>
        </div>
      </article>
      <EmptyState v-if="!rows.length" />
    </div>
  </section>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue';
import { api } from '../api';
import { useAsync } from '../composables/useAsync';
import EmptyState from '../components/EmptyState.vue';
import PageHeader from '../components/PageHeader.vue';

const query = reactive({ event_type: '' });
const rows = ref([]);
const { error, run } = useAsync();

async function load() {
  const data = await run(() => api.logs(query));
  rows.value = data?.items || [];
}

onMounted(load);
</script>
