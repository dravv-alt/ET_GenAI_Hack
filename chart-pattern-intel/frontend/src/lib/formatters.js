export function fmtPrice(value, currency = 'INR', locale = 'en-IN') {
  if (value == null || Number.isNaN(Number(value))) return '-';
  const amount = Number(value);
  try {
    return new Intl.NumberFormat(locale, {
      style: 'currency',
      currency,
      currencyDisplay: 'code',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(amount);
  } catch {
    return `${currency} ${amount.toLocaleString(locale, {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    })}`;
  }
}

export function fmtPct(value) {
  if (value == null || Number.isNaN(Number(value))) return '-';
  return `${(Number(value) * 100).toFixed(2)}%`;
}

export function fmtDate(value) {
  if (!value) return '-';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return String(value);
  return date.toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: '2-digit' });
}

export function fmtTime(timeZone = 'Asia/Kolkata', locale = 'en-IN') {
  const date = new Date();
  try {
    return new Intl.DateTimeFormat(locale, {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      hour12: false,
      timeZone,
      timeZoneName: 'short',
    }).format(date);
  } catch {
    return date.toLocaleTimeString(locale, {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      hour12: false,
    });
  }
}

export function fmtTimeZoneLabel(timeZone = 'Asia/Kolkata', locale = 'en-IN') {
  try {
    const parts = new Intl.DateTimeFormat(locale, {
      timeZone,
      timeZoneName: 'short',
    }).formatToParts(new Date());
    const tz = parts.find((part) => part.type === 'timeZoneName');
    return tz?.value || timeZone;
  } catch {
    return timeZone;
  }
}
