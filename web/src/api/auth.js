import request from './request'
import { userStore } from '../stores/userStore'
import {
  clearAuthSession,
  normalizeUserInfo,
  parseAuthResponse,
  saveAuthSession,
} from '../utils/user'

function getData(res) {
  return res?.data || res || {}
}

function persistUserInfo(userSource) {
  const token = localStorage.getItem('token')
  const userInfo = normalizeUserInfo(userSource)
  localStorage.setItem('userInfo', JSON.stringify(userInfo))
  window.dispatchEvent(new Event('userInfoUpdated'))
  if (token) {
    userStore.updateUserInfo({ ...userInfo, token })
  }
  return userInfo
}

export async function login({ email, password }) {
  const res = await request({
    url: '/api/auth/login',
    method: 'POST',
    data: { email, password },
  })

  const { token, user, raw } = parseAuthResponse(res)

  if (!token) {
    throw new Error('登录失败：后端未返回 token')
  }

  const userInfo = saveAuthSession(token, user)
  userStore.updateUserInfo({ ...userInfo, token })

  return { ...raw, access_token: token, user: userInfo }
}

export async function register({ username, email, password }) {
  const res = await request({
    url: '/api/auth/register',
    method: 'POST',
    data: { username, email, password },
  })

  const { token, user, raw } = parseAuthResponse(res)
  if (token) {
    const userInfo = saveAuthSession(token, user)
    return { ...raw, access_token: token, user: userInfo }
  }

  return getData(res)
}

export async function getUserInfo() {
  const res = await request({
    url: '/api/user/info',
    method: 'GET',
  })

  const data = getData(res)
  return persistUserInfo(data)
}

export async function updateUserInfo({ nickname, gender, phone, avatar }) {
  const res = await request({
    url: '/api/user/info',
    method: 'PUT',
    data: { nickname, gender, phone, avatar },
  })

  const data = getData(res)
  const oldUserInfo = JSON.parse(localStorage.getItem('userInfo') || '{}')

  const merged = normalizeUserInfo({
    ...oldUserInfo,
    ...data,
    nickname: data.nickname ?? nickname ?? oldUserInfo.nickname ?? '',
    gender: data.gender ?? gender ?? oldUserInfo.gender ?? '',
    phone: data.phone ?? phone ?? oldUserInfo.phone ?? '',
    avatar: data.avatar ?? avatar ?? oldUserInfo.avatar ?? '',
  })

  localStorage.setItem('userInfo', JSON.stringify(merged))
  window.dispatchEvent(new Event('userInfoUpdated'))

  const token = localStorage.getItem('token')
  if (token) {
    userStore.updateUserInfo({ ...merged, token })
  }

  return merged
}

export function logout() {
  clearAuthSession()
  userStore.updateUserInfo(null)
}
