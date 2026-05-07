<template>
  <section>
    <PageHeader eyebrow="Clients" title="客户端绑定">
      <button type="button" class="ghost-btn" @click="load">刷新</button>
    </PageHeader>

    <p v-if="error" class="notice error">{{ error }}</p>

    <div class="table-wrap">
      <table>
        <thead>
          <tr>
            <th>ID</th>
            <th>匿名客户端</th>
            <th>卡密</th>
            <th>版本</th>
            <th>最近 IP</th>
            <th>最后在线</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="item in rows" :key="item.id">
            <td>{{ item.id }}</td>
            <td class="mono">{{ item.machine_id }}</td>
            <td class="mono">{{ item.license_key }}</td>
            <td>{{ item.app_version || '-' }}</td>
            <td>{{ item.last_ip || '-' }}</td>
            <td>{{ item.last_seen_at || '-' }}</td>
            <td><button type="button" class="link-btn" @click="unbind(item)">解绑</button></td>
          </tr>
        </tbody>
      </table>
      <EmptyState v-if="!rows.length" />
    </div>
  </section>
</template>

<script setup>
import { onMounted, ref } from 'vue';
import { api } from '../api';
import { useAsync } from '../composables/useAsync';
import EmptyState from '../components/EmptyState.vue';
import PageHeader from '../components/PageHeader.vue';

const rows = ref([]);
const { error, run } = useAsync();

async function load() {
  const data = await run(() => api.bindings());
  rows.value = data?.items || [];
}

async function unbind(item) {
  const data = await run(() => api.unbindClient(item.id));
  if (data !== null) await load();
}

onMounted(load);
</script>
