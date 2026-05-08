<template>
  <section>
    <PageHeader eyebrow="Releases" title="版本发布">
      <button type="button" class="primary-btn" @click="publish">发布版本</button>
    </PageHeader>

    <form class="release-form" @submit.prevent="publish">
      <label>版本号<input v-model.trim="form.version" placeholder="例如 1.2.0" required /></label>
      <label>下载地址<input v-model.trim="form.download_url" placeholder="http://服务器IP/updates/xxx.zip" required /></label>
      <label class="full">更新说明<textarea v-model.trim="form.release_note" rows="4" /></label>
      <label class="checkbox-row"><input v-model="form.force_update" type="checkbox" /> 标记为强制更新</label>
    </form>

    <p class="notice muted">
      客户端检查更新出现 404，通常表示这里还没有发布任何“启用”的 windows 版本。发布一条启用版本后会恢复正常。
    </p>
    <p v-if="error" class="notice error">{{ error }}</p>

    <section class="panel">
      <h2>历史版本</h2>
      <div class="table-wrap">
        <table>
          <thead>
            <tr>
              <th>版本号</th>
              <th>平台</th>
              <th>强制</th>
              <th>启用</th>
              <th>发布时间</th>
              <th>下载地址</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in rows" :key="item.id">
              <td class="mono">{{ item.version }}</td>
              <td>{{ item.platform }}</td>
              <td>{{ item.mandatory ? '是' : '否' }}</td>
              <td><span class="status" :data-status="item.active ? 'active' : 'disabled'">{{ item.active ? '启用' : '停用' }}</span></td>
              <td>{{ formatTime(item.created_at) }}</td>
              <td><a :href="item.download_url" target="_blank" rel="noreferrer">{{ item.download_url }}</a></td>
            </tr>
          </tbody>
        </table>
        <EmptyState v-if="!rows.length" />
      </div>
    </section>
  </section>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue';
import { api } from '../api';
import { useAsync } from '../composables/useAsync';
import EmptyState from '../components/EmptyState.vue';
import PageHeader from '../components/PageHeader.vue';
import { formatServerTime } from '../utils/time';

const rows = ref([]);
const form = reactive({ version: '', download_url: '', release_note: '', force_update: false });
const { error, run } = useAsync();

function formatTime(value) {
  return formatServerTime(value);
}

async function load() {
  const data = await run(() => api.versions());
  rows.value = data?.items || [];
}

async function publish() {
  const data = await run(() => api.publishVersion(form));
  if (data) {
    form.version = '';
    form.download_url = '';
    form.release_note = '';
    form.force_update = false;
    await load();
  }
}

onMounted(load);
</script>
