import request from './request'

const DEFAULT_COURSE_ID = 1

function normalizeQuestionType(type) {
  const value = String(type || '').toLowerCase()
  if (value === 'true_false' || value === 'judgment' || value === 'judge') {
    return 'true_false'
  }
  if (value === 'single_choice' || value === 'multiple_choice') {
    return 'single_choice'
  }
  return 'short_answer'
}

function buildQuestionOptions(question, type) {
  if (type === 'true_false') {
    return [
      { value: 'true', text: '正确' },
      { value: 'false', text: '错误' },
    ]
  }

  if (Array.isArray(question.options) && question.options.length) {
    return question.options.map((option, index) => {
      if (typeof option === 'string') {
        return { value: String.fromCharCode(65 + index), text: option }
      }
      return {
        value: option.value || String.fromCharCode(65 + index),
        text: option.text || option.label || String(option.value || ''),
      }
    })
  }

  return []
}

function adaptCourseQuestion(question) {
  const type = normalizeQuestionType(question.question_type)
  return {
    id: question.id,
    type,
    stem: question.stem,
    knowledge_point: question.knowledge_point_id
      ? `知识点 #${question.knowledge_point_id}`
      : null,
    options: buildQuestionOptions(question, type),
  }
}

export async function startEvaluation(params = {}) {
  const courseId = Number(params.course_id) > 0 ? Number(params.course_id) : DEFAULT_COURSE_ID
  const limit = Number(params.limit) > 0 ? Number(params.limit) : 5

  const rawQuestions = await request({
    url: `/api/v1/courses/${courseId}/assessment/questions`,
    method: 'GET',
    params: { limit },
  })

  const sourceQuestions = Array.isArray(rawQuestions) ? rawQuestions.slice(0, limit) : []

  return {
    path_id: params.path_id ?? null,
    course_id: courseId,
    questions: sourceQuestions.map(adaptCourseQuestion),
  }
}

export async function submitEvaluation(data) {
  const answers = Array.isArray(data.answers) ? data.answers : []

  const response = await request({
    url: '/api/v1/evaluations/submit',
    method: 'POST',
    data: {
      user_id: data.user_id,
      course_id: data.course_id,
      path_id: data.path_id,
      answers,
      completed_resource_count: data.completed_resource_count || 0,
      study_minutes: data.study_minutes || 10,
    },
  })

  return {
    ...response,
    weak_points: response.profile_update?.weak_points || [],
  }
}

export function getEvaluationHistory() {
  return request({
    url: '/api/v1/evaluations/history',
    method: 'GET',
  })
}

export function getEvaluationDetail(evaluationId) {
  return request({
    url: `/api/v1/evaluations/${evaluationId}`,
    method: 'GET',
  })
}

export default {
  startEvaluation,
  submitEvaluation,
  getEvaluationHistory,
  getEvaluationDetail,
}
