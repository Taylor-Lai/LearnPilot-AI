export function normalizeUserInfo(source = {}) {
  const id = source.id ?? source.user_id ?? source.userId ?? ''
  const username = source.username || ''
  const isAdminFlag =
    source.isAdmin === true ||
    source.is_admin === true ||
    source.isAdmin === 1 ||
    source.is_admin === 1 ||
    source.isAdmin === '1' ||
    source.is_admin === '1'

  return {
    id,
    userId: id,
    username,
    nickname: source.nickname || username,
    email: source.email || '',
    role:
      isAdminFlag || source.role === 'ADMIN' || source.role === 'admin'
        ? 'ADMIN'
        : source.role || 'USER',
    isAdmin: isAdminFlag || source.role === 'ADMIN' || source.role === 'admin',
    avatar: source.avatar || '',
    gender: source.gender || '',
    phone: source.phone || '',
  }
}

export function isAdminUser(userInfo = null) {
  if (!userInfo) return false
  const role = String(userInfo.role ?? '').trim().toLowerCase()
  return (
    userInfo.isAdmin === true ||
    userInfo.is_admin === true ||
    role === 'admin'
  )
}

export function getStoredUserInfo() {
  try {
    const raw = localStorage.getItem('userInfo')
    if (!raw) return null
    return JSON.parse(raw)
  } catch {
    return null
  }
}

export function getStoredUserId() {
  const info = getStoredUserInfo()
  if (!info) return null
  const id = info.id ?? info.userId ?? info.user_id
  if (id === '' || id == null) return null
  const numericId = Number(id)
  return Number.isFinite(numericId) ? numericId : null
}

export function saveAuthSession(token, userSource = {}) {
  localStorage.setItem('token', token)
  const userInfo = normalizeUserInfo(userSource)
  localStorage.setItem('userInfo', JSON.stringify(userInfo))
  window.dispatchEvent(new Event('userInfoUpdated'))
  return userInfo
}

export function clearAuthSession() {
  localStorage.removeItem('token')
  localStorage.removeItem('userInfo')
  sessionStorage.removeItem('profileBuilderSessionId')
  window.dispatchEvent(new Event('userInfoUpdated'))
}

export function parseAuthResponse(res) {
  const data = res?.data || res || {}
  const token = data.access_token || data.token || ''
  const user = data.user || data
  return { token, user, raw: data }
}
