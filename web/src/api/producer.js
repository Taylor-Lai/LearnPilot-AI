import request from './request'

export function createTask(data) {
  return request({
    url: '/producer/task',
    method: 'POST',
    data,
  })
}

export function getTaskStatus(taskId) {
  return request({
    url: `/producer/task/${taskId}`,
    method: 'GET',
  })
}

export function getTaskResult(taskId) {
  return request({
    url: `/producer/result/${taskId}`,
    method: 'GET',
  })
}

export function cancelTask(taskId) {
  return request({
    url: `/producer/task/${taskId}/cancel`,
    method: 'POST',
  })
}

export function retryTask(taskId) {
  return request({
    url: `/producer/task/${taskId}/retry`,
    method: 'POST',
  })
}

export async function downloadTaskExport(taskId, format = 'docx') {
  const host = (import.meta.env.VITE_API_BASE_URL || '').replace(/\/$/, '')
  const token = localStorage.getItem('token')
  const response = await fetch(`${host}/producer/export/${encodeURIComponent(taskId)}?format=${encodeURIComponent(format)}`, {
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  })
  if (!response.ok) {
    let message = `导出失败（HTTP ${response.status}）`
    try {
      const payload = await response.json()
      message = payload.detail || payload.message || message
    } catch {
      // Keep the HTTP status message when the server did not return JSON.
    }
    throw new Error(message)
  }
  return response.blob()
}

export async function listTasks(params = {}) {
  const limit = Number(params.limit) > 0 ? Number(params.limit) : 20
  return request({
    url: '/producer/tasks',
    method: 'GET',
    params: { limit },
  })
}

export function chatWithAI(data) {
  return request({
    url: '/producer/chat',
    method: 'POST',
    data: {
      message: data.message,
      session_id: data.session_id || data.sessionId || '',
      topic: data.topic || '学习主题',
    },
  })
}

export function getRoadmap(topic) {
  return request({
    url: '/producer/roadmap',
    method: 'GET',
    params: { topic },
  })
}

export function getExercises(topic) {
  return request({
    url: '/producer/exercises',
    method: 'GET',
    params: { topic },
  })
}

export function getVideos(topic) {
  return request({
    url: '/producer/videos',
    method: 'GET',
    params: { topic },
  })
}

export function getCodeExamples(topic, language) {
  return request({
    url: '/producer/code',
    method: 'GET',
    params: {
      topic,
      language,
    },
  })
}

export function runCode(data) {
  return request({
    url: '/producer/run',
    method: 'POST',
    data,
  })
}

export function getDatasets(keyword) {
  return request({
    url: '/producer/datasets',
    method: 'GET',
    params: { keyword },
  })
}

export default {
  createTask,
  cancelTask,
  retryTask,
  getTaskStatus,
  getTaskResult,
  downloadTaskExport,
  listTasks,
  chatWithAI,
  getRoadmap,
  getExercises,
  getVideos,
  getCodeExamples,
  runCode,
  getDatasets,
}
