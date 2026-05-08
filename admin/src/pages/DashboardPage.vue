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
        <h2>最近活跃</h2>
        <ul v-if="recentLogs.length" class="timeline">
          <li v-for="log in recentLogs" :key="log.id">
            <span>{{ eventName(log.event_type) }}</span>
            <p>{{ log.license_key || log.machine_id || '匿名客户端' }}</p>
            <time>{{ formatTime(log.created_at) }}</time>
          </li>
        </ul>
        <EmptyState v-else title="暂无活跃日志" description="客户端启动、心跳、验证和更新检查会显示在这里。" />
      </section>

      <section class="panel">
        <h2>活跃指标</h2>
        <div class="activity-list">
          <div>
            <span>近 15 分钟在线</span>
            <strong>{{ activity.active_15m || 0 }}</strong>
          </div>
          <div>
            <span>近 24 小时活跃客户端</span>
            <strong>{{ activity.unique_active_24h || 0 }}</strong>
          </div>
          <div>
            <span>近 24 小时启动次数</span>
            <strong>{{ activity.app_starts_24h || 0 }}</strong>
          </div>
          <div>
            <span>近 24 小时估算在线分钟</span>
            <strong>{{ activity.estimated_online_minutes_24h || 0 }}</strong>
          </div>
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
import { formatServerTime } from '../utils/time';

const summary = ref({});
const recentLogs = ref([]);
const { error, run } = useAsync();

const activity = computed(() => summary.value.activity || {});
const metrics = computed(() => [
  { label: '有效卡密', value: summary.value.licenses?.active_usable || 0, hint: '当前可正常验证的卡密' },
  { label: '已禁用卡密', value: summary.value.licenses?.disabled || 0, hint: '后台手动禁用的卡密' },
  { label: '绑定客户端', value: summary.value.clients?.total || 0, hint: '已经激活绑定的客户端数' },
  { label: '近 24 小时活跃', value: activity.value.unique_active_24h || 0, hint: '有启动、心跳或验证的客户端' }
]);

const EVENT_TEXT = {
  app_start: '启动',
  app_heartbeat: '心跳',
  license_activate: '激活',
  license_verify: '验证',
  'license.activate': '激活',
  'license.verify': '验证',
  update_check: '更新检查'
};

function eventName(value) {
  return EVENT_TEXT[value] || value || '活跃';
}

function formatTime(value) {
  return formatServerTime(value);
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
