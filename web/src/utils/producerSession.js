const STORAGE_KEY = 'currentProducerTaskId'

export function getCurrentProducerTaskId() {
  try {
    const raw = sessionStorage.getItem(STORAGE_KEY)
    return raw && raw.trim() ? raw.trim() : null
  } catch {
    return null
  }
}

export function setCurrentProducerTaskId(taskId) {
  if (!taskId) return
  sessionStorage.setItem(STORAGE_KEY, String(taskId))
}

export function clearCurrentProducerTaskId() {
  sessionStorage.removeItem(STORAGE_KEY)
}
