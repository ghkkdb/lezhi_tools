<template>
  <main class="login-page">
    <section class="login-panel">
      <div class="login-copy">
        <span class="badge">Admin Console</span>
        <h1>乐知工具后台</h1>
        <p>管理卡密、客户端绑定、版本发布与事件审计。</p>
      </div>

      <form class="login-form" @submit.prevent="submit">
        <label>
          账号
          <input v-model.trim="form.username" autocomplete="username" placeholder="请输入管理员账号" required />
        </label>
        <label>
          密码
          <input
            v-model="form.password"
            type="password"
            autocomplete="current-password"
            placeholder="请输入密码"
            required
          />
        </label>
        <p v-if="error" class="form-error">{{ error }}</p>
        <button type="submit" class="primary-btn" :disabled="loading">
          {{ loading ? '登录中...' : '登录' }}
        </button>
      </form>
    </section>
  </main>
</template>

<script setup>
import { reactive } from 'vue';
import { api } from '../api';
import { useAsync } from '../composables/useAsync';

const emit = defineEmits(['login']);
const form = reactive({ username: '', password: '' });
const { loading, error, run } = useAsync();

async function submit() {
  const data = await run(() => api.login(form));
  const token = data?.token || data?.access_token;
  if (token) {
    emit('login', token);
  } else if (data) {
    error.value = '登录响应缺少 token';
  }
}
</script>
