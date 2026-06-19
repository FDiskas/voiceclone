// Short human-readable duration, e.g. 45 → "45s", 95 → "1m 35s".
export function formatDuration(seconds: number): string {
  const total = Math.max(0, Math.ceil(seconds));
  if (total < 60) return `${total}s`;
  const minutes = Math.floor(total / 60);
  const rest = total % 60;
  return `${minutes}m ${rest.toString().padStart(2, "0")}s`;
}

// Human-readable byte size, e.g. 4096 → "4.0 KB", 0 → "0 B".
export function formatBytes(bytes: number): string {
  if (bytes <= 0) return "0 B";
  const units = ["B", "KB", "MB", "GB"];
  const i = Math.min(Math.floor(Math.log(bytes) / Math.log(1024)), units.length - 1);
  return `${(bytes / 1024 ** i).toFixed(i === 0 ? 0 : 1)} ${units[i]}`;
}
