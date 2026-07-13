import request from './request'
import { getStoredUserId } from '../utils/user'
import { buildLearningPathProfilePayload } from '../utils/profile'

const FALLBACK_USER_ID = 9

function resolvePathUserId(params = {}) {
  const raw = params.userId ?? params.user_id ?? getStoredUserId() ?? FALLBACK_USER_ID
  const numericId = Number(raw)
  return Number.isFinite(numericId) && numericId > 0 ? numericId : FALLBACK_USER_ID
}

export function getCurrentProfile() {
  const params = {}
  const userId = getStoredUserId()
  if (userId != null) {
    params.userId = userId
  }

  return request({
    url: '/api/ml/profile/current',
    method: 'GET',
    params,
  })
}

export function generateLearningPath(learningGoal, profileData = {}) {
  const payload = {
    profile: buildLearningPathProfilePayload(profileData, learningGoal),
  }

  const userId = getStoredUserId()
  if (userId != null) {
    payload.userId = userId
  }

  return request({
    url: '/api/ml/learning-path/generate',
    method: 'POST',
    data: payload,
  })
}

export function getProfileSchema() {
  return request({
    url: '/profile/schema',
    method: 'GET',
  })
}

export function updateUserProfile(data) {
  return request({
    url: '/profile/update',
    method: 'POST',
    data,
  })
}

export function getLearningPathDetail(params) {
  return request({
    url: '/path/detail',
    method: 'GET',
    params,
  })
}

export function getUserPathList(params = {}) {
  const userId = resolvePathUserId(params)
  const rest = { ...params }
  delete rest.user_id

  return request({
    url: '/path/list',
    method: 'GET',
    params: {
      ...rest,
      userId,
    },
  })
}

export function deleteLearningPath(params = {}) {
  const pathId = params.pathId ?? params.path_id
  if (pathId == null || pathId === '') {
    return Promise.reject(new Error('pathId is required'))
  }

  return request({
    // Keep the identifier in the URL so DELETE remains correct even when a
    // transport wrapper only serializes `params` for GET requests.
    url: `/path/delete?pathId=${encodeURIComponent(String(pathId))}`,
    method: 'DELETE',
  })
}

export function updatePathProgress(data) {
  return request({
    url: '/path/progress/update',
    method: 'POST',
    data,
  })
}

export function getPathProgress(params) {
  return request({
    url: '/path/progress',
    method: 'GET',
    params,
  })
}

export function getNodeResources(params) {
  return request({
    url: '/path/resources',
    method: 'GET',
    params,
  })
}

export function getRecommendedPaths(params) {
  return request({
    url: '/path/recommend',
    method: 'GET',
    params,
  })
}

export function submitPathFeedback(data) {
  return request({
    url: '/path/feedback',
    method: 'POST',
    data,
  })
}

export default {
  getCurrentProfile,
  generateLearningPath,
  getProfileSchema,
  updateUserProfile,
  getLearningPathDetail,
  getUserPathList,
  deleteLearningPath,
  updatePathProgress,
  getPathProgress,
  getNodeResources,
  getRecommendedPaths,
  submitPathFeedback,
}
