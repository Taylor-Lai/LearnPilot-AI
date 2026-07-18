<template>
  <section class="profile-page">
    <RouterLink class="ui-back-link page-back-link" to="/">
      ← 返回首页
    </RouterLink>

    <main class="profile-content">
      <section class="hero-card">
        <div class="hero-icon" aria-hidden="true">🎓</div>
        <p class="eyebrow">动态画像 · DYNAMIC STUDENT PROFILE</p>
        <h1>对话式学习画像自主构建</h1>
        <p class="description">
          通过对话采集学生的专业方向、学习目标、知识基础、困惑内容和情绪状态，
          动态生成学习画像，并构建个性化学习分析面板。
        </p>
        <div v-if="profileGenerated" class="hero-status">
          <span class="status-dot" aria-hidden="true"></span>
          画像已生成 · {{ new Date().toLocaleDateString('zh-CN') }}
        </div>
      </section>

      <section class="main-grid">
        <!-- 左侧四部分 -->
        <section class="side-column left-column">
          <!-- 学习目标：文字分析 + 进度条 -->
          <article class="analysis-card goal-card">
            <div class="card-head">
              <div class="title-with-icon">
                <span class="icon-3d" aria-hidden="true"></span>
                <span>学习目标</span>
              </div>
              <em>GOAL</em>
            </div>
            <div v-if="!profileGenerated" class="pending-block">待生成</div>
            <template v-else>
              <p class="analysis-text">{{ profileData.goal.analysis }}</p>
              <div class="goal-progress">
              <div class="progress-top">
                <span>目标完成度</span>
                <strong>{{ profileData.goal.progress }}%</strong>
              </div>
              <div class="progress-track">
                <i :style="{ width: `${profileData.goal.progress}%` }"></i>
              </div>
            </div>
            </template>
          </article>

          <!-- 知识掌握度：图表 -->
          <article class="analysis-card">
            <div class="card-head">
              <div class="title-with-icon">
                <span class="icon-3d" aria-hidden="true"></span>
                <span>知识掌握度</span>
              </div>
              <em>MASTERY</em>
            </div>
            <div v-if="!profileGenerated" class="pending-block">待生成</div>
            <div v-else class="mastery-chart">
              <div
                v-for="(item, index) in profileData.knowledge"
                :key="item.name"
                class="mastery-bar"
              >
                <div
                  class="mastery-column"
                  :style="{
                    height: `${item.value}%`,
                    background: barGradients[index % barGradients.length],
                  }"
                >
                  <strong>{{ item.value }}%</strong>
                </div>
                <span>{{ item.name }}</span>
              </div>
            </div>
          </article>

          <!-- 薄弱知识点：气泡，越薄弱越大 -->
          <article class="analysis-card">
            <div class="card-head">
              <div class="title-with-icon">
                <span class="icon-3d" aria-hidden="true"></span>
                <span>薄弱知识点</span>
              </div>
              <em>WEAKNESS</em>
            </div>
            <div v-if="!profileGenerated" class="pending-block">待生成</div>
            <div v-else class="weak-bubbles">
              <span
                v-for="(item, index) in profileData.weakPoints"
                :key="item.name"
                class="weak-bubble"
                :style="{
                  width: `${48 + item.risk * 0.72}px`,
                  height: `${48 + item.risk * 0.72}px`,
                  background: bubbleGradients[index % bubbleGradients.length],
                }"
              >
                <b>{{ item.name }}</b>
                <small>{{ item.risk }}%</small>
              </span>
            </div>
          </article>

          <!-- 学习偏好：列举 -->
          <article class="analysis-card">
            <div class="card-head">
              <div class="title-with-icon">
                <span class="icon-3d" aria-hidden="true"></span>
                <span>学习偏好</span>
              </div>
              <em>PREFERENCE</em>
            </div>
            <div v-if="!profileGenerated" class="pending-block">待生成</div>
            <ul v-else class="preference-list">
              <li v-for="(item, index) in profileData.preferences" :key="item">
                <i :style="{ background: chartColors[index % chartColors.length] }"></i>
                <span>{{ item }}</span>
              </li>
            </ul>
          </article>
        </section>

        <!-- 中间对话 -->
        <section class="dialog-card">
          <div class="panel-head">
            <span>画像采集对话</span>
            <em>随学随新</em>
          </div>

          <div class="chat-list">
            <div
              v-for="msg in visibleMessages"
              :key="msg.id"
              class="chat-item"
              :class="msg.role"
            >
              <div class="avatar">{{ msg.avatar }}</div>
              <div class="bubble">
                <span v-if="msg.text">{{ msg.text }}</span><span v-if="msg.typing" class="cursor">|</span>
              </div>
            </div>
          </div>

          <form class="input-card" @submit.prevent="sendAnswer">
            <input
              v-model="inputText"
              :placeholder="isFinished ? '画像已生成，可继续补充学习状态' : '请输入你的回答'"
            />
            <button type="submit" :disabled="loading">{{ loading ? '处理中...' : '发送' }}</button>
          </form>

          <div v-if="showProfileButton" class="profile-toggle">
            <button type="button" @click="showAnalysisCard = !showAnalysisCard">
              {{ showAnalysisCard ? '收起学习画像' : '查看学习画像' }}
            </button>
          </div>

          <section v-if="showAnalysisCard && profileGenerated" class="summary-panel">
            <div class="summary-head">
              <strong>学习画像分析</strong>
              <span>AI PROFILE</span>
            </div>
            <p>{{ profileSummary }}</p>
          </section>
        </section>

        <!-- 右侧四部分 -->
        <section class="side-column right-column">
          <!-- 认知风格：饼状图 -->
          <article class="analysis-card">
            <div class="card-head">
              <div class="title-with-icon">
                <span class="icon-3d" aria-hidden="true"></span>
                <span>认知风格</span>
              </div>
              <em>STYLE</em>
            </div>
            <div v-if="!profileGenerated" class="pending-block">待生成</div>
            <div v-else class="pie-wrap">
              <div class="pie-chart" :style="{ background: cognitionPieStyle }">
                <span>{{ profileData.cognition.main }}</span>
              </div>
              <div class="legend-list">
                <div
                  v-for="(item, index) in profileData.cognition.parts"
                  :key="item.name"
                >
                  <i :style="{ background: chartColors[index % chartColors.length] }"></i>
                  <span>{{ item.name }}</span>
                  <strong>{{ item.value }}%</strong>
                </div>
              </div>
            </div>
          </article>

          <!-- 学习投入度：折线图 -->
          <article class="analysis-card">
            <div class="card-head">
              <div class="title-with-icon">
                <span class="icon-3d" aria-hidden="true"></span>
                <span>学习投入度</span>
              </div>
              <em>ENGAGEMENT</em>
            </div>
            <div v-if="!profileGenerated" class="pending-block">待生成</div>
            <div v-else class="line-chart">
              <div class="line-bg"></div>
              <svg viewBox="0 0 300 120" preserveAspectRatio="none">
                <defs>
                  <linearGradient id="engagementLine" x1="0" y1="0" x2="1" y2="0">
                    <stop offset="0%" stop-color="#6366f1" />
                    <stop offset="50%" stop-color="#06b6d4" />
                    <stop offset="100%" stop-color="#22c55e" />
                  </linearGradient>
                </defs>
                <polyline
                  :points="engagementPolyline"
                  fill="none"
                  stroke="url(#engagementLine)"
                  stroke-width="4"
                  stroke-linecap="round"
                  stroke-linejoin="round"
                />
                <circle
                  v-for="point in engagementPoints"
                  :key="point.day"
                  :cx="point.x"
                  :cy="point.y"
                  r="4.8"
                />
              </svg>
              <div class="chart-x-labels">
                <span v-for="item in profileData.engagement" :key="item.day">
                  {{ item.day }}
                </span>
              </div>
            </div>
          </article>

          <!-- 遗忘风险：动态曲线图 -->
          <article class="analysis-card">
            <div class="card-head">
              <div class="title-with-icon">
                <span class="icon-3d" aria-hidden="true"></span>
                <span>遗忘风险</span>
              </div>
              <em>RISK</em>
            </div>
            <div v-if="!profileGenerated" class="pending-block">待生成</div>
            <div v-else class="risk-chart">
              <svg viewBox="0 0 300 130" preserveAspectRatio="none">
                <defs>
                  <linearGradient id="riskLine" x1="0" y1="0" x2="1" y2="0">
                    <stop offset="0%" stop-color="#f59e0b" />
                    <stop offset="50%" stop-color="#ef4444" />
                    <stop offset="100%" stop-color="#ec4899" />
                  </linearGradient>
                  <linearGradient id="riskArea" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stop-color="#ef4444" stop-opacity="0.28" />
                    <stop offset="100%" stop-color="#ffffff" stop-opacity="0" />
                  </linearGradient>
                </defs>
                <path :d="riskAreaPath" fill="url(#riskArea)" class="risk-area"></path>
                <path :d="riskCurvePath" fill="none" stroke="url(#riskLine)" stroke-width="4" stroke-linecap="round" class="risk-line"></path>
              </svg>
              <div class="risk-tips">
                <strong>高风险：{{ highestRisk.name }}</strong>
                <span>建议 24 小时内复习</span>
              </div>
            </div>
          </article>

          <!-- 历史反馈：文字分析 -->
          <article class="analysis-card feedback-card">
            <div class="card-head">
              <div class="title-with-icon">
                <span class="icon-3d" aria-hidden="true"></span>
                <span>历史反馈</span>
              </div>
              <em>FEEDBACK</em>
            </div>
            <div v-if="!profileGenerated" class="pending-block">待生成</div>
            <template v-else>
              <p class="analysis-text">{{ profileData.feedback.analysis }}</p>
              <div class="feedback-tags">
              <span
                v-for="(tag, index) in profileData.feedback.tags"
                :key="tag"
                :style="{ background: bubbleBackgrounds[index % bubbleBackgrounds.length], color: chartColors[index % chartColors.length] }"
              >
                {{ tag }}
              </span>
            </div>
            </template>
          </article>
        </section>
      </section>
    </main>
  </section>
</template>

<script setup>
import { computed, nextTick, onMounted, onUnmounted, reactive, ref } from 'vue'
import { RouterLink } from 'vue-router'
import { getProfileQuestions, sendProfileAnswer, generateProfile } from '@/api/builder'
import { normalizeProfileResult } from '@/utils/profile'
import {
  clearProfileBuilderSessionId,
  getProfileBuilderSessionId,
  setProfileBuilderSessionId,
} from '@/utils/profileBuilderSession'

const inputText = ref('')
const loading = ref(false)
const profileGenerated = ref(false)
const showProfileButton = ref(false)
const showAnalysisCard = ref(false)
const currentQuestionIndex = ref(0)
const questions = ref([])
const sessionId = ref(getProfileBuilderSessionId())
let typingTimer = null

const answers = reactive([])

const messages = reactive([
  {
    id: 1,
    role: 'ai',
    avatar: 'AI',
    text: '你好，我会通过一些问题采集你的学习情况。请先稍等，我正在获取问题列表。',
    typing: false,
  },
])

const visibleMessages = computed(() =>
  messages.filter((msg) => normalizeMessageText(msg.text)),
)

const emptyProfileData = () => ({
  goal: { progress: 0, analysis: '' },
  knowledge: [],
  weakPoints: [],
  preferences: [],
  cognition: { main: '', parts: [] },
  engagement: [],
  forgettingRisk: [],
  feedback: { analysis: '', tags: [] },
  summary: '',
})

const profileData = reactive(emptyProfileData())

const chartColors = [
  '#6366f1',
  '#06b6d4',
  '#22c55e',
  '#f59e0b',
  '#ef4444',
  '#ec4899',
  '#8b5cf6',
]

const barGradients = [
  'linear-gradient(180deg, #6366f1, #06b6d4)',
  'linear-gradient(180deg, #06b6d4, #22c55e)',
  'linear-gradient(180deg, #f59e0b, #ef4444)',
  'linear-gradient(180deg, #ec4899, #8b5cf6)',
]

const bubbleGradients = [
  'radial-gradient(circle at 28% 24%, #ffffff 0 7%, #818cf8 8%, #6366f1 72%)',
  'radial-gradient(circle at 28% 24%, #ffffff 0 7%, #67e8f9 8%, #06b6d4 72%)',
  'radial-gradient(circle at 28% 24%, #ffffff 0 7%, #86efac 8%, #22c55e 72%)',
  'radial-gradient(circle at 28% 24%, #ffffff 0 7%, #fcd34d 8%, #f59e0b 72%)',
  'radial-gradient(circle at 28% 24%, #ffffff 0 7%, #fca5a5 8%, #ef4444 72%)',
]

const bubbleBackgrounds = [
  'rgba(99, 102, 241, 0.10)',
  'rgba(6, 182, 212, 0.10)',
  'rgba(34, 197, 94, 0.10)',
  'rgba(245, 158, 11, 0.12)',
  'rgba(239, 68, 68, 0.10)',
  'rgba(236, 72, 153, 0.10)',
]

const fallbackQuestions = [
  { id: 'major', text: '你的专业或主要学习方向是什么？' },
  { id: 'goal', text: '你当前最重要的学习目标是什么？' },
  { id: 'foundation', text: '你觉得自己目前掌握得比较好的知识有哪些？' },
  { id: 'weakness', text: '最近学习中最容易出错或最困惑的知识点是什么？' },
  { id: 'preference', text: '你更喜欢哪种学习方式：视频、文字、案例、项目、刷题，还是老师讲解？' },
  { id: 'engagement', text: '你最近一周的学习投入情况如何？例如每天学习多久、是否容易分心。' },
  { id: 'forgetting', text: '哪些内容你学过但很容易忘？' },
  { id: 'feedback', text: '以前老师或系统给你的学习反馈中，哪些建议对你最有帮助？' },
]

function getQuestionId(question = {}) {
  return question.question_id || question.id || ''
}

function persistSessionId(nextSessionId) {
  const normalized = (nextSessionId || '').trim()
  if (!normalized) return
  sessionId.value = normalized
  setProfileBuilderSessionId(normalized)
}

function resetProfileBuilderSession() {
  sessionId.value = ''
  clearProfileBuilderSessionId()
}

function handleUserInfoUpdated() {
  if (!localStorage.getItem('token')) {
    resetProfileBuilderSession()
  }
}

const isFinished = computed(() => questions.value.length > 0 && currentQuestionIndex.value >= questions.value.length)

const profileSummary = computed(() =>
  profileData.summary || profileData.feedback.analysis || '画像已生成，系统将根据后端机器学习分析结果持续更新。',
)

function scrollChatToBottom() {
  nextTick(() => {
    const chat = document.querySelector('.chat-list')
    if (chat) chat.scrollTop = chat.scrollHeight
  })
}

function normalizeMessageText(text) {
  return String(text ?? '')
    .replace(/\r\n/g, '\n')
    .replace(/[ \t]*\n[ \t]*/g, ' ')
    .replace(/\s{2,}/g, ' ')
    .trim()
}

function addUserMessage(text) {
  const cleanText = normalizeMessageText(text)
  if (!cleanText) return

  messages.push({
    id: Date.now(),
    role: 'user',
    avatar: '我',
    text: cleanText,
    typing: false,
  })
  scrollChatToBottom()
}

function typeAiMessage(text) {
  clearInterval(typingTimer)

  const cleanText = normalizeMessageText(text)
  if (!cleanText) return

  // 删除被中断的空 AI 消息，避免对话框出现空白气泡
  for (let i = messages.length - 1; i >= 0; i -= 1) {
    const msg = messages[i]
    if (msg.role === 'ai' && !normalizeMessageText(msg.text)) {
      messages.splice(i, 1)
    }
  }

  const msg = reactive({
    id: Date.now() + Math.random(),
    role: 'ai',
    avatar: 'AI',
    text: '',
    typing: true,
  })

  messages.push(msg)
  scrollChatToBottom()

  let index = 0
  typingTimer = setInterval(() => {
    msg.text += cleanText[index]
    index += 1
    scrollChatToBottom()

    if (index >= cleanText.length) {
      clearInterval(typingTimer)
      msg.typing = false
    }
  }, 22)
}

function askCurrentQuestion(prefix = '') {
  const question = questions.value[currentQuestionIndex.value]
  if (!question) return

  const progress = `问题 ${currentQuestionIndex.value + 1}/${questions.value.length}`
  // 后端返回的字段是 question，不是 text
  const questionText = normalizeMessageText(question.question || question.text)
  const prefixText = prefix ? `${prefix} ` : ''
  typeAiMessage(`${prefixText}${progress}：${questionText}`)
}

async function loadQuestions() {
  try {
    const result = await getProfileQuestions()
    const list = Array.isArray(result.questions) ? result.questions : result
    questions.value = Array.isArray(list) && list.length ? list : fallbackQuestions
  } catch (error) {
    console.warn(
      '[ProfileBuilder] GET /api/ml/profile/questions failed, using fallbackQuestions:',
      error,
    )
    questions.value = fallbackQuestions
    typeAiMessage(`问题接口暂时不可用，已使用本地默认问题继续采集。错误：${error.message}`)
  }

  askCurrentQuestion()
}

function applyProfileData(nextData) {
  Object.assign(profileData, emptyProfileData(), nextData)
}

async function sendAnswer() {
  const answer = inputText.value.trim()
  if (!answer || loading.value) return

  addUserMessage(answer)
  inputText.value = ''

  if (isFinished.value) {
    typeAiMessage('画像已经生成，我已记录你的补充信息。后续可以接后端增量更新接口继续优化画像。')
    return
  }

  const question = questions.value[currentQuestionIndex.value]
  const questionText = question.question || question.text
  const questionId = getQuestionId(question)
  const answerData = {
    question_id: questionId,
    question: questionText,
    answer,
  }
  answers.push(answerData)

  loading.value = true

  try {
    const result = await sendProfileAnswer({
      session_id: sessionId.value,
      question_id: questionId,
      question: questionText,
      answer,
    })
    persistSessionId(result.session_id || result.sessionId)
  } catch (error) {
    console.error('发送回答失败:', error)
    typeAiMessage(`回答已暂存，但同步后端失败：${error.message}`)
  }

  currentQuestionIndex.value += 1

  if (currentQuestionIndex.value < questions.value.length) {
    loading.value = false
    askCurrentQuestion('已记录。')
    return
  }

  try {
    typeAiMessage('所有问题已回答，正在调用机器学习模型生成学习画像...')

    const result = await generateProfile({
      session_id: sessionId.value,
      answers: answers.map((item) => ({ ...item })),
    })

    applyProfileData(normalizeProfileResult(result))
    profileGenerated.value = true
    showProfileButton.value = true
    showAnalysisCard.value = true
    resetProfileBuilderSession()
    typeAiMessage('学习画像已生成，左侧和右侧八个板块已根据后端机器学习结果完成更新。')
  } catch (error) {
    console.error('生成画像失败:', error)
    typeAiMessage(`画像生成失败：${error.message}。请稍后重试，或检查后端接口。`)
  } finally {
    loading.value = false
  }
}

function buildLinePoints(list) {
  if (!Array.isArray(list) || list.length === 0) return []

  const max = 100
  const min = 0
  const width = 300
  const height = 120
  const paddingX = 14
  const paddingY = 16
  const usableWidth = width - paddingX * 2
  const usableHeight = height - paddingY * 2
  const step = list.length > 1 ? usableWidth / (list.length - 1) : 0

  return list.map((item, index) => ({
    ...item,
    x: paddingX + index * step,
    y: paddingY + (max - item.value) / (max - min) * usableHeight,
  }))
}

const engagementPoints = computed(() => buildLinePoints(profileData.engagement))

const engagementPolyline = computed(() =>
  engagementPoints.value.map((point) => `${point.x},${point.y}`).join(' '),
)

const riskPoints = computed(() => {
  const points = buildLinePoints(profileData.forgettingRisk)
  return points.map((item) => ({ ...item, y: item.y + 5 }))
})

function buildSmoothPath(points) {
  if (!points.length) return ''
  let d = `M ${points[0].x} ${points[0].y}`

  for (let i = 1; i < points.length; i += 1) {
    const prev = points[i - 1]
    const current = points[i]
    const midX = (prev.x + current.x) / 2
    d += ` C ${midX} ${prev.y}, ${midX} ${current.y}, ${current.x} ${current.y}`
  }

  return d
}

const riskCurvePath = computed(() => buildSmoothPath(riskPoints.value))

const riskAreaPath = computed(() => {
  const points = riskPoints.value
  if (!points.length) return ''
  return `${buildSmoothPath(points)} L ${points[points.length - 1].x} 130 L ${points[0].x} 130 Z`
})

const highestRisk = computed(() => {
  if (!profileData.forgettingRisk.length) return { name: '待生成', value: 0 }
  return profileData.forgettingRisk.reduce((max, item) => (item.value > max.value ? item : max), profileData.forgettingRisk[0])
})

const cognitionPieStyle = computed(() => {
  if (!profileData.cognition.parts.length) {
    return 'radial-gradient(circle at center, #ffffff 0 52%, transparent 53%), conic-gradient(#e5e7eb 0% 100%)'
  }

  let start = 0
  const stops = profileData.cognition.parts.map((item, index) => {
    const end = start + item.value
    const color = chartColors[index % chartColors.length]
    const segment = `${color} ${start}% ${end}%`
    start = end
    return segment
  })

  return `radial-gradient(circle at center, #ffffff 0 52%, transparent 53%), conic-gradient(${stops.join(', ')})`
})

onMounted(() => {
  sessionId.value = getProfileBuilderSessionId()
  window.addEventListener('userInfoUpdated', handleUserInfoUpdated)
  loadQuestions()
})

onUnmounted(() => {
  window.removeEventListener('userInfoUpdated', handleUserInfoUpdated)
})
</script>

<style scoped>
.profile-page {
  position: relative;
  min-height: 100vh;
  padding: 32px;
  background: linear-gradient(135deg, #f7f8fa 0%, #eef0f3 100%);
  color: #111827;
  box-sizing: border-box;
}

.page-back-link {
  position: absolute;
  left: 32px;
  top: 28px;
  color: #4b5563;
  text-decoration: none;
  font-weight: 600;
  font-size: 14px;
  transition: color 0.2s;
}

.page-back-link:hover {
  color: #111827;
}

.profile-content {
  max-width: 1640px;
  margin: 0 auto;
  padding-top: 52px;
}

/* Hero Card */
.hero-card {
  background: linear-gradient(135deg, #ffffff 0%, #f8f9ff 100%);
  border: 1px solid rgba(99, 102, 241, 0.15);
  border-radius: 24px;
  padding: 40px 50px;
  margin-bottom: 28px;
  box-shadow: 0 8px 32px rgba(99, 102, 241, 0.08);
  text-align: center;
  position: relative;
  overflow: hidden;
}

.hero-card::before {
  content: '';
  position: absolute;
  top: -50%;
  right: -20%;
  width: 400px;
  height: 400px;
  background: radial-gradient(circle, rgba(99, 102, 241, 0.05) 0%, transparent 70%);
  border-radius: 50%;
}

.hero-icon {
  font-size: 48px;
  margin-bottom: 12px;
  display: block;
}

.eyebrow {
  margin: 0 0 10px;
  font-size: 13px;
  font-weight: 700;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: #6366f1;
  position: relative;
}

.hero-card h1 {
  margin: 0 0 14px;
  font-size: 36px;
  line-height: 1.25;
  color: #111827;
  position: relative;
}

.hero-status {
  margin-top: 16px;
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 6px 16px;
  border-radius: 999px;
  background: rgba(99, 102, 241, 0.08);
  color: #6366f1;
  font-size: 13px;
  font-weight: 600;
  position: relative;
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #22c55e;
  animation: pulse-dot 2s infinite;
}

@keyframes pulse-dot {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.5; transform: scale(0.8); }
}

.description {
  max-width: 760px;
  margin: 0 auto;
  line-height: 1.9;
  font-size: 15px;
  color: #4b5563;
  position: relative;
}

.main-grid {
  display: grid;
  grid-template-columns: minmax(280px, 0.95fr) minmax(400px, 1.2fr) minmax(280px, 0.95fr);
  gap: 24px;
  align-items: stretch;
}

.side-column {
  display: grid;
  grid-template-rows: repeat(4, 270px);
  gap: 16px;
}

.dialog-card,
.analysis-card {
  background: #ffffff;
  border: 1px solid #e5e7eb;
  border-radius: 20px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.04);
  padding: 20px 22px;
  transition: box-shadow 0.3s, border-color 0.3s;
}

.analysis-card:hover {
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.06);
  border-color: rgba(99, 102, 241, 0.15);
}

.analysis-card {
  min-height: 180px;
  box-sizing: border-box;
  overflow: hidden;
}

.panel-head,
.card-head,
.summary-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 14px;
}

.panel-head span,
.card-head span,
.summary-head strong {
  color: #111827;
  font-size: 18px;
  font-weight: 800;
}

.panel-head em,
.card-head em,
.summary-head span {
  padding: 5px 14px;
  border-radius: 999px;
  background: #f1f4f9;
  color: #6b7280;
  font-size: 11px;
  font-style: normal;
  font-weight: 700;
  letter-spacing: 0.05em;
  white-space: nowrap;
}

.title-with-icon {
  display: flex;
  align-items: center;
  gap: 10px;
}

.card-icon {
  font-size: 22px;
  line-height: 1;
}

.analysis-text {
  margin: 0;
  color: #374151;
  line-height: 1.85;
  font-size: 13px;
}

.goal-progress {
  margin-top: 14px;
}

.progress-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 6px;
  font-size: 13px;
  color: #6b7280;
}

.progress-top strong {
  color: #111827;
  font-size: 18px;
  font-weight: 800;
}

.progress-track {
  height: 10px;
  overflow: hidden;
  border-radius: 999px;
  background: #eef0f3;
  box-shadow: inset 0 1px 4px rgba(0, 0, 0, 0.06);
}

.progress-track i {
  display: block;
  height: 100%;
  border-radius: inherit;
  background: linear-gradient(90deg, #6366f1, #8b5cf6);
  transition: width 0.8s ease;
  box-shadow: 0 0 20px rgba(99, 102, 241, 0.25);
}

.mastery-chart {
  height: 155px;
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
  align-items: end;
  padding: 12px 4px 0;
  border-radius: 16px;
  background:
    linear-gradient(#f0f2f5 1px, transparent 1px) 0 0 / 100% 25%,
    #fafbfc;
  border: 1px solid #eef0f3;
}

.mastery-bar {
  height: 130px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: flex-end;
  gap: 6px;
  font-size: 11px;
  font-weight: 600;
  color: #6b7280;
  text-align: center;
}

.mastery-column {
  width: 74%;
  min-height: 24px;
  display: flex;
  align-items: flex-start;
  justify-content: center;
  padding-top: 5px;
  border-radius: 12px 12px 6px 6px;
  color: #ffffff;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.1);
  transform: perspective(120px) rotateX(4deg);
  transition: height 0.6s ease;
}

.mastery-column strong {
  font-size: 11px;
  font-weight: 700;
}

.weak-bubbles {
  min-height: 140px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-wrap: wrap;
  gap: 12px;
  padding: 6px;
}

.weak-bubble {
  display: inline-flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 1px;
  border-radius: 50%;
  color: #ffffff;
  text-align: center;
  box-shadow:
    0 12px 28px rgba(0, 0, 0, 0.12),
    inset -6px -8px 16px rgba(0, 0, 0, 0.08),
    inset 6px 8px 20px rgba(255, 255, 255, 0.25);
  transform: translateZ(0);
  transition: transform 0.3s, box-shadow 0.3s;
}

.weak-bubble:hover {
  transform: scale(1.05);
  box-shadow:
    0 16px 36px rgba(0, 0, 0, 0.18),
    inset -6px -8px 16px rgba(0, 0, 0, 0.08),
    inset 6px 8px 20px rgba(255, 255, 255, 0.25);
}

.weak-bubble b {
  max-width: 78%;
  font-size: 12px;
  line-height: 1.2;
}

.weak-bubble small {
  font-size: 10px;
  opacity: 0.9;
}

.preference-list {
  display: grid;
  gap: 10px;
  padding: 0;
  margin: 0;
  list-style: none;
}

.preference-list li {
  display: flex;
  gap: 10px;
  align-items: center;
  padding: 10px 14px;
  border-radius: 14px;
  background: #f8f9fc;
  border: 1px solid #eef0f3;
  color: #111827;
  font-size: 13px;
  line-height: 1.5;
  transition: border-color 0.2s, background 0.2s;
}

.preference-list li:hover {
  border-color: #d1d5db;
  background: #f5f6fa;
}

.preference-list i,
.legend-list i {
  flex: 0 0 auto;
  width: 10px;
  height: 10px;
  border-radius: 50%;
}

.chat-list {
  min-height: 480px;
  max-height: 580px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 16px;
  border-radius: 16px;
  background: #fafbfc;
  border: 1px solid #eef0f3;
  margin-bottom: 16px;
}

.chat-list::-webkit-scrollbar {
  width: 4px;
}

.chat-list::-webkit-scrollbar-track {
  background: transparent;
}

.chat-list::-webkit-scrollbar-thumb {
  background: #d1d5db;
  border-radius: 999px;
}

.chat-item {
  display: flex;
  gap: 10px;
  animation: fadeInUp 0.3s ease;
}

@keyframes fadeInUp {
  from { opacity: 0; transform: translateY(8px); }
  to { opacity: 1; transform: translateY(0); }
}

.chat-item.user {
  flex-direction: row-reverse;
}

.avatar {
  flex: 0 0 auto;
  width: 34px;
  height: 34px;
  border-radius: 12px;
  background: linear-gradient(135deg, #6366f1, #8b5cf6);
  color: #ffffff;
  font-size: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.user .avatar {
  background: linear-gradient(135deg, #1f2937, #374151);
}

.bubble {
  max-width: 82%;
  padding: 10px 16px;
  border-radius: 16px;
  background: #ffffff;
  border: 1px solid #eef0f3;
  color: #111827;
  font-size: 14px;
  line-height: 1.8;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.03);
}

.user .bubble {
  background: linear-gradient(135deg, #1f2937, #374151);
  color: #ffffff;
  border: none;
}

.cursor {
  display: inline-block;
  margin-left: 2px;
  animation: blink 0.8s infinite;
}

@keyframes blink {
  0%, 45% { opacity: 1; }
  46%, 100% { opacity: 0; }
}

.input-card {
  display: flex;
  gap: 10px;
  align-items: center;
}

.input-card input {
  flex: 1;
  height: 46px;
  padding: 0 16px;
  border-radius: 14px;
  border: 1px solid #e5e7eb;
  background: #fafbfc;
  outline: none;
  color: #111827;
  font-size: 14px;
  transition: border-color 0.2s, box-shadow 0.2s;
}

.input-card input:focus {
  background: #ffffff;
  border-color: #6366f1;
  box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.1);
}

.input-card button,
.profile-toggle button {
  height: 46px;
  padding: 0 22px;
  border: none;
  border-radius: 999px;
  background: linear-gradient(135deg, #1f2937, #111827);
  color: #ffffff;
  font-size: 14px;
  font-weight: 700;
  cursor: pointer;
  transition: transform 0.2s, box-shadow 0.2s;
}

.input-card button:hover:not(:disabled),
.profile-toggle button:hover {
  transform: translateY(-1px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
}

.profile-toggle {
  margin-top: 12px;
  display: flex;
  justify-content: center;
}

.profile-toggle button {
  background: linear-gradient(135deg, #6366f1, #8b5cf6);
  box-shadow: 0 4px 16px rgba(99, 102, 241, 0.2);
}

.summary-panel {
  margin-top: 14px;
  padding: 16px 20px;
  border-radius: 16px;
  background: linear-gradient(135deg, #f8f9ff, #f0f1ff);
  border: 1px solid rgba(99, 102, 241, 0.12);
}

.summary-panel p {
  margin: 0;
  color: #1f2937;
  line-height: 1.85;
  font-size: 13px;
}

.pie-wrap {
  display: grid;
  grid-template-columns: 130px 1fr;
  gap: 16px;
  align-items: center;
}

.pie-chart {
  width: 126px;
  height: 126px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  box-shadow:
    0 12px 32px rgba(99, 102, 241, 0.12),
    inset 0 0 0 2px rgba(255, 255, 255, 0.8);
  transform: perspective(200px) rotateX(5deg) rotateY(-5deg);
  transition: transform 0.3s;
}

.pie-chart:hover {
  transform: perspective(200px) rotateX(5deg) rotateY(-5deg) scale(1.02);
}

.pie-chart span {
  width: 72px;
  font-size: 13px;
  font-weight: 800;
  line-height: 1.3;
  text-align: center;
  color: #111827;
}

.legend-list {
  display: grid;
  gap: 8px;
}

.legend-list div {
  display: grid;
  grid-template-columns: 14px 1fr auto;
  align-items: center;
  gap: 6px;
  color: #6b7280;
  font-size: 12px;
}

.legend-list strong {
  color: #111827;
  font-weight: 700;
}

.line-chart {
  position: relative;
  height: 150px;
  padding-bottom: 20px;
  color: #111827;
}

.line-chart svg {
  width: 100%;
  height: 120px;
}

.line-chart circle {
  fill: #ffffff;
  stroke: #6366f1;
  stroke-width: 2.5;
  box-shadow: 0 0 16px rgba(99, 102, 241, 0.2);
}

.chart-x-labels {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  gap: 4px;
  margin-top: 4px;
  font-size: 11px;
  font-weight: 500;
  color: #6b7280;
  text-align: center;
}

.risk-chart {
  position: relative;
  height: 152px;
  border-radius: 16px;
  background:
    linear-gradient(#f0f2f5 1px, transparent 1px) 0 0 / 100% 25%,
    #fafbfc;
  border: 1px solid #eef0f3;
  overflow: hidden;
}

.risk-chart svg {
  width: 100%;
  height: 130px;
}

.risk-line {
  stroke-dasharray: 620;
  animation: riskFlow 3s ease-in-out infinite alternate;
  filter: drop-shadow(0 4px 12px rgba(239, 68, 68, 0.15));
}

.risk-area {
  animation: riskFloat 3s ease-in-out infinite alternate;
}

@keyframes riskFlow {
  from { stroke-dashoffset: 80; }
  to { stroke-dashoffset: 0; }
}

@keyframes riskFloat {
  from { opacity: 0.4; transform: translateY(4px); }
  to { opacity: 1; transform: translateY(0); }
}

.risk-tips {
  position: absolute;
  left: 14px;
  right: 14px;
  bottom: 8px;
  display: flex;
  justify-content: space-between;
  gap: 12px;
  font-size: 12px;
  font-weight: 500;
}

.risk-tips strong {
  color: #ef4444;
}

.risk-tips span {
  color: #6b7280;
}

.feedback-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 12px;
}

.feedback-tags span {
  padding: 6px 14px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 700;
  transition: transform 0.2s, box-shadow 0.2s;
}

.feedback-tags span:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.06);
}

.pending-block {
  height: calc(100% - 48px);
  min-height: 100px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
  border-radius: 16px;
  border: 1.5px dashed #d1d5db;
  background: repeating-linear-gradient(135deg, #fafbfc 0 12px, #f3f4f6 12px 24px);
  color: #9ca3af;
  font-size: 20px;
  font-weight: 800;
  letter-spacing: 0.06em;
}

.pending-icon {
  font-size: 28px;
}

.input-card button:disabled {
  cursor: not-allowed;
  opacity: 0.6;
  transform: none !important;
}

/* 雷达图触发按钮 */
.radar-trigger {
  margin-top: 28px;
  display: flex;
  justify-content: center;
}

.radar-trigger button {
  padding: 14px 40px;
  border: none;
  border-radius: 999px;
  background: linear-gradient(135deg, #6366f1, #8b5cf6);
  color: #ffffff;
  font-size: 18px;
  font-weight: 700;
  cursor: pointer;
  box-shadow: 0 8px 32px rgba(99, 102, 241, 0.3);
  transition: transform 0.3s, box-shadow 0.3s;
}

.radar-trigger button:hover {
  transform: translateY(-2px) scale(1.02);
  box-shadow: 0 12px 40px rgba(99, 102, 241, 0.4);
}

/* 模态框样式 */
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  backdrop-filter: blur(8px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  animation: modalFadeIn 0.3s ease;
}

@keyframes modalFadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

.modal-content {
  background: #ffffff;
  border-radius: 28px;
  max-width: 780px;
  width: 90%;
  max-height: 90vh;
  overflow: hidden;
  box-shadow: 0 32px 80px rgba(0, 0, 0, 0.3);
  animation: modalSlideUp 0.3s ease;
}

@keyframes modalSlideUp {
  from { transform: translateY(30px) scale(0.95); opacity: 0; }
  to { transform: translateY(0) scale(1); opacity: 1; }
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 24px 32px;
  border-bottom: 1px solid #eef0f3;
}

.modal-title {
  display: flex;
  align-items: center;
  gap: 12px;
}

.modal-icon {
  font-size: 28px;
}

.modal-title h2 {
  margin: 0;
  font-size: 22px;
  font-weight: 800;
  color: #111827;
}

.modal-close {
  width: 40px;
  height: 40px;
  border: none;
  border-radius: 50%;
  background: #f1f4f9;
  color: #6b7280;
  font-size: 20px;
  cursor: pointer;
  transition: background 0.2s, transform 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
}

.modal-close:hover {
  background: #e5e7eb;
  transform: rotate(90deg);
}

.modal-body {
  padding: 32px;
}

.radar-container {
  display: grid;
  grid-template-columns: 1fr 180px;
  gap: 32px;
  align-items: center;
}

.radar-chart-wrapper {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 380px;
}

.radar-canvas {
  max-width: 100%;
  height: auto;
}

.radar-legend {
  display: grid;
  gap: 12px;
}

.radar-legend-item {
  display: grid;
  grid-template-columns: 16px 1fr auto;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  color: #374151;
  padding: 6px 12px;
  border-radius: 10px;
  transition: background 0.2s;
}

.radar-legend-item:hover {
  background: #f8f9fc;
}

.legend-color {
  width: 14px;
  height: 14px;
  border-radius: 4px;
}

.legend-label {
  font-weight: 500;
}

.legend-value {
  font-weight: 700;
  color: #111827;
}

@media (max-width: 1280px) {
  .main-grid {
    grid-template-columns: 1fr;
  }

  .side-column {
    grid-template-columns: repeat(2, 1fr);
    grid-template-rows: none;
  }

  .chat-list {
    min-height: 380px;
  }
}

@media (max-width: 900px) {
  .side-column {
    grid-template-columns: 1fr;
  }

  .pie-wrap {
    grid-template-columns: 1fr;
    justify-items: center;
  }

  .legend-list {
    width: 100%;
  }

  .radar-container {
    grid-template-columns: 1fr;
  }

  .radar-legend {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
  }
}

@media (max-width: 720px) {
  .profile-page {
    padding: 16px;
  }

  .page-back-link {
    left: 16px;
    top: 16px;
  }

  .profile-content {
    padding-top: 44px;
  }

  .hero-card {
    padding: 28px 20px;
    border-radius: 18px;
  }

  .hero-card h1 {
    font-size: 26px;
  }

  .dialog-card,
  .analysis-card {
    padding: 16px 18px;
    border-radius: 16px;
  }

  .input-card {
    flex-direction: column;
    align-items: stretch;
  }

  .input-card button {
    width: 100%;
  }

  .modal-content {
    width: 95%;
    border-radius: 20px;
  }

  .modal-header {
    padding: 18px 20px;
  }

  .modal-body {
    padding: 20px;
  }

  .radar-legend {
    grid-template-columns: 1fr 1fr;
  }
}

/* ?????????????????? */

.icon-3d {
  width: 42px;
  height: 42px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 15px;
  background: #f3f4f6;
  border: 1px solid #e5e7eb;
  box-shadow: 0 6px 14px rgba(0, 0, 0, 0.06);
  filter: none;
  transform: none;
  font-size: 23px;
}

.line-bg {
  position: absolute;
  inset: 0 0 24px;
  border-radius: 18px;
  background:
    linear-gradient(#eef0f3 1px, transparent 1px) 0 0 / 100% 25%,
    #f9fafb;
  border: 1px solid #e5e7eb;
}
</style>
