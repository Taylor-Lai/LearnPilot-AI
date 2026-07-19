const DEFAULT_TIMEOUT_MS = 30000
const UNAUTHORIZED_LOCK_MS = 2000

const AUTH_SKIP_401_PATHS = ['/api/auth/login', '/api/auth/register']

const HTTP_STATUS_MESSAGES = {
  400: '请求参数错误',
  401: '未授权，请重新登录',
  403: '禁止访问',
  404: '资源不存在',
  408: '请求超时',
  409: '资源冲突',
  422: '请求参数校验失败',
  429: '请求过于频繁',
  500: '服务器内部错误',
  502: '网关错误',
  503: '服务暂不可用',
  504: '网关超时',
}

let routerInstance = null
let unauthorizedHandling = false

export function setRequestRouter(router) {
  routerInstance = router
}

function getApiHost() {
  return (import.meta.env.VITE_API_BASE_URL || '').replace(/\/$/, '')
}

function buildUrl(url, params) {
  if (!url) {
    throw new Error('请求地址 url 不能为空')
  }

  const path = url.startsWith('/') ? url : `/${url}`
  const host = getApiHost()
  let finalUrl = host ? `${host}${path}` : path

  if (params && Object.keys(params).length > 0) {
    const searchParams = new URLSearchParams()
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null && value !== '') {
        searchParams.append(key, String(value))
      }
    })
    const query = searchParams.toString()
    if (query) {
      finalUrl += finalUrl.includes('?') ? `&${query}` : `?${query}`
    }
  }

  return finalUrl
}

function getHttpStatusMessage(status) {
  return HTTP_STATUS_MESSAGES[status] || `请求失败，HTTP ${status}`
}

function stripHtmlToText(html) {
  return html
    .replace(/<script[\s\S]*?<\/script>/gi, ' ')
    .replace(/<style[\s\S]*?<\/style>/gi, ' ')
    .replace(/<[^>]+>/g, ' ')
    .replace(/\s+/g, ' ')
    .trim()
}

function formatDetail(detail) {
  if (detail == null) return ''
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail)) {
    return detail
      .map((item) => {
        if (typeof item === 'string') return item
        if (item && typeof item === 'object') {
          return item.msg || item.message || JSON.stringify(item)
        }
        return String(item)
      })
      .filter(Boolean)
      .join('；')
  }
  if (typeof detail === 'object') {
    return detail.message || detail.msg || JSON.stringify(detail)
  }
  return String(detail)
}

function extractJsonErrorMessage(parsed) {
  if (!parsed || typeof parsed !== 'object') return ''

  if (parsed.error?.message) {
    return typeof parsed.error.message === 'string'
      ? parsed.error.message
      : JSON.stringify(parsed.error.message)
  }

  const detail = formatDetail(parsed.detail)
  if (detail) return detail

  if (parsed.message) {
    return typeof parsed.message === 'string' ? parsed.message : JSON.stringify(parsed.message)
  }

  return ''
}

function buildErrorMessage(parsed, rawText, status) {
  const jsonMessage = extractJsonErrorMessage(parsed)
  if (jsonMessage) return jsonMessage

  const text = (rawText || '').trim()
  if (text) {
    if (text.startsWith('<')) {
      const plain = stripHtmlToText(text)
      if (plain) return plain.slice(0, 300)
    }
    return text.slice(0, 300)
  }

  return getHttpStatusMessage(status)
}

function parseResponseBody(text) {
  const rawText = text ?? ''

  if (!rawText.trim()) {
    return { parsed: null, rawText }
  }

  const trimmed = rawText.trim()
  if (trimmed.startsWith('{') || trimmed.startsWith('[')) {
    try {
      return { parsed: JSON.parse(rawText), rawText }
    } catch {
      return { parsed: null, rawText }
    }
  }

  return { parsed: null, rawText }
}

function coerceProfileWeakPoints(profile) {
  if (!profile || typeof profile !== 'object') return profile

  let weakPoints = profile.weak_points

  while (typeof weakPoints === 'string') {
    const trimmed = weakPoints.trim()
    if (!trimmed) {
      weakPoints = []
      break
    }

    try {
      weakPoints = JSON.parse(trimmed)
      continue
    } catch {
      try {
        weakPoints = JSON.parse(trimmed.replace(/'/g, '"'))
        continue
      } catch {
        weakPoints = []
        break
      }
    }
  }

  if (!Array.isArray(weakPoints)) {
    weakPoints = []
  }

  return {
    ...profile,
    weak_points: weakPoints.map((item) => String(item)),
  }
}

function prepareRequestBody(url, method, data) {
  if (!data || method.toUpperCase() === 'GET') return data
  if (typeof url !== 'string' || !url.includes('/api/v1/tutor/ask')) return data
  if (!data.profile) return data

  return {
    ...data,
    profile: coerceProfileWeakPoints(data.profile),
  }
}

function shouldSkip401Redirect(url) {
  return AUTH_SKIP_401_PATHS.some((item) => url.includes(item))
}

function releaseUnauthorizedLock() {
  setTimeout(() => {
    unauthorizedHandling = false
  }, UNAUTHORIZED_LOCK_MS)
}

function handleUnauthorized(url) {
  if (shouldSkip401Redirect(url)) return

  if (unauthorizedHandling) return
  unauthorizedHandling = true

  try {
    localStorage.removeItem('token')
    localStorage.removeItem('userInfo')
    window.dispatchEvent(new Event('userInfoUpdated'))

    const currentPath = window.location.pathname
    const currentSearch = window.location.search
    const currentFullPath = `${currentPath}${currentSearch}`
    const routeMeta = routerInstance?.currentRoute?.value?.meta || {}
    const isProtectedRoute = Boolean(routeMeta.requiresAuth || routeMeta.requiresAdmin)

    if (currentPath === '/login' || currentPath === '/register') {
      releaseUnauthorizedLock()
      return
    }

    // A stale session must not make public product pages unusable. Clear the
    // invalid credentials, then keep the visitor on the current public page.
    if (!isProtectedRoute) {
      releaseUnauthorizedLock()
      return
    }

    if (routerInstance) {
      routerInstance
        .push({ name: 'login', query: { redirect: currentFullPath } })
        .catch(() => {})
        .finally(() => {
          releaseUnauthorizedLock()
        })
      return
    }

    const redirect = encodeURIComponent(currentFullPath)
    window.location.href = `/login?redirect=${redirect}`
    releaseUnauthorizedLock()
  } catch {
    releaseUnauthorizedLock()
  }
}

async function request(options = {}) {
  const token = localStorage.getItem('token')
  const {
    url,
    method = 'GET',
    params,
    data,
    headers = {},
    timeout = DEFAULT_TIMEOUT_MS,
  } = options

  const upperMethod = method.toUpperCase()
  const finalUrl = buildUrl(url, params)
  const isFormData = typeof FormData !== 'undefined' && data instanceof FormData

  const config = {
    method: upperMethod,
    headers: {
      Accept: 'application/json',
      ...(isFormData ? {} : { 'Content-Type': 'application/json' }),
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...headers,
    },
  }

  if (isFormData && config.headers['Content-Type']) {
    delete config.headers['Content-Type']
  }

  if (data && upperMethod !== 'GET') {
    const body = prepareRequestBody(url, upperMethod, data)

    config.body = isFormData ? body : JSON.stringify(body)
  }

  const controller = new AbortController()
  const timeoutId = setTimeout(() => controller.abort(), timeout)
  config.signal = controller.signal

  let response
  try {
    response = await fetch(finalUrl, config)
  } catch (error) {
    if (error.name === 'AbortError') {
      throw new Error(`请求超时（${timeout}ms）：${finalUrl}`)
    }
    throw error
  } finally {
    clearTimeout(timeoutId)
  }

  const status = response.status

  if (status === 204) {
    return {}
  }

  const text = await response.text()
  const { parsed, rawText } = parseResponseBody(text)

  if (status === 401) {
    handleUnauthorized(url)
    throw new Error(buildErrorMessage(parsed, rawText, status))
  }

  if (!response.ok) {
    throw new Error(buildErrorMessage(parsed, rawText, status))
  }

  if (parsed !== null) {
    return parsed
  }

  if (!rawText.trim()) {
    return {}
  }

  return rawText
}

export default request
