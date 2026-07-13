// stores/userStore.js
import { reactive, readonly } from 'vue'
import { normalizeUserInfo, isAdminUser } from '../utils/user'

const state = reactive({
  isLoggedIn: false,
  userId: '',
  username: '',
  nickname: '',
  userRole: '',
  isAdmin: false,
  avatar: '',
  email: '',
})

const listeners = new Set()

function updateUserInfo(userInfo = null) {
  if (userInfo && (userInfo.token || localStorage.getItem('token'))) {
    const normalized = normalizeUserInfo(userInfo)
    state.isLoggedIn = true
    state.userId = normalized.id || normalized.userId || ''
    state.username = normalized.username || ''
    state.nickname = normalized.nickname || normalized.username || ''
    state.userRole = normalized.role || 'USER'
    state.isAdmin = isAdminUser(normalized)
    state.avatar = normalized.avatar || ''
    state.email = normalized.email || ''
  } else {
    state.isLoggedIn = false
    state.userId = ''
    state.username = ''
    state.nickname = ''
    state.userRole = ''
    state.isAdmin = false
    state.avatar = ''
    state.email = ''
  }

  listeners.forEach((fn) => {
    try {
      fn()
    } catch (e) {
      console.error('Listener error:', e)
    }
  })
}

function syncFromLocalStorage() {
  try {
    const token = localStorage.getItem('token')
    const userInfoStr = localStorage.getItem('userInfo')

    if (token && userInfoStr) {
      const userInfo = JSON.parse(userInfoStr)
      updateUserInfo({ ...userInfo, token })
    } else {
      updateUserInfo(null)
    }
  } catch (e) {
    console.error('syncFromLocalStorage error:', e)
    updateUserInfo(null)
  }
}

function subscribe(listener) {
  listeners.add(listener)
  return () => listeners.delete(listener)
}

syncFromLocalStorage()

window.addEventListener('storage', (e) => {
  if (e.key === 'token' || e.key === 'userInfo') {
    syncFromLocalStorage()
  }
})

window.addEventListener('userInfoUpdated', () => {
  syncFromLocalStorage()
})

export const userStore = {
  state: readonly(state),
  updateUserInfo,
  syncFromLocalStorage,
  subscribe,
}
