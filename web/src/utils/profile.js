function normalizeList(list, keyName = 'name', valueName = 'value') {
  if (!Array.isArray(list)) return []

  return list.map((item) => {
    if (typeof item === 'string') return { name: item, value: 0 }
    return {
      name: item.name || item.label || item[keyName] || '未命名',
      value: Number(item.value ?? item.score ?? item.percent ?? item[valueName] ?? 0),
      risk: Number(item.risk ?? item.value ?? item.score ?? 0),
    }
  })
}

/**
 * 合并后端 profile（扁平画像）与 dashboard（分析面板）为页面展示结构。
 */
export function normalizeProfileResult(raw = {}) {
  const profile = raw.profile || {}
  const dashboard = raw.dashboard || {}
  const data = { ...profile, ...dashboard }

  const profileGoal =
    typeof profile.goal === 'string' ? profile.goal : profile.goal?.analysis || ''

  const goalProgress =
    typeof data.goal === 'object' && data.goal?.progress != null
      ? Number(data.goal.progress)
      : Number(data.goal_progress ?? dashboard.goal?.progress ?? 0)

  const goalAnalysis =
    (typeof data.goal === 'object' ? data.goal?.analysis : '') ||
    data.goal_analysis ||
    profileGoal ||
    dashboard.goal?.analysis ||
    ''

  const weakPointsRaw =
    data.weakPoints || data.weak_points || profile.weak_points || data.weaknesses || []

  const weakPoints = normalizeList(weakPointsRaw).map((item) => ({
    name: typeof item === 'string' ? item : item.name,
    risk: Number(item.risk || item.value || 0),
  }))

  const preferencesRaw = data.preferences || data.learning_preferences || profile.preference
  const preferences = Array.isArray(preferencesRaw)
    ? preferencesRaw.map((item) => (typeof item === 'string' ? item : item.name || item.text))
    : preferencesRaw
      ? [preferencesRaw]
      : []

  return {
    major: profile.major || data.major || '',
    grade: profile.grade || data.grade || '',
    course: profile.course || data.course || '',
    knowledge_level: profile.knowledge_level || data.knowledge_level || '',
    knowledgeLevel: profile.knowledge_level || data.knowledge_level || '',
    weak_points: Array.isArray(profile.weak_points) ? profile.weak_points : weakPoints.map((p) => p.name),
    preference: profile.preference || data.preference || '',
    cognitive_style: profile.cognitive_style || data.cognitive_style || '',
    learning_stage: profile.learning_stage || data.learning_stage || '',
    stage: profile.learning_stage || data.learning_stage || data.stage || '',
    foundation: profile.knowledge_level || data.knowledge_level || data.foundation || '',
    goalText: profileGoal,
    goal: {
      progress: goalProgress,
      analysis: goalAnalysis,
    },
    knowledge: normalizeList(data.knowledge || data.mastery || data.knowledge_mastery),
    weakPoints,
    preferences,
    cognition: {
      main:
        data.cognition?.main ||
        profile.cognitive_style ||
        data.cognitive_style?.main ||
        data.cognition_main ||
        '',
      parts: normalizeList(
        data.cognition?.parts || data.cognitive_style?.parts || data.cognition_parts,
      ),
    },
    engagement: normalizeList(data.engagement || data.learning_engagement, 'day').map(
      (item, index) => ({
        day: item.day || item.name || `第${index + 1}天`,
        value: Number(item.value || 0),
      }),
    ),
    forgettingRisk: normalizeList(
      data.forgettingRisk || data.forgetting_risk || data.memory_risk,
    ),
    feedback: {
      analysis:
        data.feedback?.analysis ||
        data.history_feedback?.analysis ||
        data.feedback_analysis ||
        dashboard.feedback?.analysis ||
        '',
      tags:
        data.feedback?.tags ||
        data.history_feedback?.tags ||
        data.feedback_tags ||
        dashboard.feedback?.tags ||
        [],
    },
    summary: data.summary || data.profile_summary || dashboard.summary || '',
  }
}

/**
 * 构造 MLLearningPathRequest.profile 字段（与后端 Pydantic 模型一致）。
 */
export function buildLearningPathProfilePayload(flatProfile = {}, learningGoal = '') {
  const weakPoints = flatProfile.weak_points ||
    (Array.isArray(flatProfile.weakPoints)
      ? flatProfile.weakPoints.map((item) => (typeof item === 'string' ? item : item.name))
      : [])

  const goal =
    learningGoal.trim() ||
    flatProfile.goalText ||
    (typeof flatProfile.goal === 'string' ? flatProfile.goal : flatProfile.goal?.analysis) ||
    ''

  return {
    major: flatProfile.major || '',
    grade: flatProfile.grade || '',
    course: flatProfile.course || '',
    goal,
    weak_points: weakPoints,
    preference:
      flatProfile.preference ||
      (Array.isArray(flatProfile.preferences) ? flatProfile.preferences.join('、') : ''),
    cognitive_style: flatProfile.cognitive_style || flatProfile.cognition?.main || '',
    knowledge_level: flatProfile.knowledge_level || flatProfile.knowledgeLevel || '',
  }
}
