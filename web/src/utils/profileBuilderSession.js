const SESSION_STORAGE_KEY = 'profileBuilderSessionId'

export function getProfileBuilderSessionId() {
  return sessionStorage.getItem(SESSION_STORAGE_KEY) || ''
}

export function setProfileBuilderSessionId(sessionId) {
  const normalized = (sessionId || '').trim()
  if (!normalized) return
  sessionStorage.setItem(SESSION_STORAGE_KEY, normalized)
}

export function clearProfileBuilderSessionId() {
  sessionStorage.removeItem(SESSION_STORAGE_KEY)
}
