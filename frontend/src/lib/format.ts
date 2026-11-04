export const TIME_ZONE = "America/Sao_Paulo";

export function formatNumber(value: number | null | undefined, digits = 0) {
  if (value == null) return "—";
  return new Intl.NumberFormat("pt-BR", { minimumFractionDigits: digits, maximumFractionDigits: digits }).format(value);
}

export function time(value: string) {
  return new Intl.DateTimeFormat("pt-BR", { timeZone: TIME_ZONE, hour: "2-digit", minute: "2-digit" }).format(new Date(value));
}

export function dayKey(value: Date | string) {
  const parts = new Intl.DateTimeFormat("en-CA", { timeZone: TIME_ZONE, year: "numeric", month: "2-digit", day: "2-digit" }).formatToParts(new Date(value));
  const part = (type: string) => parts.find((item) => item.type === type)?.value;
  return `${part("year")}-${part("month")}-${part("day")}`;
}

export function tomorrowKey(now: Date) {
  const date = new Date(`${dayKey(now)}T12:00:00-03:00`);
  date.setUTCDate(date.getUTCDate() + 1);
  return dayKey(date);
}

export function dayLabel(date: string, today: string) {
  if (date === today) return "Hoje";
  const label = new Intl.DateTimeFormat("pt-BR", { timeZone: TIME_ZONE, weekday: "short" }).format(new Date(`${date}T12:00:00-03:00`));
  return label.charAt(0).toUpperCase() + label.slice(1).replace(".", "");
}
