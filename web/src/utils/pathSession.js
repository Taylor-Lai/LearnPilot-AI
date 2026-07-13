const STORAGE_KEY = 'currentLearningPathId'

export function getCurrentPathId() {
  try {
    const raw = sessionStorage.getItem(STORAGE_KEY)
    if (!raw) return null
    const id = Number(raw)
    return Number.isFinite(id) && id > 0 ? id : null
  } catch {
    return null
  }
}

export function setCurrentPathId(pathId) {
  const id = Number(pathId)
  if (!Number.isFinite(id) || id <= 0) return
  sessionStorage.setItem(STORAGE_KEY, String(id))
}

export function clearCurrentPathId() {
  sessionStorage.removeItem(STORAGE_KEY)
}
