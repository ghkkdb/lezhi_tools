const API_BASE = '/api';

const ERROR_TEXT = {
  not_authenticated: '请先登录后台',
  session_expired: '登录已过期，请重新登录',
  invalid_credentials: '账号或密码错误',
  license_key_exists: '卡密已存在',
  bulk_create_cannot_use_fixed_key: '批量生成不能指定固定卡密',
  license_not_found: '卡密不存在',
  release_exists: '版本号已存在',
  release_not_found: '暂无可用版本'
};

async function request(path, options = {}) {
  const token = localStorage.getItem('admin_token');
  const headers = {
    'Content-Type': 'application/json',
    ...(options.headers || {})
  };

  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }

  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers
  });

  const text = await response.text();
  const data = text ? JSON.parse(text) : null;

  if (!response.ok) {
    const detail = data?.message || data?.detail || '';
    throw new Error(ERROR_TEXT[detail] || `请求失败，状态码 ${response.status}`);
  }

  return data;
}

export const api = {
  login(payload) {
    return request('/admin/login', {
      method: 'POST',
      body: JSON.stringify(payload)
    });
  },
  me() {
    return request('/admin/me');
  },
  logout() {
    return request('/admin/logout', { method: 'POST' });
  },
  dashboard() {
    return request('/admin/stats');
  },
  cardKeys(params = {}) {
    return request(`/admin/licenses${toQuery(params)}`);
  },
  createCardKey(payload) {
    const expiresAt = payload.days
      ? new Date(Date.now() + Number(payload.days) * 24 * 60 * 60 * 1000).toISOString()
      : null;
    return request('/admin/licenses', {
      method: 'POST',
      body: JSON.stringify({
        count: Number(payload.count || 1),
        owner: payload.owner || '',
        max_devices: Number(payload.max_devices || 1),
        expires_at: expiresAt,
        note: payload.remark || payload.note || '',
        status: payload.status || 'active'
      })
    });
  },
  updateCardKey(id, payload) {
    return request(`/admin/licenses/${id}`, {
      method: 'PATCH',
      body: JSON.stringify(payload)
    });
  },
  disableCardKey(id) {
    return this.updateCardKey(id, { status: 'disabled' });
  },
  enableCardKey(id) {
    return this.updateCardKey(id, { status: 'active' });
  },
  bulkDeleteCardKeys(ids) {
    return request('/admin/licenses/bulk-delete', {
      method: 'POST',
      body: JSON.stringify({ ids })
    });
  },
  bindings(params = {}) {
    return request(`/admin/clients${toQuery(params)}`);
  },
  unbindClient(id) {
    return request(`/admin/clients/${id}/unbind`, { method: 'POST' });
  },
  versions() {
    return request('/admin/releases');
  },
  publishVersion(payload) {
    return request('/admin/releases', {
      method: 'POST',
      body: JSON.stringify({
        version: payload.version,
        platform: 'windows',
        download_url: payload.download_url,
        changelog: payload.release_note || payload.changelog || '',
        mandatory: Boolean(payload.force_update || payload.mandatory),
        active: true
      })
    });
  },
  logs(params = {}) {
    return request(`/admin/events${toQuery(params)}`);
  }
};

function toQuery(params) {
  const query = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== '') {
      query.set(key, value);
    }
  });
  const text = query.toString();
  return text ? `?${text}` : '';
}
