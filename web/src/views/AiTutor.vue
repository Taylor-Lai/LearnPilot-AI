<template>
  <section class="tutor-page">
    <div class="tutor-shell">
      <header class="section-head hero-head">
        <div class="hero-bg"></div>
        <div class="hero-mask"></div>
        <button class="ui-back-link page-back-link" type="button" @click="goHome">
          ← 返回首页
        </button>
        <p class="eyebrow">INTELLIGENT TUTOR</p>
        <h2>智能辅导 · AI学习助手</h2>
        <p class="section-desc">
          基于大模型的智能辅导系统，实时解答学习疑问，提供详细的知识讲解和个性化的学习建议。
        </p>
      </header>

      <main class="tutor-layout">
        <!-- 左侧问答区域 -->
        <aside class="qa-panel">
          <div class="panel-header">
            <div>
              <h3>学习问答</h3>
              <p>输入你在学习过程中遇到的问题</p>
            </div>
          </div>

          <div class="chat-container">
            <div class="chat-messages" ref="chatMessagesRef">
              <div v-for="msg in messages" :key="msg.id" class="message-item" :class="msg.role">
                <div class="message-avatar">
                  <span v-if="msg.role === 'user'">我</span>
                  <span v-else>助教</span>
                </div>
                <div class="message-bubble">
                  <p>{{ msg.text }}</p>
                  <span class="message-time">{{ msg.time }}</span>
                </div>
              </div>
              <div v-if="isTyping" class="message-item ai">
                <div class="message-avatar">助教</div>
                <div class="message-bubble typing-bubble">
                  <span class="dot"></span>
                  <span class="dot"></span>
                  <span class="dot"></span>
                </div>
              </div>
            </div>

            <div class="input-area">
              <textarea
                v-model="inputText"
                placeholder="请输入你遇到的问题，例如：什么是机器学习？如何理解卷积神经网络？..."
                rows="3"
                @keydown.ctrl.enter="sendMessage"
                @keydown.meta.enter="sendMessage"
              ></textarea>
              <div class="input-actions">
                <div class="prompt-suggestions">
                  <button v-for="q in quickQuestions" :key="q" @click="useQuickQuestion(q)">
                    {{ q }}
                  </button>
                </div>
                <button class="send-btn" :disabled="isSending || !inputText.trim()" @click="sendMessage">
                  {{ isSending ? '思考中...' : '发送提问' }}
                </button>
              </div>
            </div>
          </div>
        </aside>

        <!-- 右侧讲解区域 -->
        <section class="explanation-panel">
          <div class="panel-header">
            <div>
              <h3>智能讲解</h3>
              <p>AI数字人详细解答</p>
            </div>
          </div>

          <div class="explanation-content">
            <!-- 数字人形象区域 -->
            <div class="avatar-section">
              <div class="digital-avatar">
                <div class="avatar-circle">
                  <div class="avatar-wave" v-if="isPlaying"></div>
                  <span class="avatar-emoji">AI</span>
                </div>
                <div class="avatar-status">
                  <span class="status-dot" :class="{ active: isPlaying }"></span>
                  <span>{{ isPlaying ? '讲解中...' : '等待提问' }}</span>
                </div>
              </div>
              <div class="voice-control">
                <button class="voice-btn" @click="toggleVoice">
                  <span>{{ isVoiceEnabled ? '语音已开启' : '语音已关闭' }}</span>
                </button>
              </div>
            </div>

            <!-- 讲解内容区域 -->
            <div class="explanation-text">
              <div v-if="!currentExplanation" class="empty-explanation">
                <div class="empty-icon">AI</div>
                <h4>等待提问</h4>
                <p>在左侧输入你的问题，AI助手将为你提供详细解答</p>
                <div class="example-questions">
                  <p>试试问这些问题：</p>
                  <button v-for="q in exampleQuestions" :key="q" @click="useQuickQuestion(q)">
                    {{ q }}
                  </button>
                </div>
              </div>
              <div v-else class="explanation-wrapper">
                <div class="explanation-header">
                  <span class="question-badge">当前问题</span>
                  <div class="current-question">{{ currentQuestion }}</div>
                </div>
                <div class="explanation-body">
                  <div class="explanation-markdown" v-html="renderedExplanation"></div>
                  <section v-if="currentVisualAid?.nodes?.length" class="visual-aid" aria-label="知识图解">
                    <h4>{{ currentVisualAid.title || '知识图解' }}</h4>
                    <div class="visual-flow">
                      <template v-for="(node, index) in currentVisualAid.nodes" :key="`${node.label}-${index}`">
                        <article class="visual-node">
                          <span>0{{ index + 1 }}</span>
                          <strong>{{ node.label }}</strong>
                          <p>{{ node.detail }}</p>
                        </article>
                        <span v-if="index < currentVisualAid.nodes.length - 1" class="visual-arrow">→</span>
                      </template>
                    </div>
                  </section>
                </div>
                <div class="explanation-actions">
                  <button class="action-btn" @click="copyExplanation">
                    复制讲解
                  </button>
                  <button class="action-btn" @click="regenerateAnswer">
                    重新讲解
                  </button>
                </div>
              </div>
            </div>
          </div>
        </section>
      </main>
    </div>
  </section>
</template>

<script setup>
import { computed, nextTick, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { marked } from 'marked'
import { askTutor } from '../api/tutor'
import { getCurrentProfile } from '../api/path'
import { buildLearningPathProfilePayload } from '../utils/profile'
import { getStoredUserId } from '../utils/user'

const router = useRouter()

marked.setOptions({
  breaks: true,
  gfm: true,
  headerIds: false,
  mangle: false,
})

const inputText = ref('')
const isSending = ref(false)
const isTyping = ref(false)
const isPlaying = ref(false)
const isVoiceEnabled = ref(true)
const currentQuestion = ref('')
const currentExplanation = ref('')
const currentVisualAid = ref(null)
const chatMessagesRef = ref(null)

const messages = ref([
  {
    id: 1,
    role: 'ai',
    text: '你好！我是你的智能学习助手。在学习过程中遇到任何问题，都可以随时问我，我会为你提供详细的解答和讲解。',
    time: getCurrentTime(),
    isWelcome: true,
  },
])

const quickQuestions = [
  '什么是机器学习？',
  '解释一下反向传播算法',
  'Python中如何实现快速排序？',
  '什么是卷积神经网络？',
]

const exampleQuestions = [
  '什么是梯度下降？',
  '解释一下过拟合和欠拟合',
  'React Hooks是什么？',
  '如何理解闭包？',
]

function sanitizeHtml(html) {
  if (!html) return ''
  return html
    .replace(/<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>/gi, '')
    .replace(/<iframe\b[^<]*(?:(?!<\/iframe>)<[^<]*)*<\/iframe>/gi, '')
    .replace(/\son\w+\s*=\s*["'][^"']*["']/gi, '')
    .replace(/\son\w+\s*=\s*[^\s>]+/gi, '')
    .replace(/javascript:/gi, '')
}

const renderedExplanation = computed(() => {
  if (!currentExplanation.value) return ''
  try {
    return sanitizeHtml(marked(currentExplanation.value))
  } catch {
    return sanitizeHtml(`<pre>${currentExplanation.value}</pre>`)
  }
})

function getCurrentTime() {
  const now = new Date()
  return `${now.getHours().toString().padStart(2, '0')}:${now.getMinutes().toString().padStart(2, '0')}`
}

function scrollToBottom() {
  nextTick(() => {
    if (chatMessagesRef.value) {
      chatMessagesRef.value.scrollTop = chatMessagesRef.value.scrollHeight
    }
  })
}

const DEFAULT_COURSE_ID = 1

async function fetchTutorProfile() {
  try {
    const res = await getCurrentProfile()
    const profile = res?.profile
    if (!profile) return null
    return buildLearningPathProfilePayload(profile)
  } catch {
    return null
  }
}

function buildTutorRequestContext() {
  return {
    userId: getStoredUserId() ?? undefined,
    courseId: DEFAULT_COURSE_ID,
  }
}

function normalizeWeakPointsList(items) {
  if (!Array.isArray(items)) return []

  return items
    .map((item) => {
      if (typeof item === 'string') return item.trim()
      if (item && typeof item === 'object') {
        return String(item.name || item.label || item.knowledge_point || '').trim()
      }
      return ''
    })
    .filter(Boolean)
}

function parseWeakPointsValue(value) {
  if (value == null || value === '') return []

  if (Array.isArray(value)) {
    return normalizeWeakPointsList(value)
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
          return normalizeWeakPointsList(parsed)
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

function normalizeTutorProfile(profile) {
  if (!profile) return undefined

  const weakPoints = parseWeakPointsValue(profile.weak_points)
  const normalizedProfile = {
    ...profile,
    weak_points: Array.isArray(weakPoints) ? [...weakPoints] : [],
  }

  return normalizedProfile
}

function buildChatHistory(list, maxItems = 8) {
  return list
    .filter((item) => !item.isWelcome && !item.isError)
    .slice(-maxItems)
    .map((item) => (item.role === 'user' ? `用户：${item.text}` : `助手：${item.text}`))
}

function adaptTutorResponse(res) {
  const answer = res?.answer || ''
  const hints = Array.isArray(res?.hints) ? res.hints : []
  const nextAction = res?.next_action || ''
  const evidence = Array.isArray(res?.evidence) ? res.evidence : []

  const firstParagraph = answer.split(/\n\n+/)[0]?.trim() || answer
  const message =
    firstParagraph.length > 200 ? `${firstParagraph.slice(0, 200)}...` : firstParagraph

  let detailed = answer

  if (hints.length) {
    detailed += `\n\n### 提示\n${hints.map((hint) => `- ${hint}`).join('\n')}`
  }

  if (nextAction) {
    detailed += `\n\n### 下一步建议\n${nextAction}`
  }

  if (evidence.length) {
    detailed += `\n\n### 参考资料\n${evidence
      .map((item) => {
        const title = item.title || `资源 ${item.resource_id || ''}`
        const source = item.source || item.resource_id || item.chunk_id || ''
        const snippet = item.snippet || item.summary || ''
        let line = `- **${title}**`
        if (source) line += `（来源：${source}）`
        if (snippet) line += `\n  ${snippet}`
        return line
      })
      .join('\n')}`
  }

  return {
    message,
    detailedExplanation: detailed,
    visualAid: res?.visual_aid || null,
  }
}

async function requestTutorAnswer(question, { appendUserMessage = true } = {}) {
  const profile = await fetchTutorProfile()
  const history = buildChatHistory(messages.value)

  if (appendUserMessage) {
    messages.value.push({
      id: Date.now(),
      role: 'user',
      text: question,
      time: getCurrentTime(),
    })
    inputText.value = ''
    scrollToBottom()
  }

  isSending.value = true
  isTyping.value = true

  try {
    const { userId, courseId } = buildTutorRequestContext()
    const normalizedProfile = normalizeTutorProfile(profile)
    const res = await askTutor({
      question,
      profile: normalizedProfile,
      history,
      userId,
      courseId,
    })
    const adapted = adaptTutorResponse(res)

    isTyping.value = false

    messages.value.push({
      id: Date.now() + 1,
      role: 'ai',
      text: adapted.message,
      time: getCurrentTime(),
    })
    scrollToBottom()

    currentQuestion.value = question
    currentExplanation.value = adapted.detailedExplanation
    currentVisualAid.value = adapted.visualAid
    startVoicePlay(adapted.detailedExplanation)
  } catch {
    isTyping.value = false
    messages.value.push({
      id: Date.now() + 1,
      role: 'ai',
      text: '智能辅导服务暂时不可用，请稍后重试。',
      time: getCurrentTime(),
      isError: true,
    })
    scrollToBottom()
  } finally {
    isSending.value = false
  }
}

async function sendMessage() {
  const text = inputText.value.trim()
  if (!text || isSending.value) return
  await requestTutorAnswer(text)
}

function useQuickQuestion(question) {
  if (isSending.value) return
  inputText.value = question
  sendMessage()
}

async function regenerateAnswer() {
  if (!currentQuestion.value || isSending.value) return

  isSending.value = true
  isTyping.value = true

  try {
    const profile = await fetchTutorProfile()
    const history = buildChatHistory(messages.value)
    const { userId, courseId } = buildTutorRequestContext()
    const normalizedProfile = normalizeTutorProfile(profile)
    const res = await askTutor({
      question: currentQuestion.value,
      profile: normalizedProfile,
      history,
      userId,
      courseId,
    })
    const adapted = adaptTutorResponse(res)

    isTyping.value = false

    const lastAiMessage = [...messages.value]
      .reverse()
      .find((item) => item.role === 'ai' && !item.isWelcome && !item.isError)

    if (lastAiMessage) {
      lastAiMessage.text = adapted.message
      lastAiMessage.time = getCurrentTime()
    } else {
      messages.value.push({
        id: Date.now(),
        role: 'ai',
        text: adapted.message,
        time: getCurrentTime(),
      })
    }

    currentExplanation.value = adapted.detailedExplanation
    currentVisualAid.value = adapted.visualAid
    startVoicePlay(adapted.detailedExplanation)
    scrollToBottom()
  } catch {
    isTyping.value = false
    messages.value.push({
      id: Date.now(),
      role: 'ai',
      text: '智能辅导服务暂时不可用，请稍后重试。',
      time: getCurrentTime(),
      isError: true,
    })
    scrollToBottom()
  } finally {
    isSending.value = false
  }
}

function copyExplanation() {
  const text = currentExplanation.value
  navigator.clipboard.writeText(text).then(() => {
    alert('讲解内容已复制到剪贴板')
  }).catch(() => {
    alert('复制失败，请手动复制')
  })
}

function toggleVoice() {
  isVoiceEnabled.value = !isVoiceEnabled.value
}

function startVoicePlay() {
  if (!isVoiceEnabled.value) return

  isPlaying.value = true
  setTimeout(() => {
    isPlaying.value = false
  }, 3000)
}

function goHome() {
  router.push({ name: 'home' })
}

onMounted(() => {})
</script>

<style scoped>
.tutor-page {
  min-height: 100vh;
  padding: 32px;
  background: #f7f8fa;
  color: #111827;
  box-sizing: border-box;
}

.tutor-shell {
  width: 100%;
  max-width: 1600px;
  margin: 0 auto;
}

/* 头部样式 */
.section-head {
  position: relative;
  overflow: hidden;
  border-radius: 18px;
  padding: 54px 34px 24px 34px;
  margin: 0 0 24px;
  text-align: center;
  background: #ffffff;
  border: 1px solid #e5e7eb;
  box-shadow: var(--shadow-md);
}

.page-back-link {
  position: absolute;
  left: 24px;
  top: 22px;
  margin: 0 0 16px;
}

.eyebrow {
  margin: 0 0 10px;
  font-size: 13px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: #111827;
}

.section-head h2 {
  max-width: 760px;
  margin: 0 auto 10px;
  font-size: 34px;
  line-height: 1.25;
  color: #111827;
}

.section-desc {
  max-width: 760px;
  margin: 0 auto;
  line-height: 1.9;
  font-size: 15px;
  color: #111827;
}

/* 主布局 */
.tutor-layout {
  display: grid;
  grid-template-columns: 1fr 1.2fr;
  gap: 24px;
  align-items: stretch;
}

/* 左侧问答面板 */
.qa-panel {
  background: #ffffff;
  border: 1px solid #e5e7eb;
  border-radius: 18px;
  box-shadow: var(--shadow-md);
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.panel-header {
  padding: 20px 24px;
  border-bottom: 1px solid #e5e7eb;
  display: flex;
  align-items: center;
  gap: 14px;
  background: #ffffff;
}

.panel-icon {
  font-size: 32px;
}

.panel-header h3 {
  margin: 0;
  font-size: 20px;
  font-weight: 800;
  color: #111827;
}

.panel-header p {
  margin: 4px 0 0;
  font-size: 13px;
  color: #6b7280;
}

/* 聊天区域 */
.chat-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  padding: 20px;
}

.chat-messages {
  flex: 1;
  max-height: 500px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 16px;
  margin-bottom: 20px;
}

.message-item {
  display: flex;
  gap: 12px;
}

.message-item.user {
  flex-direction: row-reverse;
}

.message-avatar {
  width: 36px;
  height: 36px;
  border-radius: 12px;
  background: #f3f4f6;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  font-weight: 700;
  flex-shrink: 0;
  border: 1px solid #e5e7eb;
}

.message-item.user .message-avatar {
  background: #111827;
  color: #ffffff;
}

.message-bubble {
  max-width: 80%;
  padding: 12px 16px;
  border-radius: 16px;
  background: #f9fafb;
  border: 1px solid #e5e7eb;
}

.message-item.user .message-bubble {
  background: #111827;
  color: #ffffff;
  border-color: #111827;
}

.message-bubble p {
  margin: 0;
  line-height: 1.6;
  font-size: 14px;
}

.message-time {
  display: block;
  margin-top: 6px;
  font-size: 11px;
  color: #9ca3af;
}

.message-item.user .message-time {
  color: rgba(255, 255, 255, 0.6);
}

.typing-bubble {
  display: flex;
  gap: 4px;
  align-items: center;
  padding: 14px 16px;
}

.typing-bubble .dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #6b7280;
  animation: typing 1.4s infinite;
}

.typing-bubble .dot:nth-child(2) {
  animation-delay: 0.2s;
}

.typing-bubble .dot:nth-child(3) {
  animation-delay: 0.4s;
}

@keyframes typing {
  0%, 60%, 100% {
    opacity: 0.3;
    transform: translateY(0);
  }
  30% {
    opacity: 1;
    transform: translateY(-4px);
  }
}

/* 输入区域 */
.input-area {
  border-top: 1px solid #e5e7eb;
  padding-top: 16px;
}

.input-area textarea {
  width: 100%;
  border: 1px solid #e5e7eb;
  border-radius: 16px;
  padding: 12px 16px;
  resize: vertical;
  font-size: 14px;
  line-height: 1.6;
  font-family: inherit;
  outline: none;
  background: #f9fafb;
  color: #111827;
  box-sizing: border-box;
}

.input-area textarea:focus {
  border-color: #111827;
  box-shadow: 0 0 0 3px rgba(0, 0, 0, 0.08);
  background: #ffffff;
}

.input-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 12px;
  flex-wrap: wrap;
  gap: 12px;
}

.prompt-suggestions {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.prompt-suggestions button {
  padding: 6px 12px;
  border: 1px solid #e5e7eb;
  border-radius: 18px;
  background: #f3f4f6;
  color: #111827;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.prompt-suggestions button:hover {
  background: #111827;
  color: #ffffff;
  border-color: #111827;
}

.send-btn {
  padding: 8px 20px;
  border: none;
  border-radius: 14px;
  background: #111827;
  color: #ffffff;
  font-size: 14px;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.2s ease;
}

.send-btn:hover:not(:disabled) {
  background: #1f2937;
  transform: translateY(-2px);
}

.send-btn:disabled {
  opacity: 0.55;
  cursor: not-allowed;
}

/* 右侧讲解面板 */
.explanation-panel {
  background: #ffffff;
  border: 1px solid #e5e7eb;
  border-radius: 18px;
  box-shadow: var(--shadow-md);
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.explanation-content {
  flex: 1;
  padding: 24px;
}

/* 数字人区域 */
.avatar-section {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-bottom: 24px;
  border-bottom: 1px solid #e5e7eb;
  margin-bottom: 24px;
}

.digital-avatar {
  display: flex;
  align-items: center;
  gap: 16px;
}

.avatar-circle {
  position: relative;
  width: 80px;
  height: 80px;
  border-radius: 50%;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 8px 24px rgba(102, 126, 234, 0.3);
}

.avatar-wave {
  position: absolute;
  inset: -4px;
  border-radius: 50%;
  border: 2px solid #667eea;
  animation: wave 1.5s ease-out infinite;
}

@keyframes wave {
  0% {
    transform: scale(1);
    opacity: 0.8;
  }
  100% {
    transform: scale(1.3);
    opacity: 0;
  }
}

.avatar-emoji {
  font-size: 20px;
  font-weight: 800;
  color: #111827;
}

.avatar-status {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.status-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: #9ca3af;
  display: inline-block;
}

.status-dot.active {
  background: #10b981;
  animation: pulse 1s infinite;
}

@keyframes pulse {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.5;
  }
}

.voice-control {
  display: flex;
  align-items: center;
}

.voice-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  border: 1px solid #e5e7eb;
  border-radius: 18px;
  background: #f9fafb;
  cursor: pointer;
  transition: all 0.2s ease;
  font-size: 13px;
}

.voice-btn:hover {
  background: #f1f5f9;
}

/* 讲解内容区域 */
.explanation-text {
  min-height: 400px;
}

.empty-explanation {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  padding: 60px 20px;
}

.empty-icon {
  width: 80px;
  height: 80px;
  border-radius: 50%;
  background: #f3f4f6;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 40px;
  margin-bottom: 20px;
}

.empty-explanation h4 {
  margin: 0 0 10px;
  font-size: 20px;
  color: #111827;
}

.empty-explanation p {
  margin: 0 0 20px;
  color: #6b7280;
}

.example-questions {
  margin-top: 20px;
}

.example-questions p {
  margin-bottom: 12px;
  font-size: 13px;
}

.example-questions button {
  margin: 4px;
  padding: 8px 16px;
  border: 1px solid #e5e7eb;
  border-radius: 18px;
  background: #f9fafb;
  cursor: pointer;
  font-size: 13px;
  transition: all 0.2s ease;
}

.example-questions button:hover {
  background: #111827;
  color: #ffffff;
  border-color: #111827;
}

.explanation-wrapper {
  animation: fadeIn 0.3s ease;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.explanation-header {
  margin-bottom: 20px;
  padding-bottom: 12px;
  border-bottom: 1px solid #e5e7eb;
}

.question-badge {
  display: inline-block;
  padding: 4px 10px;
  background: #f3f4f6;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 700;
  margin-bottom: 10px;
}

.current-question {
  font-size: 18px;
  font-weight: 800;
  color: #111827;
  line-height: 1.4;
}

.explanation-body {
  max-height: 400px;
  overflow-y: auto;
  padding-right: 8px;
}

.visual-aid {
  margin: 22px 0 4px;
  padding: 16px;
  border: 1px solid #dbeafe;
  border-radius: 16px;
  background: linear-gradient(135deg, #eff6ff, #ecfeff);
}

.visual-aid h4 {
  margin: 0 0 14px;
  color: #0f172a;
}

.visual-flow {
  display: flex;
  align-items: stretch;
  gap: 8px;
}

.visual-node {
  flex: 1;
  min-width: 0;
  padding: 12px;
  border-radius: 12px;
  background: #ffffff;
  box-shadow: 0 6px 18px rgba(15, 23, 42, 0.06);
}

.visual-node span {
  display: block;
  color: #0891b2;
  font-size: 11px;
  font-weight: 800;
}

.visual-node strong {
  display: block;
  margin: 5px 0;
  color: #0f172a;
  font-size: 13px;
}

.visual-node p {
  margin: 0;
  color: #475569;
  font-size: 12px;
  line-height: 1.5;
}

.visual-arrow {
  align-self: center;
  color: #0891b2;
  font-weight: 900;
}

@media (max-width: 760px) {
  .visual-flow {
    flex-direction: column;
  }

  .visual-arrow {
    transform: rotate(90deg);
  }
}

/* Markdown 样式 */
.explanation-markdown {
  line-height: 1.8;
  color: #1f2937;
  font-size: 14px;
}

.explanation-markdown h1 {
  font-size: 24px;
  margin: 20px 0 12px;
  padding-bottom: 8px;
  border-bottom: 1px solid #e5e7eb;
  color: #111827;
}

.explanation-markdown h2 {
  font-size: 20px;
  margin: 18px 0 10px;
  color: #111827;
}

.explanation-markdown h3 {
  font-size: 18px;
  margin: 14px 0 8px;
  color: #111827;
}

.explanation-markdown p {
  margin: 12px 0;
}

.explanation-markdown ul,
.explanation-markdown ol {
  margin: 12px 0;
  padding-left: 28px;
}

.explanation-markdown li {
  margin: 6px 0;
}

.explanation-markdown code {
  background: #f3f4f6;
  padding: 2px 6px;
  border-radius: 4px;
  font-family: 'Courier New', monospace;
  font-size: 0.9em;
}

.explanation-markdown pre {
  background: #1f2937;
  color: #f3f4f6;
  padding: 16px;
  border-radius: 12px;
  overflow-x: auto;
  margin: 16px 0;
}

.explanation-markdown pre code {
  background: transparent;
  padding: 0;
  color: inherit;
}

.explanation-markdown blockquote {
  border-left: 4px solid #111827;
  margin: 16px 0;
  padding: 8px 0 8px 20px;
  color: #6b7280;
  font-style: italic;
}

.explanation-markdown table {
  border-collapse: collapse;
  width: 100%;
  margin: 16px 0;
}

.explanation-markdown th,
.explanation-markdown td {
  border: 1px solid #e5e7eb;
  padding: 10px 12px;
  text-align: left;
}

.explanation-markdown th {
  background: #f9fafb;
  font-weight: 700;
}

.explanation-actions {
  display: flex;
  gap: 12px;
  margin-top: 24px;
  padding-top: 16px;
  border-top: 1px solid #e5e7eb;
}

.action-btn {
  padding: 8px 16px;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  background: #f9fafb;
  cursor: pointer;
  font-size: 13px;
  font-weight: 600;
  transition: all 0.2s ease;
}

.action-btn:hover {
  background: #f1f5f9;
  transform: translateY(-2px);
}

/* 响应式 */
@media (max-width: 1100px) {
  .tutor-layout {
    grid-template-columns: 1fr;
  }

  .chat-messages {
    max-height: 400px;
  }
}

@media (max-width: 720px) {
  .tutor-page {
    padding: 18px;
  }

  .section-head {
    padding: 54px 20px 20px;
    border-radius: 18px;
  }

  .section-head h2 {
    font-size: 24px;
  }

  .qa-panel,
  .explanation-panel {
    border-radius: 18px;
  }

  .avatar-circle {
    width: 60px;
    height: 60px;
  }

  .avatar-emoji {
    font-size: 32px;
  }

  .input-actions {
    flex-direction: column;
  }

  .prompt-suggestions {
    width: 100%;
    justify-content: center;
  }

  .send-btn {
    width: 100%;
  }
}
</style>
