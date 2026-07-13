import { getUserInfo } from '../api/auth'
import { getCurrentProfile, getUserPathList } from '../api/path'
import { getEvaluationHistory } from '../api/evaluation'
import { listTasks } from '../api/producer'
import { adaptPathListResponse } from './path'

export const KNOWLEDGE_LEVEL_LABELS = {
  beginner: '入门',
  foundation: '基础',
  intermediate: '中级',
  advanced: '高级',
}

const PATH_STATUS_LABELS = {
  active: '进行中',
  completed: '已完成',
}

const PRODUCER_STATUS_LABELS = {
  pending: '等待中',
  running: '生成中',
  completed: '已完成',
  failed: '失败',
}

export function formatDate(value) {
  if (!value) return '未知时间'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value
  return date.toLocaleString('zh-CN')
}

export function pathStatusText(status) {
  return PATH_STATUS_LABELS[status] || status || '未知'
}

export function producerStatusText(status) {
  return PRODUCER_STATUS_LABELS[status] || status || '未知'
}

export function knowledgeLevelText(level) {
  if (!level) return '未设置'
  return KNOWLEDGE_LEVEL_LABELS[level] || level
}

export function summarizeRequirement(text, maxLength = 80) {
  const value = String(text || '').trim()
  if (!value) return '无额外要求'
  return value.length > maxLength ? `${value.slice(0, maxLength)}...` : value
}

export function summarizeText(text, maxLength = 100) {
  const value = String(text || '').trim()
  if (!value) return ''
  return value.length > maxLength ? `${value.slice(0, maxLength)}...` : value
}

export function formatAccuracy(value) {
  if (value == null || Number.isNaN(Number(value))) return '正确率 -'
  const num = Number(value)
  const percent = num <= 1 ? Math.round(num * 100) : Math.round(num)
  return `正确率 ${percent}%`
}

export function parseProfileSummary(raw = {}) {
  const profile = raw.profile || raw || {}
  return {
    major: profile.major || '',
    grade: profile.grade || '',
    course: profile.course || '',
    goal: profile.goal || '',
    weak_points: Array.isArray(profile.weak_points) ? profile.weak_points : [],
    preference: profile.preference || '',
    cognitive_style: profile.cognitive_style || '',
    knowledge_level: profile.knowledge_level || '',
  }
}

export function hasProfileSummary(profile) {
  if (!profile) return false
  const weakPoints = profile.weak_points
  return !!(
    profile.major
    || profile.course
    || profile.goal
    || (Array.isArray(weakPoints) && weakPoints.length)
  )
}

export function weakPointsPreview(weakPoints, limit = 3) {
  if (!Array.isArray(weakPoints) || !weakPoints.length) return []
  return weakPoints
    .slice(0, limit)
    .map((item) => (typeof item === 'string' ? item : item.name || item.label || ''))
    .filter(Boolean)
}

export function buildStatistics(pathItems, pathTotal, evaluationItems, evaluationTotal, producerTaskCount) {
  const paths = Array.isArray(pathItems) ? pathItems : []
  const evaluations = Array.isArray(evaluationItems) ? evaluationItems : []
  const progressValues = paths.map((item) => Number(item.progress) || 0)
  const scores = evaluations
    .map((item) => Number(item.score))
    .filter((value) => Number.isFinite(value))

  return {
    learningPathCount: Number(pathTotal) || paths.length,
    completedPathCount: paths.filter((item) => item.status === 'completed').length,
    averagePathProgress: progressValues.length
      ? Math.round(progressValues.reduce((sum, value) => sum + value, 0) / progressValues.length)
      : 0,
    evaluationCount: Number(evaluationTotal) || evaluations.length,
    averageScore: scores.length
      ? Math.round((scores.reduce((sum, value) => sum + value, 0) / scores.length) * 10) / 10
      : 0,
    producerTaskCount: Number(producerTaskCount) || 0,
  }
}

export function pickCurrentPath(items) {
  const paths = Array.isArray(items) ? items : []
  if (!paths.length) return null
  return paths.find((item) => item.status === 'active') || paths[0]
}

function settleError(result, label) {
  if (result.status === 'fulfilled') return null
  const reason = result.reason
  const message = reason?.message || String(reason || '未知错误')
  return `${label}：${message}`
}

export async function fetchDashboardData() {
  const results = await Promise.allSettled([
    getUserInfo(),
    getCurrentProfile(),
    getUserPathList(),
    getEvaluationHistory(),
    listTasks({ limit: 5 }),
  ])

  const errors = {}

  let user = null
  if (results[0].status === 'fulfilled') {
    user = results[0].value
  } else {
    errors.user = settleError(results[0], '用户信息加载失败')
  }

  let profile = null
  if (results[1].status === 'fulfilled') {
    profile = parseProfileSummary(results[1].value)
  } else {
    errors.profile = settleError(results[1], '学习画像加载失败')
  }

  let paths = { items: [], total: 0 }
  if (results[2].status === 'fulfilled') {
    paths = adaptPathListResponse(results[2].value)
  } else {
    errors.paths = settleError(results[2], '学习路径加载失败')
  }

  let evaluations = { items: [], total: 0 }
  if (results[3].status === 'fulfilled') {
    const response = results[3].value || {}
    const items = response.items || []
    evaluations = {
      items,
      total: Number(response.total) || items.length,
    }
  } else {
    errors.evaluations = settleError(results[3], '评测记录加载失败')
  }

  let tasks = { items: [], total: 0 }
  if (results[4].status === 'fulfilled') {
    const response = results[4].value || {}
    const items = response.items || []
    tasks = {
      items,
      total: Number(response.total) || items.length,
    }
  } else {
    errors.tasks = settleError(results[4], '生成任务加载失败')
  }

  return {
    user,
    profile,
    paths,
    evaluations,
    tasks,
    errors,
  }
}

export function buildResourceQuery(profile) {
  if (profile?.course) {
    return { keyword: profile.course, sort: 'default' }
  }
  const weakPoints = weakPointsPreview(profile?.weak_points, 1)
  if (weakPoints.length) {
    return { keyword: weakPoints[0], sort: 'default' }
  }
  return { sort: 'hot' }
}
