const TIME_FORMATTER = new Intl.DateTimeFormat('zh-CN', {
  timeZone: 'Asia/Shanghai',
  year: 'numeric',
  month: '2-digit',
  day: '2-digit',
  hour: '2-digit',
  minute: '2-digit',
  second: '2-digit',
  hour12: false
});

export function parseServerTime(value) {
  if (!value) return null;
  const text = String(value).trim();
  if (!text) return null;
  if (text.includes('T') || /[zZ]|[+-]\d{2}:\d{2}$/.test(text)) {
    return new Date(text);
  }
  return new Date(`${text.replace(' ', 'T')}Z`);
}

export function formatServerTime(value, fallback = '-') {
  const date = parseServerTime(value);
  if (!date || Number.isNaN(date.getTime())) return fallback;
  return TIME_FORMATTER.format(date).replaceAll('/', '-');
}

export function isServerTimeExpired(value) {
  const date = parseServerTime(value);
  return Boolean(date && !Number.isNaN(date.getTime()) && date.getTime() <= Date.now());
}
