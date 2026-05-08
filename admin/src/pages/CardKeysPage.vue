<template>
  <section>
    <PageHeader eyebrow="Licenses" title="卡密管理">
      <div class="header-actions">
        <button type="button" class="ghost-btn" @click="exportSelected">导出</button>
        <button type="button" class="primary-btn" @click="create">生成卡密</button>
      </div>
    </PageHeader>

    <form class="inline-form license-form" @submit.prevent="create">
      <label>生成数量<input v-model.number="newKey.count" type="number" min="1" max="500" /></label>
      <label>有效天数<input v-model.number="newKey.days" type="number" min="1" /></label>
      <label>最大客户端<input v-model.number="newKey.max_devices" type="number" min="1" /></label>
      <label>备注<input v-model.trim="newKey.remark" placeholder="可选" /></label>
    </form>

    <div class="toolbar action-toolbar">
      <input v-model.trim="keyword" placeholder="搜索卡密、备注或拥有者" />
      <button type="button" class="ghost-btn" @click="copySelected">复制选中</button>
      <button type="button" class="ghost-btn" :disabled="!selectedIds.length" @click="extendSelected">选中加时</button>
      <button type="button" class="danger-btn" :disabled="!selectedIds.length" @click="deleteSelected">删除选中</button>
    </div>

    <p v-if="error" class="notice error">{{ error }}</p>
    <p v-if="notice" class="notice success">{{ notice }}</p>

    <div class="table-wrap">
      <table>
        <thead>
          <tr>
            <th class="check-col"><input type="checkbox" :checked="allVisibleSelected" @change="toggleAll" /></th>
            <th>卡密</th>
            <th>状态</th>
            <th>到期时间</th>
            <th>最大客户端</th>
            <th>备注</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="item in filteredRows" :key="item.id">
            <td class="check-col"><input v-model="selectedIds" type="checkbox" :value="item.id" /></td>
            <td class="mono">{{ item.key }}</td>
            <td><span class="status" :data-status="statusKind(item)">{{ statusText(item) }}</span></td>
            <td>{{ formatTime(item.expires_at) }}</td>
            <td>{{ item.max_devices }}</td>
            <td>{{ item.note || '-' }}</td>
            <td class="row-actions">
              <button type="button" class="link-btn" @click="copyKeys([item])">复制</button>
              <button type="button" class="link-btn" @click="extendOne(item)">加时</button>
              <button v-if="item.status === 'disabled'" type="button" class="link-btn" @click="enable(item)">
                解除禁用
              </button>
              <button v-else type="button" class="link-btn danger-text" @click="disable(item)">禁用</button>
            </td>
          </tr>
        </tbody>
      </table>
      <EmptyState v-if="!filteredRows.length" />
    </div>
  </section>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue';
import { api } from '../api';
import { useAsync } from '../composables/useAsync';
import EmptyState from '../components/EmptyState.vue';
import PageHeader from '../components/PageHeader.vue';
import { formatServerTime, isServerTimeExpired, parseServerTime } from '../utils/time';

const newKey = reactive({ count: 1, days: 30, max_devices: 1, remark: '' });
const rows = ref([]);
const selectedIds = ref([]);
const keyword = ref('');
const notice = ref('');
const { error, run } = useAsync();

const filteredRows = computed(() => {
  const word = keyword.value.toLowerCase();
  if (!word) return rows.value;
  return rows.value.filter((item) =>
    [item.key, item.note, item.owner, item.status].some((value) => String(value || '').toLowerCase().includes(word))
  );
});

const selectedRows = computed(() => rows.value.filter((item) => selectedIds.value.includes(item.id)));
const allVisibleSelected = computed(
  () => filteredRows.value.length > 0 && filteredRows.value.every((item) => selectedIds.value.includes(item.id))
);

async function load() {
  const data = await run(() => api.cardKeys());
  rows.value = data?.items || [];
  selectedIds.value = selectedIds.value.filter((id) => rows.value.some((item) => item.id === id));
}

async function create() {
  notice.value = '';
  const data = await run(() => api.createCardKey(newKey));
  if (data) {
    notice.value = `已生成 ${data.items?.length || 1} 个卡密`;
    await load();
  }
}

async function disable(item) {
  if (!(await confirmAction(`确认禁用卡密 ${item.key}？`))) return;
  const data = await run(() => api.disableCardKey(item.id));
  if (data !== null) await load();
}

async function enable(item) {
  const data = await run(() => api.enableCardKey(item.id));
  if (data !== null) await load();
}

async function extendOne(item) {
  const days = askDays();
  if (!days) return;
  await extendRows([item], days);
}

async function extendSelected() {
  const days = askDays();
  if (!days) return;
  await extendRows(selectedRows.value, days);
}

async function extendRows(items, days) {
  notice.value = '';
  for (const item of items) {
    await run(() => api.updateCardKey(item.id, { expires_at: addDays(item.expires_at, days) }));
  }
  notice.value = `已为 ${items.length} 个卡密增加 ${days} 天`;
  await load();
}

async function deleteSelected() {
  if (!selectedIds.value.length) return;
  if (!(await confirmAction(`确认删除选中的 ${selectedIds.value.length} 个卡密？此操作不可恢复。`))) return;
  const data = await run(() => api.bulkDeleteCardKeys(selectedIds.value));
  if (data !== null) {
    notice.value = `已删除 ${data.deleted || selectedIds.value.length} 个卡密`;
    selectedIds.value = [];
    await load();
  }
}

function toggleAll(event) {
  const visibleIds = filteredRows.value.map((item) => item.id);
  if (event.target.checked) {
    selectedIds.value = Array.from(new Set([...selectedIds.value, ...visibleIds]));
  } else {
    selectedIds.value = selectedIds.value.filter((id) => !visibleIds.includes(id));
  }
}

function copySelected() {
  copyKeys(selectedRows.value.length ? selectedRows.value : filteredRows.value);
}

async function copyKeys(items) {
  const text = items.map((item) => item.key).join('\n');
  if (!text) return;
  try {
    await navigator.clipboard.writeText(text);
    notice.value = `已复制 ${items.length} 个卡密`;
  } catch {
    notice.value = '当前浏览器不允许直接复制，请使用导出功能';
  }
}

function exportSelected() {
  const items = selectedRows.value.length ? selectedRows.value : filteredRows.value;
  const header = ['卡密', '状态', '到期时间', '最大客户端', '备注'];
  const lines = [header, ...items.map((item) => [item.key, statusText(item), item.expires_at || '', item.max_devices, item.note || ''])];
  const csv = lines.map((line) => line.map(csvCell).join(',')).join('\n');
  const blob = new Blob([`\ufeff${csv}`], { type: 'text/csv;charset=utf-8' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = `卡密导出-${new Date().toISOString().slice(0, 10)}.csv`;
  link.click();
  URL.revokeObjectURL(url);
}

function statusKind(item) {
  if (item.status === 'disabled') return 'disabled';
  if (isExpired(item.expires_at)) return 'expired';
  return 'active';
}

function statusText(item) {
  if (item.status === 'disabled') return '已禁用';
  if (isExpired(item.expires_at)) return '已过期';
  if (item.status === 'active') return '可使用';
  return item.status || '未知';
}

function isExpired(value) {
  return isServerTimeExpired(value);
}

function formatTime(value) {
  return formatServerTime(value, '永久');
}

function askDays() {
  const raw = window.prompt('请输入要增加的天数', '30');
  const days = Number(raw);
  return Number.isFinite(days) && days > 0 ? Math.floor(days) : 0;
}

function addDays(value, days) {
  const parsed = parseServerTime(value);
  const base = parsed && parsed.getTime() > Date.now() ? parsed : new Date();
  base.setDate(base.getDate() + days);
  return base.toISOString();
}

function csvCell(value) {
  return `"${String(value ?? '').replaceAll('"', '""')}"`;
}

function confirmAction(message) {
  return Promise.resolve(window.confirm(message));
}

onMounted(load);
</script>
