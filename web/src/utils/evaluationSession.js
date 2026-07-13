const STORAGE_KEY = 'currentEvaluationId'

export function getCurrentEvaluationId() {
  try {
    const raw = sessionStorage.getItem(STORAGE_KEY)
    if (!raw) return null
    const id = Number(raw)
    return Number.isFinite(id) && id > 0 ? id : null
  } catch {
    return null
  }
}

export function setCurrentEvaluationId(evaluationId) {
  const id = Number(evaluationId)
  if (!Number.isFinite(id) || id <= 0) return
  sessionStorage.setItem(STORAGE_KEY, String(id))
}

export function clearCurrentEvaluationId() {
  sessionStorage.removeItem(STORAGE_KEY)
}
