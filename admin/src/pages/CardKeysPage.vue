<template>
  <section>
    <PageHeader eyebrow="Licenses" title="卡密管理">
      <button type="button" class="primary-btn" @click="create">生成卡密</button>
    </PageHeader>

    <form class="inline-form" @submit.prevent="create">
      <label>天数<input v-model.number="newKey.days" type="number" min="1" /></label>
      <label>最大客户端<input v-model.number="newKey.max_devices" type="number" min="1" /></label>
      <label>备注<input v-model.trim="newKey.remark" placeholder="可选" /></label>
    </form>

    <p v-if="error" class="notice error">{{ error }}</p>

    <div class="table-wrap">
      <table>
        <thead>
          <tr>
            <th>卡密</th>
            <th>状态</th>
            <th>到期时间</th>
            <th>最大客户端</th>
            <th>备注</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="item in rows" :key="item.id">
            <td class="mono">{{ item.key }}</td>
            <td><span class="status" :data-status="item.status">{{ item.status }}</span></td>
            <td>{{ item.expires_at || '-' }}</td>
            <td>{{ item.max_devices }}</td>
            <td>{{ item.note || '-' }}</td>
            <td>
              <button type="button" class="link-btn" :disabled="item.status === 'disabled'" @click="disable(item)">
                禁用
              </button>
            </td>
          </tr>
        </tbody>
      </table>
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

const newKey = reactive({ days: 30, max_devices: 1, remark: '' });
const rows = ref([]);
const { error, run } = useAsync();

async function load() {
  const data = await run(() => api.cardKeys());
  rows.value = data?.items || [];
}

async function create() {
  const data = await run(() => api.createCardKey(newKey));
  if (data) await load();
}

async function disable(item) {
  const data = await run(() => api.disableCardKey(item.id));
  if (data !== null) await load();
}

onMounted(load);
</script>
