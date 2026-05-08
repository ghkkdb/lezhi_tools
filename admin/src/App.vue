<template>
  <LoginPage v-if="!isAuthed" @login="handleLogin" />
  <div v-else class="app-shell">
    <aside class="sidebar">
      <div class="brand">
        <div class="brand-mark">LZ</div>
        <div>
          <strong>Lezhi Admin</strong>
          <span>授权与活跃看板</span>
        </div>
      </div>

      <nav class="nav" aria-label="后台导航">
        <button
          v-for="item in navItems"
          :key="item.key"
          type="button"
          :class="{ active: activePage === item.key }"
          @click="activePage = item.key"
        >
          <span>{{ item.icon }}</span>{{ item.label }}
        </button>
      </nav>

      <button type="button" class="logout" @click="logout">退出登录</button>
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
  { key: 'dashboard', label: '仪表盘', icon: '总', component: DashboardPage },
  { key: 'licenses', label: '卡密管理', icon: '卡', component: CardKeysPage },
  { key: 'clients', label: '客户端绑定', icon: '端', component: ClientBindingsPage },
  { key: 'releases', label: '版本发布', icon: '版', component: VersionsPage },
  { key: 'events', label: '活跃日志', icon: '活', component: EventLogsPage }
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
    // 本地退出优先。
  }
  localStorage.removeItem('admin_token');
  isAuthed.value = false;
}
</script>
