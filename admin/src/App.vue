<template>
  <LoginPage v-if="!isAuthed" @login="handleLogin" />
  <div v-else class="app-shell">
    <aside class="sidebar">
      <h1>Lezhi Admin</h1>
      <button
        v-for="item in navItems"
        :key="item.key"
        type="button"
        :class="{ active: activePage === item.key }"
        @click="activePage = item.key"
      >
        <span>{{ item.icon }}</span>{{ item.label }}
      </button>
      <button type="button" class="logout-btn" @click="logout">退出登录</button>
    </aside>
    <main class="content">
      <component :is="currentPage" />
    </main>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue';
import { api } from './api';
import LoginPage from './pages/LoginPage.vue';
import DashboardPage from './pages/DashboardPage.vue';
import CardKeysPage from './pages/CardKeysPage.vue';
import ClientBindingsPage from './pages/ClientBindingsPage.vue';
import VersionsPage from './pages/VersionsPage.vue';
import EventLogsPage from './pages/EventLogsPage.vue';

const navItems = [
  { key: 'dashboard', label: '仪表盘', icon: '[]', component: DashboardPage },
  { key: 'licenses', label: '卡密管理', icon: '##', component: CardKeysPage },
  { key: 'clients', label: '客户端绑定', icon: '<>', component: ClientBindingsPage },
  { key: 'releases', label: '版本发布', icon: '>>', component: VersionsPage },
  { key: 'events', label: '事件日志', icon: '--', component: EventLogsPage }
];

const isAuthed = ref(Boolean(localStorage.getItem('admin_token')));
const activePage = ref('dashboard');
const currentPage = computed(
  () => navItems.find((item) => item.key === activePage.value)?.component || DashboardPage
);

function handleLogin(token) {
  localStorage.setItem('admin_token', token);
  isAuthed.value = true;
}

async function logout() {
  try {
    await api.logout();
  } catch {
    // 本地退出优先，服务端会话过期时忽略错误。
  }
  localStorage.removeItem('admin_token');
  isAuthed.value = false;
}
</script>
