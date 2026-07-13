import request from './request'
import { getStoredUserId } from '../utils/user'
import { buildLearningPathProfilePayload } from '../utils/profile'

const DEFAULT_COURSE_ID = 1
const FALLBACK_USER_ID = 9

function normalizeWeakPoints(value) {
  if (value == null || value === '') return []

  if (Array.isArray(value)) {
    return value
      .map((item) => {
        if (typeof item === 'string') return item.trim()
        if (item && typeof item === 'object') {
          return String(item.name || item.label || item.knowledge_point || '').trim()
        }
        return ''
      })
      .filter(Boolean)
  }

  if (typeof value !== 'string') return []

  let current = value.trim()
  if (!current) return []

  for (let attempt = 0; attempt < 3; attempt += 1) {
    const candidates = [current, current.replace(/'/g, '"')]

    for (const candidate of candidates) {
      try {
        const parsed = JSON.parse(candidate)
        if (Array.isArray(parsed)) {
          return parsed.map((item) => String(item).trim()).filter(Boolean)
        }
        if (typeof parsed === 'string') {
          current = parsed.trim()
          break
        }
      } catch {
        // try next candidate
      }
    }

    if (!current.startsWith('[') && !current.startsWith('{')) {
      break
    }
  }

  if (current.includes('、')) {
    return current.split('、').map((item) => item.trim()).filter(Boolean)
  }
  if (current.includes(',')) {
    return current.split(',').map((item) => item.trim()).filter(Boolean)
  }

  return [current]
}

function buildTutorProfile(profile) {
  if (!profile) return undefined

  const payload = buildLearningPathProfilePayload(profile)
  const weakPoints = normalizeWeakPoints(payload.weak_points ?? profile.weak_points)

  return {
    major: payload.major || null,
    grade: payload.grade || null,
    course: payload.course || null,
    goal: payload.goal || null,
    weak_points: weakPoints,
    preference: payload.preference || null,
    cognitive_style: payload.cognitive_style || null,
    knowledge_level: payload.knowledge_level || null,
  }
}

function resolveUserId(userId) {
  if (userId != null && userId !== '') {
    const numericId = Number(userId)
    if (Number.isFinite(numericId) && numericId > 0) {
      return numericId
    }
  }

  const storedId = getStoredUserId()
  if (storedId != null && storedId > 0) {
    return storedId
  }

  return FALLBACK_USER_ID
}

function resolveCourseId(courseId) {
  if (courseId != null && courseId !== '') {
    const numericId = Number(courseId)
    if (Number.isFinite(numericId) && numericId > 0) {
      return numericId
    }
  }

  return DEFAULT_COURSE_ID
}

function ensureWeakPointsArray(weakPoints) {
  let value = weakPoints

  while (typeof value === 'string') {
    const trimmed = value.trim()
    if (!trimmed) return []

    try {
      value = JSON.parse(trimmed)
      continue
    } catch {
      try {
        value = JSON.parse(trimmed.replace(/'/g, '"'))
        continue
      } catch {
        return []
      }
    }
  }

  if (!Array.isArray(value)) return []
  return value.map((item) => String(item))
}

export function askTutor({ question, profile, history = [], courseId, userId } = {}) {
  const tutorProfile = buildTutorProfile(profile)

  const body = {
    user_id: resolveUserId(userId),
    course_id: resolveCourseId(courseId),
    question,
    history: Array.isArray(history) ? [...history] : [],
  }

  if (tutorProfile) {
    const weakPoints = ensureWeakPointsArray(tutorProfile.weak_points)
    body.profile = {
      major: tutorProfile.major ?? null,
      grade: tutorProfile.grade ?? null,
      course: tutorProfile.course ?? null,
      goal: tutorProfile.goal ?? null,
      weak_points: [...weakPoints],
      preference: tutorProfile.preference ?? null,
      cognitive_style: tutorProfile.cognitive_style ?? null,
      knowledge_level: tutorProfile.knowledge_level ?? null,
    }
  }

  return request({
    url: '/api/v1/tutor/ask',
    method: 'POST',
    data: body,
  })
}

export default {
  askTutor,
}
