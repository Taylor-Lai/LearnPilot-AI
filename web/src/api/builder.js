import request from './request'
import { getStoredUserId } from '../utils/user'

function attachOptionalFields(payload, data) {
  const sessionId = (data.session_id || '').trim()
  if (sessionId) {
    payload.session_id = sessionId
  }

  const userId = getStoredUserId()
  if (userId != null) {
    payload.userId = userId
  }

  return payload
}

export function getProfileQuestions() {
  return request({
    url: '/api/ml/profile/questions',
    method: 'GET',
  })
}

export function sendProfileAnswer(data) {
  const payload = attachOptionalFields(
    {
      question_id: data.question_id,
      question: data.question || '',
      answer: data.answer,
    },
    data,
  )

  return request({
    url: '/api/ml/profile/answer',
    method: 'POST',
    data: payload,
  })
}

export function generateProfile(data) {
  const payload = attachOptionalFields(
    {
      answers: (data.answers || []).map((item) => ({
        question_id: item.question_id,
        question: item.question || '',
        answer: item.answer || '',
      })),
    },
    data,
  )

  return request({
    url: '/api/ml/profile/generate',
    method: 'POST',
    data: payload,
  })
}

export function startProfileBuilder() {
  return request({
    url: '/profile-builder/start',
    method: 'POST',
  })
}

export function sendBuilderAnswer({ sessionId, answer }) {
  return request({
    url: '/profile-builder/answer',
    method: 'POST',
    data: { session_id: sessionId, answer },
  })
}

export function getBuilderProfile(sessionId) {
  return request({
    url: '/profile-builder/result',
    method: 'GET',
    params: { session_id: sessionId },
  })
}

export function regenerateProfile(sessionId) {
  return request({
    url: '/profile-builder/regenerate',
    method: 'POST',
    data: { session_id: sessionId },
  })
}

export default {
  getProfileQuestions,
  sendProfileAnswer,
  generateProfile,
  startProfileBuilder,
  sendBuilderAnswer,
  getBuilderProfile,
  regenerateProfile,
}
