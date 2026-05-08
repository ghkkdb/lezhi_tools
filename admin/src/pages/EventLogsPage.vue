<template>
  <section>
    <PageHeader eyebrow="Activity" title="活跃日志">
      <button type="button" class="ghost-btn" @click="load">刷新</button>
    </PageHeader>

    <form class="toolbar" @submit.prevent="load">
      <select v-model="query.event_type">
        <option value="">全部活跃事件</option>
        <option value="app_start">启动</option>
        <option value="app_heartbeat">心跳</option>
        <option value="license_verify">卡密验证</option>
        <option value="license_activate">卡密激活</option>
        <option value="update_check">更新检查</option>
      </select>
      <button type="submit" class="ghost-btn">查询</button>
    </form>

    <p v-if="error" class="notice error">{{ error }}</p>

    <div class="log-list">
      <article v-for="item in rows" :key="item.id" class="log-item">
        <span class="log-level">{{ eventName(item.event_type) }}</span>
        <div>
          <strong>{{ item.license_key || item.machine_id || '匿名客户端' }}</strong>
          <p>{{ eventSummary(item) }}</p>
          <small>{{ item.ip || '-' }} | {{ formatTime(item.created_at) }}</small>
        </div>
      </article>
      <EmptyState v-if="!rows.length" title="暂无活跃日志" description="这里不会记录具体任务名称、任务结果或个人使用明细。" />
    </div>
  </section>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue';
import { api } from '../api';
import { useAsync } from '../composables/useAsync';
import EmptyState from '../components/EmptyState.vue';
import PageHeader from '../components/PageHeader.vue';
import { formatServerTime } from '../utils/time';

const query = reactive({ event_type: '' });
const rows = ref([]);
const { error, run } = useAsync();

const EVENT_TEXT = {
  app_start: '启动',
  app_heartbeat: '心跳',
  license_activate: '卡密激活',
  license_verify: '卡密验证',
  'license.activate': '卡密激活',
  'license.verify': '卡密验证',
  update_check: '更新检查'
};

function eventName(value) {
  return EVENT_TEXT[value] || value || '活跃';
}

function eventSummary(item) {
  const payload = parsePayload(item.payload);
  if (item.event_type === 'update_check') {
    return payload.has_update ? `发现新版本 ${payload.latest_version || ''}` : '已检查更新';
  }
  if (item.event_type === 'app_heartbeat') return '客户端在线心跳';
  if (item.event_type === 'app_start') return '客户端启动';
  if (item.event_type?.includes('license')) return '卡密状态校验';
  return '活跃事件';
}

function parsePayload(value) {
  if (!value) return {};
  try {
    return JSON.parse(value);
  } catch {
    return {};
  }
}

function formatTime(value) {
  return formatServerTime(value);
}

async function load() {
  const data = await run(() => api.logs(query));
  rows.value = data?.items || [];
}

onMounted(load);
</script>
