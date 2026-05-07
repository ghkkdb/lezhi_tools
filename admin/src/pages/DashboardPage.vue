<template>
  <section>
    <PageHeader eyebrow="Overview" title="仪表盘">
      <button type="button" class="ghost-btn" @click="load">刷新</button>
    </PageHeader>

    <p v-if="error" class="notice error">{{ error }}</p>

    <div class="metric-grid">
      <article v-for="metric in metrics" :key="metric.label" class="metric-card">
        <span>{{ metric.label }}</span>
        <strong>{{ metric.value }}</strong>
        <small>{{ metric.hint }}</small>
      </article>
    </div>

    <div class="split-grid">
      <section class="panel">
        <h2>最近事件</h2>
        <ul v-if="recentLogs.length" class="timeline">
          <li v-for="log in recentLogs" :key="log.id">
            <span>{{ log.event_type || 'event' }}</span>
            <p>{{ eventPayload(log) }}</p>
            <time>{{ log.created_at || '-' }}</time>
          </li>
        </ul>
        <EmptyState v-else />
      </section>

      <section class="panel">
        <h2>统计概览</h2>
        <div class="version-summary">
          <strong>{{ summary.releases?.total || 0 }} 个版本</strong>
          <span>{{ summary.clients?.total || 0 }} 个客户端</span>
          <p>事件类型：{{ Object.keys(summary.events || {}).join(', ') || '暂无' }}</p>
        </div>
      </section>
    </div>
  </section>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue';
import { api } from '../api';
import { useAsync } from '../composables/useAsync';
import EmptyState from '../components/EmptyState.vue';
import PageHeader from '../components/PageHeader.vue';

const summary = ref({});
const recentLogs = ref([]);
const { error, run } = useAsync();

const metrics = computed(() => [
  { label: '有效卡密', value: summary.value.licenses?.active || 0, hint: '当前 active 状态卡密' },
  { label: '已绑定客户端', value: summary.value.clients?.total || 0, hint: '客户端绑定数量' },
  {
    label: '事件总数',
    value: Object.values(summary.value.events || {}).reduce((sum, value) => sum + Number(value || 0), 0),
    hint: '全部事件累计'
  },
  { label: '任务失败', value: summary.value.events?.task_error || 0, hint: '需要关注的任务异常' }
]);

function eventPayload(log) {
  if (!log.payload) return '-';
  try {
    return JSON.stringify(JSON.parse(log.payload));
  } catch {
    return log.payload;
  }
}

async function load() {
  const data = await run(() => api.dashboard());
  if (!data) return;
  summary.value = data;
  const logs = await run(() => api.logs({ limit: 8 }));
  recentLogs.value = logs?.items || [];
}

onMounted(load);
</script>
