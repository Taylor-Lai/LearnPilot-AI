<template>
  <section class="evaluation-page">
    <RouterLink class="ui-back-link page-back-link" to="/">← 返回首页</RouterLink>

    <main class="evaluation-content">
      <section class="hero-card">
        <p class="eyebrow">LEARNING EVALUATION</p>
        <h1>学习效果评估</h1>
        <p class="description">
          基于当前学习路径进行阶段测评，题目与标准答案均由后端生成和判分，前端不保存正确答案。
        </p>
      </section>

      <section class="setup-card">
        <div class="panel-head">
          <div>
            <span>评测设置</span>
            <small>选择学习路径后开始评测</small>
          </div>
        </div>

        <div v-if="profileLoading" class="pending-block">正在加载学习画像...</div>
        <div v-else-if="profileError" class="error-block">{{ profileError }}</div>
        <div v-else class="profile-brief">
          <strong>{{ profileView.major || '未设置专业' }}</strong>
          <p>{{ profileView.summary || '暂无画像摘要' }}</p>
          <div class="tag-list" v-if="profileView.weakPoints.length">
            <span v-for="item in profileView.weakPoints" :key="item">薄弱点：{{ item }}</span>
          </div>
        </div>

        <div v-if="pathsLoading" class="pending-block">正在加载学习路径...</div>
        <div v-else-if="!pathOptions.length" class="empty-block">
          <p>请先生成学习路径，再进行阶段评测。</p>
          <RouterLink class="primary-button link-button" to="/learning-path">前往学习路径</RouterLink>
        </div>
        <template v-else>
          <label class="field-label">当前学习路径</label>
          <select v-model="selectedPathId" :disabled="quizActive || submitting || starting">
            <option v-for="item in pathOptions" :key="item.pathId" :value="item.pathId">
              {{ item.title }}（{{ item.progress }}%）
            </option>
          </select>
          <button
            class="primary-button"
            type="button"
            :disabled="starting || quizActive || submitting || !selectedPathId"
            @click="handleStartEvaluation"
          >
            {{ starting ? '正在出题...' : '开始评测' }}
          </button>
        </template>

        <p v-if="pageError" class="error-text">{{ pageError }}</p>
      </section>

      <section v-if="quizActive" class="quiz-card">
        <div class="panel-head">
          <div>
            <span>评测进行中</span>
            <small>第 {{ currentIndex + 1 }} / {{ questions.length }} 题</small>
          </div>
        </div>

        <article v-if="currentQuestion" class="question-panel">
          <div class="question-meta">
            <em v-if="currentQuestion.knowledge_point">{{ currentQuestion.knowledge_point }}</em>
            <em>{{ questionTypeLabel(currentQuestion.type) }}</em>
          </div>
          <h2>{{ currentQuestion.stem }}</h2>

          <div v-if="isTrueFalse(currentQuestion)" class="option-list">
            <label
              v-for="option in currentQuestion.options"
              :key="option.value"
              class="option-row"
              :class="{ selected: answers[currentQuestion.id] === option.value }"
            >
              <input
                v-model="answers[currentQuestion.id]"
                type="radio"
                :name="`q-${currentQuestion.id}`"
                :value="option.value"
                :disabled="submitting"
              />
              <span>{{ option.text }}</span>
            </label>
          </div>

          <div v-else class="option-list">
            <label
              v-for="option in currentQuestion.options"
              :key="option.value"
              class="option-row"
              :class="{ selected: answers[currentQuestion.id] === option.value }"
            >
              <input
                v-model="answers[currentQuestion.id]"
                type="radio"
                :name="`q-${currentQuestion.id}`"
                :value="option.value"
                :disabled="submitting"
              />
              <span>{{ option.value }}. {{ option.text }}</span>
            </label>
          </div>

          <div v-if="!currentQuestion.options?.length" class="short-answer-box">
            <label class="field-label" :for="`answer-${currentQuestion.id}`">你的回答</label>
            <textarea
              :id="`answer-${currentQuestion.id}`"
              v-model="answers[currentQuestion.id]"
              rows="4"
              placeholder="请输入你的答案"
              :disabled="submitting"
            ></textarea>
          </div>
        </article>

        <div class="action-row">
          <button class="ghost-button" type="button" :disabled="currentIndex === 0 || submitting" @click="prevQuestion">
            上一题
          </button>
          <button
            class="ghost-button"
            type="button"
            :disabled="currentIndex >= questions.length - 1 || submitting"
            @click="nextQuestion"
          >
            下一题
          </button>
          <button class="primary-button" type="button" :disabled="submitting" @click="handleSubmit">
            {{ submitting ? '提交中...' : '提交评测' }}
          </button>
        </div>
        <p v-if="unansweredHint" class="form-tip">{{ unansweredHint }}</p>
      </section>

      <section v-if="result" class="result-card">
        <div class="panel-head">
          <div>
            <span>评测结果</span>
            <small>本次测评已完成</small>
          </div>
        </div>

        <div class="result-stats">
          <div>
            <strong>{{ result.score ?? 0 }}</strong>
            <span>总分</span>
          </div>
          <div>
            <strong>{{ formatPercent(result.accuracy) }}</strong>
            <span>正确率</span>
          </div>
          <div>
            <strong>{{ result.correct_count ?? 0 }}/{{ result.total_count ?? 0 }}</strong>
            <span>正确题数</span>
          </div>
          <div>
            <strong>{{ formatPercent(result.mastery_score) }}</strong>
            <span>掌握度</span>
          </div>
        </div>

        <p class="feedback-text">{{ result.feedback }}</p>

        <div v-if="result.weak_points?.length" class="weak-points">
          <h3>薄弱知识点</h3>
          <div class="tag-list">
            <span v-for="item in result.weak_points" :key="item">{{ item }}</span>
          </div>
        </div>

        <div v-if="result.path_adjustment" class="suggestion-box">
          <h3>路径建议</h3>
          <p>{{ result.path_adjustment }}</p>
        </div>

        <div v-if="result.wrong_items?.length" class="wrong-list">
          <h3>错题解析</h3>
          <article v-for="item in result.wrong_items" :key="item.question_id" class="wrong-item">
            <strong>{{ item.stem }}</strong>
            <p>你的答案：{{ item.user_answer || '未作答' }}</p>
            <p>正确答案：{{ item.correct_answer }}</p>
            <p v-if="item.explanation">解析：{{ item.explanation }}</p>
          </article>
        </div>

        <div class="action-row">
          <RouterLink class="ghost-button link-button" to="/learning-path">返回学习路径</RouterLink>
          <button class="primary-button" type="button" @click="restartEvaluation">再测一次</button>
        </div>
      </section>

      <section class="history-card">
        <div class="panel-head">
          <div>
            <span>历史评测</span>
            <small>最近 20 条记录</small>
          </div>
          <em>{{ historyItems.length }} 条</em>
        </div>

        <div v-if="historyLoading" class="pending-block">正在加载历史记录...</div>
        <div v-else-if="!historyItems.length" class="pending-block">暂无评测记录</div>
        <div v-else class="history-list">
          <article v-for="item in historyItems" :key="item.evaluation_id" class="history-item" :class="{ active: highlightedEvaluationId === item.evaluation_id }">
            <div>
              <strong>评测 #{{ item.evaluation_id }}</strong>
              <p>{{ item.feedback }}</p>
              <span>{{ formatDate(item.created_at) }}</span>
            </div>
            <div class="history-meta">
              <em>分数 {{ item.score ?? '-' }}</em>
              <em>正确率 {{ formatPercent(item.accuracy) }}</em>
              <button class="ghost-button" type="button" @click="openHistoryDetail(item.evaluation_id)">查看详情</button>
            </div>
          </article>
        </div>
      </section>

      <section v-if="historyDetail" class="result-card history-detail-card">
        <div class="panel-head">
          <div>
            <span>历史详情 #{{ historyDetail.evaluation_id }}</span>
            <small>{{ formatDate(historyDetail.created_at) }}</small>
          </div>
          <button class="ghost-button" type="button" @click="historyDetail = null">关闭</button>
        </div>
        <p class="feedback-text">{{ historyDetail.feedback }}</p>
        <div v-if="historyDetail.wrong_items?.length" class="wrong-list">
          <article v-for="item in historyDetail.wrong_items" :key="item.question_id" class="wrong-item">
            <strong>{{ item.stem }}</strong>
            <p>你的答案：{{ item.user_answer || '未作答' }}</p>
            <p>正确答案：{{ item.correct_answer }}</p>
            <p v-if="item.explanation">解析：{{ item.explanation }}</p>
          </article>
        </div>
      </section>
    </main>
  </section>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { RouterLink } from 'vue-router'
import { getCurrentProfile } from '@/api/path'
import { getUserPathList } from '@/api/path'
import {
  startEvaluation,
  submitEvaluation,
  getEvaluationHistory,
  getEvaluationDetail,
} from '@/api/evaluation'
import { normalizeProfileResult } from '@/utils/profile'
import { clearCurrentEvaluationId, getCurrentEvaluationId } from '@/utils/evaluationSession'

const profileLoading = ref(false)
const profileError = ref('')
const pathsLoading = ref(false)
const historyLoading = ref(false)
const starting = ref(false)
const submitting = ref(false)
const pageError = ref('')
const unansweredHint = ref('')

const profileData = reactive(normalizeProfileResult({ profile: {}, dashboard: {} }))
const pathOptions = ref([])
const selectedPathId = ref('')
const questions = ref([])
const answers = reactive({})
const currentIndex = ref(0)
const quizActive = ref(false)
const result = ref(null)
const historyItems = ref([])
const historyDetail = ref(null)
const highlightedEvaluationId = ref(null)
const sessionCourseId = ref(null)

const currentQuestion = computed(() => questions.value[currentIndex.value] || null)

const profileView = computed(() => ({
  major: profileData.major || '',
  summary: profileData.summary || profileData.feedback?.analysis || '',
  weakPoints: profileData.weak_points || profileData.weakPoints || [],
}))

function questionTypeLabel(type) {
  if (type === 'true_false') return '判断题'
  if (type === 'short_answer') return '简答题'
  return '单选题'
}

function isTrueFalse(question) {
  return question?.type === 'true_false'
}

function formatPercent(value) {
  if (value == null || Number.isNaN(Number(value))) return '-'
  const num = Number(value)
  if (num <= 1) return `${Math.round(num * 100)}%`
  return `${Math.round(num)}%`
}

function formatDate(value) {
  if (!value) return ''
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value
  return date.toLocaleString('zh-CN')
}

async function loadProfile() {
  profileLoading.value = true
  profileError.value = ''
  try {
    const response = await getCurrentProfile()
    Object.assign(profileData, normalizeProfileResult(response))
  } catch (error) {
    profileError.value = `画像加载失败：${error.message}`
  } finally {
    profileLoading.value = false
  }
}

async function loadPaths() {
  pathsLoading.value = true
  try {
    const response = await getUserPathList()
    const items = Array.isArray(response.items) ? response.items : []
    pathOptions.value = items.map((item) => ({
      pathId: String(item.pathId ?? item.path_id ?? ''),
      title: item.title || '未命名路径',
      progress: Number(item.progress) || 0,
      status: item.status || 'active',
    }))
    const active = pathOptions.value.find((item) => item.status === 'active') || pathOptions.value[0]
    if (active) selectedPathId.value = active.pathId
  } catch (error) {
    pageError.value = `路径加载失败：${error.message}`
  } finally {
    pathsLoading.value = false
  }
}

async function loadHistory() {
  historyLoading.value = true
  try {
    const response = await getEvaluationHistory()
    historyItems.value = Array.isArray(response.items) ? response.items : []
  } catch (error) {
    pageError.value = `历史记录加载失败：${error.message}`
  } finally {
    historyLoading.value = false
  }
}

function resetQuizState() {
  questions.value = []
  Object.keys(answers).forEach((key) => delete answers[key])
  currentIndex.value = 0
  quizActive.value = false
  unansweredHint.value = ''
  sessionCourseId.value = null
}

async function handleStartEvaluation() {
  if (!selectedPathId.value || starting.value) return
  starting.value = true
  pageError.value = ''
  result.value = null
  resetQuizState()

  try {
    const response = await startEvaluation({
      path_id: Number(selectedPathId.value),
      course_id: 1,
      limit: 5,
    })
    const list = Array.isArray(response.questions) ? response.questions : []
    if (!list.length) {
      pageError.value = '后端未返回评测题目，请稍后重试。'
      return
    }
    questions.value = list
    sessionCourseId.value = response.course_id ?? null
    list.forEach((question) => {
      answers[question.id] = ''
    })
    quizActive.value = true
    currentIndex.value = 0
  } catch (error) {
    pageError.value = `开始评测失败：${error.message}`
  } finally {
    starting.value = false
  }
}

function prevQuestion() {
  if (currentIndex.value > 0) currentIndex.value -= 1
}

function nextQuestion() {
  if (currentIndex.value < questions.value.length - 1) currentIndex.value += 1
}

function collectUnanswered() {
  return questions.value.filter((question) => !String(answers[question.id] || '').trim())
}

async function handleSubmit() {
  if (submitting.value || !questions.value.length) return
  const missing = collectUnanswered()
  if (missing.length) {
    unansweredHint.value = `还有 ${missing.length} 道题未作答，请完成后再提交。`
    const firstMissing = questions.value.findIndex((q) => !String(answers[q.id] || '').trim())
    if (firstMissing >= 0) currentIndex.value = firstMissing
    return
  }

  submitting.value = true
  pageError.value = ''
  unansweredHint.value = ''

  try {
    const payload = {
      path_id: Number(selectedPathId.value),
      course_id: sessionCourseId.value || undefined,
      study_minutes: 10,
      answers: questions.value.map((question) => ({
        question_id: question.id,
        answer: String(answers[question.id] || ''),
        elapsed_seconds: 0,
      })),
    }
    const response = await submitEvaluation(payload)
    result.value = response
    quizActive.value = false
    await loadHistory()
  } catch (error) {
    pageError.value = `提交评测失败：${error.message}`
  } finally {
    submitting.value = false
  }
}

function restartEvaluation() {
  result.value = null
  resetQuizState()
}

async function openHistoryDetail(evaluationId) {
  pageError.value = ''
  try {
    historyDetail.value = await getEvaluationDetail(evaluationId)
    highlightedEvaluationId.value = evaluationId
  } catch (error) {
    pageError.value = `详情加载失败：${error.message}`
  }
}

async function restoreEvaluationFromSession() {
  const evaluationId = getCurrentEvaluationId()
  if (!evaluationId) return
  clearCurrentEvaluationId()
  await openHistoryDetail(evaluationId)
}

onMounted(async () => {
  await Promise.all([loadProfile(), loadPaths(), loadHistory()])
  await restoreEvaluationFromSession()
})
</script>

<style scoped>
.evaluation-page {
  position: relative;
  min-height: 100vh;
  padding: 32px;
  background: var(--bg-page);
  color: #111827;
}

.page-back-link {
  position: absolute;
  left: 32px;
  top: 28px;
}

.evaluation-content {
  max-width: 1080px;
  margin: 0 auto;
  padding-top: 52px;
  display: grid;
  gap: 20px;
}

.hero-card,
.setup-card,
.quiz-card,
.result-card,
.history-card {
  padding: 24px;
  border: 1px solid #e5e7eb;
  border-radius: 18px;
  background: #fff;
  box-shadow: var(--shadow-md);
}

.eyebrow {
  margin: 0 0 8px;
  font-size: 12px;
  font-weight: 800;
  letter-spacing: 0.08em;
}

.hero-card h1 {
  margin: 0 0 10px;
  font-size: 32px;
}

.description,
.feedback-text {
  margin: 0;
  line-height: 1.8;
  color: #4b5563;
}

.panel-head {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 16px;
}

.panel-head span {
  display: block;
  font-size: 20px;
  font-weight: 900;
}

.panel-head small,
.form-tip {
  color: #6b7280;
  font-size: 13px;
}

.profile-brief {
  padding: 16px;
  border-radius: 18px;
  background: #f9fafb;
  margin-bottom: 16px;
}

.field-label {
  display: block;
  margin-bottom: 8px;
  font-size: 13px;
  font-weight: 700;
}

.short-answer-box textarea {
  width: 100%;
  padding: 12px 14px;
  border: 1px solid #e5e7eb;
  border-radius: 14px;
  background: #f9fafb;
  resize: vertical;
}

select {
  width: 100%;
  margin-bottom: 14px;
  padding: 12px 14px;
  border: 1px solid #e5e7eb;
  border-radius: 14px;
  background: #f9fafb;
}

.primary-button,
.ghost-button {
  border: none;
  border-radius: 14px;
  padding: 12px 18px;
  font-weight: 800;
  cursor: pointer;
}

.primary-button {
  background: #111827;
  color: #fff;
}

.ghost-button,
.link-button {
  background: #f3f4f6;
  color: #111827;
  border: 1px solid #e5e7eb;
  text-decoration: none;
  display: inline-flex;
  align-items: center;
}

.primary-button:disabled,
.ghost-button:disabled,
select:disabled {
  opacity: 0.55;
  cursor: not-allowed;
}

.pending-block,
.empty-block,
.error-block {
  padding: 18px;
  border-radius: 18px;
  background: #f9fafb;
  text-align: center;
  color: #6b7280;
}

.error-text,
.error-block {
  color: #b91c1c;
}

.question-panel h2 {
  margin: 12px 0 18px;
  line-height: 1.6;
  font-size: 22px;
}

.question-meta {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.question-meta em,
.history-meta em,
.tag-list span {
  padding: 5px 10px;
  border-radius: 999px;
  background: #f3f4f6;
  font-style: normal;
  font-size: 12px;
  font-weight: 700;
}

.option-list {
  display: grid;
  gap: 10px;
}

.option-row {
  display: flex;
  gap: 10px;
  align-items: center;
  padding: 14px;
  border: 1px solid #e5e7eb;
  border-radius: 16px;
  cursor: pointer;
}

.option-row.selected {
  border-color: #111827;
  background: #f9fafb;
}

.action-row {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-top: 16px;
}

.result-stats {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
  margin-bottom: 16px;
}

.result-stats div {
  padding: 14px;
  border-radius: 16px;
  background: #f9fafb;
  text-align: center;
}

.result-stats strong {
  display: block;
  font-size: 24px;
}

.result-stats span {
  color: #6b7280;
  font-size: 12px;
}

.weak-points,
.suggestion-box,
.wrong-list {
  margin-top: 18px;
}

.wrong-item {
  padding: 14px;
  border: 1px solid #fee2e2;
  border-radius: 16px;
  background: #fff7f7;
  margin-top: 10px;
}

.history-list {
  display: grid;
  gap: 12px;
}

.history-item {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  padding: 14px;
  border: 1px solid #e5e7eb;
  border-radius: 16px;
}

.history-item.active {
  border-color: #111827;
  background: #f9fafb;
}

.history-item p,
.history-item span {
  color: #6b7280;
  font-size: 13px;
}

.history-meta {
  display: grid;
  gap: 8px;
  justify-items: end;
}

@media (max-width: 760px) {
  .evaluation-page {
    padding: 24px 16px;
  }

  .result-stats {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .history-item {
    flex-direction: column;
  }
}
</style>
