import { ref } from 'vue';

export function useAsync() {
  const loading = ref(false);
  const error = ref('');

  async function run(task) {
    loading.value = true;
    error.value = '';
    try {
      return await task();
    } catch (err) {
      error.value = err?.message || '操作失败';
      return null;
    } finally {
      loading.value = false;
    }
  }

  return { loading, error, run };
}
