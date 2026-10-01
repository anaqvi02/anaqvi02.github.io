/* Calendar days in the project's timezone, independent of the visitor's clock zone. */
function projectEta(deadline, now = new Date()) {
 const match = /^(\d{4})-(\d{2})-(\d{2})$/.exec(deadline || '');
 if (!match || !Number.isFinite(now.getTime())) return null;
 const [, year, month, day] = match.map(Number);
 const target = new Date(Date.UTC(year, month - 1, day));
 if (target.getUTCFullYear() !== year || target.getUTCMonth() !== month - 1 || target.getUTCDate() !== day) return null;
 const parts = new Intl.DateTimeFormat('en-US', {timeZone:'America/Toronto', year:'numeric', month:'numeric', day:'numeric'}).formatToParts(now);
 const calendar = Object.fromEntries(parts.map(part => [part.type, part.value]));
 const today = Date.UTC(+calendar.year, +calendar.month - 1, +calendar.day);
 const days = Math.round((target.getTime() - today) / 86400000);
 if (days <= 0) return 'ASAP';
 if (days < 7) return days + (days === 1 ? ' DAY' : ' DAYS');
 const weeks = Math.ceil(days / 7);
 return weeks + (weeks === 1 ? ' WEEK' : ' WEEKS');
}
