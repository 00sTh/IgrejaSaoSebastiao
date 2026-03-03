interface CacheEntry {
  value: unknown
  expires: number
}

const DEFAULT_TTL = 300 // 5 minutes
const cache = new Map<string, CacheEntry>()

export function cacheGet<T>(key: string): T | null {
  const entry = cache.get(key)
  if (!entry) return null
  if (entry.expires <= Date.now()) {
    cache.delete(key)
    return null
  }
  return entry.value as T
}

export function cacheSet(key: string, value: unknown, ttlSeconds = DEFAULT_TTL): void {
  cache.set(key, { value, expires: Date.now() + ttlSeconds * 1000 })
}

export function cacheDelete(key: string): void {
  cache.delete(key)
}

export function cacheInvalidatePrefix(prefix: string): void {
  for (const key of cache.keys()) {
    if (key.startsWith(prefix)) cache.delete(key)
  }
}
