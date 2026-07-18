<template>
  <section class="agent-page">
    <div class="agent-shell">
      <header class="section-head hero-head">
        <div class="hero-bg"></div>
        <div class="hero-mask"></div>
        <button class="ui-back-link page-back-link" type="button" @click="goHome">
          ← 返回首页
        </button>
        <p class="eyebrow">多智能体协同 · 资源生成</p>
        <h2>多智能体协同的资源生成</h2>
        <p class="section-desc">
          通过智能问答采集学习需求，自动生成思维导图、详解文档、视频资源、在线习题和可编辑代码实操环境。
        </p>
      </header>

      <main class="agent-layout">
        <aside class="agent-nav">
          <button
            v-for="item in navItems"
            :key="item.key"
            class="nav-item"
            :class="{ active: activeKey === item.key }"
            @click="switchTab(item.key)"
          >
            <span class="nav-icon" aria-hidden="true">{{ item.icon }}</span>
            <span>
              <strong>{{ item.title }}</strong>
              <em>{{ item.desc }}</em>
            </span>
          </button>
        </aside>

        <section class="workspace">
          <div class="workspace-top">
            <div>
              <p class="workspace-label">当前任务</p>
              <h3>{{ currentNav.title }}</h3>
              <p>{{ currentNav.longDesc }}</p>
            </div>
            <div class="progress-card">
              <span>{{ taskStatusLabel }}</span>
              <strong>{{ taskProgress }}%</strong>
            </div>
          </div>

          <p v-if="pageError" class="page-error">{{ pageError }}</p>
          <p v-if="pollTimeoutMessage" class="page-info">{{ pollTimeoutMessage }}</p>

          <section v-if="agentTraces.length" class="trace-card">
            <div class="section-title-row">
              <div>
                <h4>智能体执行轨迹</h4>
                <p>来自任务 result.agent_traces，非前端模拟。</p>
              </div>
            </div>
            <article v-for="(trace, index) in agentTraces" :key="index" class="trace-item">
              <strong>{{ trace.agent }}</strong>
              <p>{{ trace.action }}</p>
              <span>{{ trace.output }}</span>
              <em v-if="trace.status">{{ trace.status }}</em>
            </article>
          </section>

          <section class="history-card">
            <div class="section-title-row">
              <div>
                <h4>历史生成任务</h4>
                <p>最近任务可查看结果或重新生成。</p>
              </div>
              <em>{{ historyTasks.length }} 条</em>
            </div>
            <div v-if="historyLoading" class="empty-state">加载历史任务...</div>
            <div v-else-if="!historyTasks.length" class="empty-state">暂无历史任务</div>
            <article
              v-for="item in historyTasks"
              :key="item.task_id"
              class="history-item"
              :class="{ active: currentTaskId === item.task_id }"
            >
              <div>
                <strong>{{ item.topic }}</strong>
                <p>{{ summarizeRequirement(item.requirement) }}</p>
                <span>{{ formatDate(item.created_at) }} · {{ statusText(item.status) }} · {{ item.progress }}%</span>
              </div>
              <div class="history-actions">
                <button class="ghost-btn" type="button" :disabled="isTaskRunning" @click="loadTaskResult(item.task_id)">
                  查看结果
                </button>
                <button
                  v-if="item.status === 'failed' || item.status === 'cancelled'"
                  class="ghost-btn"
                  type="button"
                  :disabled="isTaskRunning"
                  @click="retryHistoryTask(item)"
                >
                  重试
                </button>
                <button
                  v-if="item.status === 'pending' || item.status === 'running'"
                  class="ghost-btn danger-btn"
                  type="button"
                  @click="cancelHistoryTask(item)"
                >
                  取消
                </button>
              </div>
            </article>
          </section>

          <div class="generation-panel">
            <canvas ref="starCanvas" class="star-canvas"></canvas>
            <div class="panel-content">
              <div class="typing-head">
                <span class="pulse-dot"></span>
                <strong>多智能体资源生成系统</strong>
              </div>

              <div class="resource-preview">
                <template v-if="activeKey === 'qa'">
                  <div class="section-title-row">
                    <div>
                      <h4>智能问答 · 学习需求采集</h4>
                      <p>通过对话采集学习需求，AI将根据需求生成对应的学习资源。</p>
                    </div>
                  </div>

                  <div class="chat-box" ref="chatBoxRef">
                    <div v-for="msg in messages" :key="msg.id" class="chat-item" :class="msg.role">
                      <span>{{ msg.avatar }}</span>
                      <p>{{ msg.text }}<span v-if="msg.typing" class="chat-cursor"></span></p>
                    </div>
                  </div>

                  <div class="prompt-chips">
                    <button v-for="prompt in quickPrompts" :key="prompt" @click="usePrompt(prompt)">{{ prompt }}</button>
                  </div>

                  <form class="input-row" @submit.prevent="sendMessage">
                    <input v-model="inputText" placeholder="输入学习需求，如：我想学习机器学习基础" />
                    <button type="submit" :disabled="isSending || isTaskRunning">{{ isSending || isTaskRunning ? '处理中...' : '发送' }}</button>
                  </form>

                  <div class="generated-tip">
                    {{ resourceGenerated ? '已生成课程资源，可点击左侧查看思维导图、文档、视频、习题和代码实操。' : '发送需求后，AI将自动生成完整学习资源。' }}
                  </div>
                </template>

                <template v-else-if="activeKey === 'mindmap'">
                  <div class="section-title-row">
                    <div>
                      <h4>学习思维导图</h4>
                      <p>根据学习需求生成的知识结构导图。</p>
                    </div>
                    <div class="btn-group">
                      <button class="ghost-btn" type="button" @click="previewMindmap = true">全屏预览</button>
                      <button class="ghost-btn" type="button" @click="activeKey = 'doc'">查看详解文档</button>
                    </div>
                  </div>

                  <div v-if="isLoadingMindmap" class="empty-state">加载中...</div>
                  <div v-else-if="!mindNodes.length" class="empty-state" @click="activeKey = 'qa'">待生成，请先完成问答</div>
                  <div v-else class="mindmap-wrapper">
                    <div class="mindmap-container horizontal">
                      <div class="mindmap-center">
                        <div class="center-node">
                          <span class="center-title-vertical">{{ mindmapTitle }}</span>
                        </div>
                      </div>
                      <div class="mindmap-branches-horizontal">
                        <article
                          v-for="branch in mindmapBranches"
                          :key="branch.label"
                          class="branch-group-horizontal"
                        >
                          <div class="branch-main-horizontal">
                            <span class="branch-label-horizontal">{{ branch.label }}</span>
                          </div>
                          <div class="branch-children-horizontal">
                            <span
                              v-for="child in branch.children"
                              :key="child"
                              class="child-node-horizontal"
                            >
                              {{ child }}
                            </span>
                          </div>
                        </article>
                      </div>
                    </div>
                  </div>

                  <div v-if="previewMindmap" class="modal-overlay" @click.self="previewMindmap = false">
                    <div class="modal-content modal-large">
                      <div class="modal-header">
                        <div class="modal-title">
                          <h2>{{ mindmapTitle }}</h2>
                          <p>思维导图预览</p>
                        </div>
                        <button class="modal-close" type="button" aria-label="关闭预览" @click="previewMindmap = false">×</button>
                      </div>
                      <div class="modal-body">
                        <div class="mindmap-container horizontal preview-mode">
                          <div class="mindmap-center">
                            <div class="center-node">
                              <span class="center-title-vertical">{{ mindmapTitle }}</span>
                            </div>
                          </div>
                          <div class="mindmap-branches-horizontal">
                            <article
                              v-for="branch in mindmapBranches"
                              :key="`preview-${branch.label}`"
                              class="branch-group-horizontal"
                            >
                              <div class="branch-main-horizontal">{{ branch.label }}</div>
                              <div class="branch-children-horizontal">
                                <span
                                  v-for="child in branch.children"
                                  :key="child"
                                  class="child-node-horizontal"
                                >
                                  {{ child }}
                                </span>
                              </div>
                            </article>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                </template>

                <template v-else-if="activeKey === 'doc'">
                  <div class="section-title-row">
                    <div>
                      <h4>详解文档 · 支持预览和下载</h4>
                      <p>根据学习需求生成的详细学习文档。</p>
                    </div>
                    <div class="btn-group">
                      <button class="ghost-btn" @click="showDocPreview = !showDocPreview">{{ showDocPreview ? '收起预览' : '预览文档' }}</button>
                      <button class="ghost-btn" @click="downloadDocument('pdf')">PDF</button>
                      <button class="ghost-btn" @click="downloadDocument('pptx')">PPTX</button>
                      <button class="primary-btn" @click="downloadDocument('docx')">DOCX</button>
                    </div>
                  </div>

                  <div v-if="isLoadingDoc" class="empty-state">加载中...</div>
                  <div v-else-if="!documentSections.length" class="empty-state" @click="activeKey = 'qa'">待生成，请先完成问答</div>
                  <div v-else class="doc-layout">
                    <aside class="doc-toc">
                      <button
                        v-for="(section, index) in documentSections"
                        :key="section.title"
                        :class="{ active: activeDocIndex === index }"
                        @click="activeDocIndex = index"
                      >
                        <span>{{ String(index + 1).padStart(2, '0') }}</span>
                        {{ section.title }}
                      </button>
                    </aside>

                    <article class="doc-card markdown-body">
                      <h5>{{ activeDoc.title }}</h5>
                      <div v-html="renderMarkdown(activeDoc.content)"></div>
                      <ul>
                        <li v-for="point in activeDoc.points" :key="point">{{ point }}</li>
                      </ul>
                    </article>
                  </div>

                  <div v-if="showDocPreview && documentSections.length" class="doc-preview">
                    <h5>完整文档预览</h5>
                    <section v-for="section in documentSections" :key="section.title" class="markdown-body">
                      <strong>{{ section.title }}</strong>
                      <div v-html="renderMarkdown(section.content)"></div>
                    </section>
                  </div>
                </template>

                <template v-else-if="activeKey === 'video'">
                  <div class="section-title-row">
                    <div>
                      <h4>视频与动画资源 · 分页展示</h4>
                      <p>当前提供可播放动画预览与公开视频；正式视频渲染能力作为扩展接口保留。</p>
                    </div>
                    <span class="page-info">第 {{ videoPage }} / {{ totalVideoPages }} 页</span>
                  </div>

                  <div v-if="isLoadingVideo" class="empty-state">加载中...</div>
                  <div v-else-if="!videos.length" class="empty-state" @click="activeKey = 'qa'">待生成，请先完成问答</div>
                  <div v-else class="video-grid">
                    <article v-for="video in pagedVideos" :key="video.id" class="video-card">
                      <video
                        v-if="video.mp4Available && video.url"
                        class="video-player"
                        :src="video.url"
                        controls
                        preload="metadata"
                        playsinline
                        :aria-label="`${video.title} 播放器`"
                      />
                      <iframe
                        v-else-if="video.animationHtml"
                        class="animation-preview"
                        :srcdoc="video.animationHtml"
                        sandbox=""
                        loading="lazy"
                        :title="`${video.title} 播放器`"
                      />
                      <div v-else class="video-thumb">
                        <span>▶</span>
                        <em>{{ video.duration || '未提供' }}</em>
                      </div>
                      <strong>{{ video.title }}</strong>
                      <span v-if="video.mediaStatus === 'ready'" class="ready-badge">MP4 · 讯飞配音</span>
                      <span v-else-if="video.mediaStatus === 'preview'" class="preview-badge">动画预览</span>
                      <p>{{ video.desc }}</p>
                      <div class="video-meta">
                        <span>{{ video.level || '未提供' }}</span>
                        <span>{{ video.type || '视频' }}</span>
                      </div>
                      <a v-if="video.url" :href="video.url" class="video-link" target="_blank" rel="noopener noreferrer">打开视频</a>
                    </article>
                  </div>

                  <div v-if="videos.length" class="pagination">
                    <button :disabled="videoPage === 1" @click="videoPage--">上一页</button>
                    <button
                      v-for="page in totalVideoPages"
                      :key="page"
                      :class="{ active: videoPage === page }"
                      @click="videoPage = page"
                    >
                      {{ page }}
                    </button>
                    <button :disabled="videoPage === totalVideoPages" @click="videoPage++">下一页</button>
                  </div>
                </template>

                <template v-else-if="activeKey === 'exercise'">
                  <div class="section-title-row">
                    <div>
                      <h4>在线习题 · 练习模式</h4>
                      <p>根据任务结果展示练习题，批阅仅供自习参考，与正式学习评测无关。</p>
                    </div>
                    <button class="ghost-btn" @click="resetQuiz">重做习题</button>
                  </div>

                  <div v-if="isLoadingExercise" class="empty-state">加载中...</div>
                  <div v-else-if="!quizQuestions.length" class="empty-state" @click="activeKey = 'qa'">待生成，请先完成问答</div>
                  <div v-else class="quiz-list">
                    <article v-for="(q, index) in quizQuestions" :key="q.id" class="quiz-card">
                      <div class="quiz-head">
                        <strong>{{ index + 1 }}. {{ q.title }}</strong>
                        <span v-if="quizSubmitted" :class="q.gradable ? (isCorrect(q) ? 'right' : 'wrong') : 'review'">
                          {{ q.gradable ? (isCorrect(q) ? '正确' : '错误') : '参考答案' }}
                        </span>
                      </div>
                      <div class="quiz-question markdown-body" v-html="renderMarkdown(q.question)"></div>
                      <label v-for="option in q.options" :key="option.value" class="option-row">
                        <input v-model="answers[q.id]" type="radio" :name="q.id" :value="option.value" :disabled="quizSubmitted" />
                        <span>{{ option.value }}. {{ option.text }}</span>
                      </label>
                      <textarea
                        v-if="!q.options.length"
                        v-model.trim="answers[q.id]"
                        class="short-answer-input"
                        rows="4"
                        :disabled="quizSubmitted"
                        placeholder="写下你的思路和答案，提交后可对照参考答案复盘"
                      ></textarea>
                      <div v-if="quizSubmitted" class="analysis-box">
                        <div class="analysis-answer"><strong>参考答案：</strong>{{ q.answer || '暂无标准答案' }}</div>
                        <div class="analysis-detail">{{ q.analysis }}</div>
                      </div>
                    </article>
                  </div>

                  <div v-if="quizQuestions.length" class="quiz-footer">
                    <button class="primary-btn" @click="submitQuiz">提交批改</button>
                    <strong v-if="quizSubmitted && gradableQuestionCount">客观题得分：{{ quizScore }} / {{ gradableQuestionCount }}</strong>
                    <span v-else-if="quizSubmitted" class="review-hint">简答题请根据参考答案完成自评与复盘</span>
                  </div>
                </template>

                <template v-else-if="activeKey === 'reading'">
                  <div class="section-title-row">
                    <div>
                      <h4>拓展阅读材料</h4>
                      <p>根据学习需求推荐的拓展阅读资源。</p>
                    </div>
                  </div>

                  <div v-if="isLoadingReading" class="empty-state">加载中...</div>
                  <div v-else-if="!readings.length" class="empty-state" @click="activeKey = 'qa'">待生成，请先完成问答</div>
                  <div v-else class="reading-list">
                    <article v-for="r in readings" :key="r.title">
                      <span>{{ r.tag || '推荐' }}</span>
                      <strong>{{ r.title }}</strong>
                      <p>{{ r.desc }}</p>
                    </article>
                  </div>
                </template>

                <template v-else>
                  <div class="section-title-row">
                    <div>
                      <h4>代码实操 · 多语言在线编辑器</h4>
                      <p>支持 Python、JavaScript、Java、C++、HTML、SQL，可编辑并运行代码。</p>
                    </div>
                    <div class="btn-group">
                      <select v-model="selectedLanguage" class="language-select" @change="changeLanguage">
                        <option v-for="lang in codeLanguages" :key="lang.value" :value="lang.value">
                          {{ lang.label }}
                        </option>
                      </select>
                      <button class="ghost-btn" @click="resetCode">清空代码</button>
                      <button class="primary-btn" @click="runCode">运行代码</button>
                    </div>
                  </div>

                  <div class="code-editor-wrap">
                    <div class="editor-panel">
                      <div class="editor-toolbar">
                        <span>{{ currentLanguageLabel }}</span>
                        <em>可编辑</em>
                      </div>
                      <div class="editor-body">
                        <pre class="line-numbers">{{ lineNumbers }}</pre>
                        <textarea
                          v-model="editableCode"
                          spellcheck="false"
                          class="code-editor"
                          @keydown.tab.prevent="insertTab"
                        ></textarea>
                      </div>
                    </div>
                    <div class="code-output">
                      <strong>运行输出</strong>
                      <pre>{{ codeOutput }}</pre>
                    </div>
                  </div>
                </template>
              </div>
            </div>
          </div>
        </section>
      </main>
    </div>
  </section>
</template>

<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import {
  cancelTask as cancelProducerTask,
  chatWithAI,
  createTask,
  downloadTaskExport,
  downloadTaskVideo,
  getCodeExamples,
  getExercises,
  getRoadmap,
  getTaskResult,
  getTaskStatus,
  getVideos,
  listTasks,
  retryTask as retryProducerTask,
  runCode as runCodeApi,
} from '@/api/producer'
import {
  clearCurrentProducerTaskId,
  getCurrentProducerTaskId,
  setCurrentProducerTaskId,
} from '@/utils/producerSession'
import { normalizeDisplayContent, renderMarkdown } from '@/utils/contentPresentation'

const router = useRouter()

const POLL_INTERVAL_MS = 2000
const POLL_MAX_MS = 600000
const DEFAULT_TASK_TYPES = ['lecture', 'mind_map', 'exercise', 'video', 'code', 'dataset', 'roadmap']

const activeKey = ref('qa')
const inputText = ref('')
const resourceGenerated = ref(false)
const showDocPreview = ref(true)
const previewMindmap = ref(false)
const activeDocIndex = ref(0)
const videoPage = ref(1)
const pageSize = 6
const quizSubmitted = ref(false)
const answers = reactive({})
const chatBoxRef = ref(null)
const sessionId = ref('')
const isSending = ref(false)
const isTaskRunning = ref(false)
const currentTopic = ref('')
const currentRequirement = ref('')
const currentTaskId = ref('')
const taskStatus = ref('')
const taskProgress = ref(0)
const pageError = ref('')
const pollTimeoutMessage = ref('')
const historyTasks = ref([])
const historyLoading = ref(false)
const agentTraces = ref([])

const isLoadingMindmap = ref(false)
const isLoadingDoc = ref(false)
const isLoadingVideo = ref(false)
const isLoadingExercise = ref(false)
const isLoadingReading = ref(false)

let pollTimer = null
let pollStartedAt = 0

const navItems = [
  { key: 'qa', icon: '✦', title: '智能问答', desc: '需求采集', longDesc: '通过问答收集学习需求，AI自动生成课程资源。' },
  { key: 'mindmap', icon: '⌘', title: '思维导图', desc: '知识结构', longDesc: '根据学习需求生成知识结构导图。' },
  { key: 'doc', icon: '▤', title: '详解文档', desc: '预览下载', longDesc: '生成支持预览和下载的课程详解文档。' },
  { key: 'video', icon: '▶', title: '视频资源', desc: '分页学习', longDesc: '推荐的视频学习资源，支持分页切换。' },
  { key: 'exercise', icon: '✓', title: '在线习题', desc: '答题批改', longDesc: '生成练习题，支持在线作答和自动批改。' },
  { key: 'reading', icon: '⌁', title: '拓展阅读', desc: '延伸学习', longDesc: '推荐的拓展阅读材料。' },
  { key: 'code', icon: '</>', title: '代码实操', desc: '可编辑运行', longDesc: '多语言代码编辑器，可编辑并运行代码。' },
]

const statusLabels = {
  pending: '等待中',
  running: '生成中',
  completed: '已完成',
  failed: '失败',
  cancelled: '已取消',
}

const currentNav = computed(() => navItems.find(item => item.key === activeKey.value) || navItems[0])
const taskStatusLabel = computed(() => statusLabels[taskStatus.value] || (resourceGenerated.value ? '已完成' : '待生成'))
const mindmapTitle = ref('知识结构导图')

const messages = reactive([])
const initialAiMessage = '你好！请输入你的学习需求，例如：我想学习Python基础、机器学习入门等。我会根据你的需求生成完整的学习资源。'

const quickPrompts = [
  '我想学习Python基础',
  '生成机器学习入门课程资源',
  '需要前端开发学习路线',
  '数据库设计学习资料',
]

const mindNodes = reactive([])
const mindmapBranches = computed(() => mindNodes.map((node, index) => ({
  label: node.title || `分支 ${index + 1}`,
  children: Array.isArray(node.children) && node.children.length
    ? node.children
    : [node.desc || '核心知识点'],
})))
const documentSections = reactive([])
const activeDoc = computed(() => documentSections[activeDocIndex.value] || { title: '', content: '', points: [] })

const videos = reactive([])
const videoObjectUrls = new Set()
const totalVideoPages = computed(() => Math.max(1, Math.ceil(videos.length / pageSize)))
const pagedVideos = computed(() => videos.slice((videoPage.value - 1) * pageSize, videoPage.value * pageSize))

const quizQuestions = reactive([])
const gradableQuestionCount = computed(() => quizQuestions.filter(q => q.gradable).length)
const quizScore = computed(() => quizQuestions.reduce((sum, q) => sum + (q.gradable && isCorrect(q) ? 1 : 0), 0))

const readings = reactive([])
const codeExamples = ref([])

const defaultCode = `# 欢迎使用代码编辑器
# 请输入你的代码，点击运行查看结果

print("Hello, World!")`
const editableCode = ref(defaultCode)
const selectedLanguage = ref('python')
const codeOutput = ref('点击“运行代码”查看输出结果。')

const codeLanguages = [
  { value: 'python', label: 'Python' },
  { value: 'javascript', label: 'JavaScript' },
  { value: 'java', label: 'Java' },
  { value: 'cpp', label: 'C++' },
  { value: 'html', label: 'HTML' },
  { value: 'sql', label: 'SQL' },
]

const currentLanguageLabel = computed(() => codeLanguages.find(item => item.value === selectedLanguage.value)?.label || '代码')
const lineNumbers = computed(() => editableCode.value.split('\n').map((_, index) => index + 1).join('\n'))

function goHome() {
  router.push({ name: 'home' })
}

function statusText(status) {
  return statusLabels[status] || status || '未知'
}

function summarizeRequirement(text) {
  const value = String(text || '').trim()
  if (!value) return '无额外要求'
  return value.length > 80 ? `${value.slice(0, 80)}...` : value
}

function formatDate(value) {
  if (!value) return '未知时间'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value
  return date.toLocaleString()
}

function extractTopicAndRequirement(text) {
  const requirement = text.trim()
  if (!requirement) return { topic: '', requirement: '' }
  const firstSentence = requirement.split(/[。！？.!?\n]/)[0].trim()
  let topic = firstSentence || requirement
  const generatedSubject = topic.match(/生成\s*([^，,、]{2,30}?)(?=讲义|思维导图|练习题|习题|代码|课程资源|学习资料|学习路线|资源|$)/)
  if (generatedSubject?.[1]) topic = generatedSubject[1]
  topic = topic
    .replace(/^(?:请|请帮我|帮我)?(?:为|围绕|关于)?/, '')
    .replace(/^(?:我想|我希望|需要)?学习/, '')
    .replace(/^(?:我想|我希望|需要)/, '')
    .split(/(?:讲义|思维导图|练习题|习题|可运行代码|代码实操|课程资源|学习资料|学习路线|资源)/)[0]
    .replace(/(?:的|相关)$/, '')
    .trim()
  topic = (topic || firstSentence || requirement).slice(0, 50)
  return { topic, requirement }
}

function pickList(data, keys = ['items', 'list', 'nodes', 'questions', 'exercises', 'videos', 'code_examples']) {
  if (!data) return []
  if (Array.isArray(data)) return data
  for (const key of keys) {
    if (Array.isArray(data[key])) return data[key]
  }
  return []
}

function normalizeOptions(options) {
  if (!Array.isArray(options) || !options.length) {
    return []
  }
  if (typeof options[0] === 'string') {
    const letters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
    return options.map((text, index) => ({
      value: letters[index] || String(index + 1),
      text,
    }))
  }
  return options.map((option, index) => {
    if (typeof option === 'string') {
      const letters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
      return { value: letters[index] || String(index + 1), text: option }
    }
    return {
      value: option.value || option.label || String(index + 1),
      text: option.text || option.label || String(option.value || ''),
    }
  })
}

function parseLecture(lecture) {
  if (!lecture) return []
  if (typeof lecture === 'string') {
    return [{ title: '讲解文档', content: normalizeDisplayContent(lecture), points: [] }]
  }
  const content = lecture.content || ''
  const sections = content
    .split(/\n(?=##\s)/)
    .map(part => part.trim())
    .filter(Boolean)
    .map((part, index) => {
      const lines = part.split('\n')
      const title = lines[0].replace(/^#+\s*/, '').trim() || `章节${index + 1}`
      const body = normalizeDisplayContent(lines.slice(1).join('\n').trim())
      return {
        title,
        content: body || part,
        points: [],
      }
    })
  if (sections.length) return sections
  return [{
    title: lecture.title || '讲解文档',
    content: normalizeDisplayContent(content),
    points: pickList(lecture.references).map(item => item.title || item.name || '').filter(Boolean),
  }]
}

function normalizeMindmapChildren(value) {
  const items = Array.isArray(value) ? value : []
  return items
    .map(item => typeof item === 'string' ? item : item?.title || item?.name || item?.label || '')
    .map(item => String(item).trim())
    .filter(Boolean)
    .slice(0, 6)
}

function parseMindmapOutline(content) {
  const branches = []
  let current = null
  for (const rawLine of String(content || '').split('\n')) {
    const match = rawLine.match(/^(\s*)[-*]\s+(.+)$/)
    if (!match) continue
    const indent = match[1].replace(/\t/g, '  ').length
    const text = match[2].trim()
    if (!text) continue
    if (indent < 2 || !current) {
      current = { title: text, desc: '', children: [] }
      branches.push(current)
    } else if (current.children.length < 6) {
      current.children.push(text)
    }
  }
  return branches.slice(0, 9)
}

function buildMindNodes(mindMap, roadmap, topic) {
  if (mindMap?.content) {
    const outline = parseMindmapOutline(mindMap.content)
    if (outline.length) return outline
  }
  const generatedNodes = pickList(mindMap, ['nodes', 'items', 'list'])
  if (generatedNodes.length) {
    return generatedNodes.slice(0, 9).map((node, index) => ({
      title: node.label || node.title || node.name || `节点${index + 1}`,
      desc: node.desc || node.description || '',
      children: normalizeMindmapChildren(node.children || node.subtopics || node.points),
    }))
  }
  const roadmapNodes = pickList(roadmap, ['nodes', 'items', 'list'])
  if (roadmapNodes.length) {
    return roadmapNodes.map((node, index) => ({
      title: node.title || node.name || `节点${index + 1}`,
      desc: node.desc || node.description || '',
      children: normalizeMindmapChildren(node.children || node.subtopics || node.points),
    }))
  }
  if (mindMap?.title) mindmapTitle.value = mindMap.title
  return [{ title: topic || '知识结构', desc: '暂无详细节点，已降级为树状列表。', children: [] }]
}

function parseReading(reading, datasets) {
  const items = []
  if (reading) {
    if (typeof reading === 'string') {
      items.push({ title: '拓展阅读', desc: reading, tag: '推荐' })
    } else if (Array.isArray(reading)) {
      reading.forEach((entry, index) => {
        if (typeof entry === 'string') {
          items.push({ title: `阅读${index + 1}`, desc: entry, tag: '推荐' })
        } else {
          items.push({
            title: entry.title || `阅读${index + 1}`,
            desc: entry.desc || entry.description || entry.content || '',
            tag: entry.tag || '推荐阅读',
          })
        }
      })
    } else {
      items.push({
        title: reading.title || '拓展阅读',
        desc: reading.content || reading.description || '',
        tag: '必读推荐',
      })
      pickList(reading, ['items', 'references', 'list']).forEach((entry, index) => {
        items.push({
          title: entry.title || `参考资料${index + 1}`,
          desc: entry.description || entry.desc || entry.content || '',
          tag: entry.type || '参考资料',
        })
      })
    }
  }
  pickList(datasets).forEach((entry, index) => {
    items.push({
      title: entry.title || `数据集${index + 1}`,
      desc: entry.description || entry.desc || '',
      tag: '数据集',
    })
  })
  return items
}

function mapExercises(raw) {
  const questions = pickList(raw, ['items', 'questions', 'exercises', 'list'])
  return questions
    .filter(question => question && typeof question === 'object')
    .map((question, index) => {
      const options = normalizeOptions(question.options)
      return {
        id: question.id || index + 1,
        type: question.type || (options.length ? 'single_choice' : 'short_answer'),
        title: question.title || `习题 ${index + 1}`,
        question: normalizeDisplayContent(question.question || question.prompt || question.content || ''),
        options,
        answer: question.answer || '',
        analysis: question.analysis || question.explanation || '请对照参考答案检查概念、步骤与推理过程。',
        evidenceRefs: question.evidence_refs || [],
        gradable: options.length > 0 && Boolean(question.answer),
      }
    })
    .filter(question => question.question)
}

function mapVideos(raw) {
  const videoList = pickList(raw, ['items', 'videos', 'list'])
  return videoList.map((video, index) => ({
    id: video.id || index + 1,
    title: video.title || `视频${index + 1}`,
    desc: video.desc || video.description || '',
    duration: video.duration || '',
    level: video.level || '',
    type: video.type || '视频',
    url: video.mp4_available ? '' : (video.url || ''),
    apiUrl: video.url || '',
    generated: Boolean(video.generated),
    mediaStatus: video.media_status || '',
    renderingMode: video.rendering_mode || '',
    mp4Available: Boolean(video.mp4_available),
    animationHtml: video.animation_html || '',
  }))
}

function mapCodeExamples(raw) {
  return pickList(raw, ['items', 'code_examples', 'list']).map((item, index) => ({
    title: item.title || `代码案例${index + 1}`,
    code: item.code || '',
    explanation: item.explanation || item.description || '',
    language: item.language || 'python',
  }))
}

function applyTaskStatus(payload) {
  if (!payload) return
  taskStatus.value = payload.status || taskStatus.value
  taskProgress.value = Number(payload.progress ?? taskProgress.value)
  if (payload.error_message) pageError.value = payload.error_message
}

function applyTaskResult(result, topic) {
  if (!result) return
  const resolvedTopic = result.topic || topic || currentTopic.value
  currentTopic.value = resolvedTopic
  if (result.requirement) currentRequirement.value = result.requirement

  mindmapTitle.value = result.mind_map?.title || `${resolvedTopic} 思维导图`
  mindNodes.splice(0, mindNodes.length, ...buildMindNodes(result.mind_map, result.roadmap, resolvedTopic))

  documentSections.splice(0, documentSections.length, ...parseLecture(result.lecture))
  activeDocIndex.value = 0

  videos.splice(0, videos.length, ...mapVideos(result.videos))
  videoPage.value = 1

  quizQuestions.splice(0, quizQuestions.length, ...mapExercises(result.exercises))
  resetQuiz()

  readings.splice(0, readings.length, ...parseReading(result.reading, result.datasets))

  const mappedCode = mapCodeExamples(result.code_examples)
  codeExamples.value = mappedCode
  if (mappedCode.length) {
    editableCode.value = mappedCode[0].code || defaultCode
    selectedLanguage.value = mappedCode[0].language || selectedLanguage.value
  } else {
    editableCode.value = defaultCode
  }

  agentTraces.value = Array.isArray(result.agent_traces) ? result.agent_traces : []
  resourceGenerated.value = true
}

function clearVideoObjectUrls() {
  videoObjectUrls.forEach(url => URL.revokeObjectURL(url))
  videoObjectUrls.clear()
}

async function hydrateRenderedVideo(taskId) {
  const rendered = videos.find(video => video.mp4Available && video.apiUrl)
  if (!rendered) return
  clearVideoObjectUrls()
  try {
    const blob = await downloadTaskVideo(taskId)
    const url = URL.createObjectURL(blob)
    videoObjectUrls.add(url)
    rendered.url = url
  } catch (error) {
    console.error('加载正式视频失败:', error)
    rendered.mediaStatus = 'preview'
    rendered.mp4Available = false
  }
}

function clearPollTimer() {
  if (pollTimer) {
    clearTimeout(pollTimer)
    pollTimer = null
  }
}

function handleTaskError(error) {
  const status = error?.response?.status || error?.status
  const message = error?.response?.data?.detail || error?.message || '请求失败，请稍后重试'
  if (status === 404) {
    clearCurrentProducerTaskId()
    currentTaskId.value = ''
  }
  pageError.value = typeof message === 'string' ? message : JSON.stringify(message)
}

async function fetchTaskResult(taskId) {
  const resultRes = await getTaskResult(taskId)
  applyTaskStatus(resultRes)
  applyTaskResult(resultRes.result, currentTopic.value)
  await hydrateRenderedVideo(taskId)
  return resultRes
}

async function pollTaskUntilDone(taskId) {
  pollStartedAt = Date.now()
  pollTimeoutMessage.value = ''

  return new Promise(resolve => {
    const tick = async () => {
      if (Date.now() - pollStartedAt > POLL_MAX_MS) {
        clearPollTimer()
        pollTimeoutMessage.value = '任务仍在处理中，请稍后刷新'
        resolve(null)
        return
      }
      try {
        const statusRes = await getTaskStatus(taskId)
        applyTaskStatus(statusRes)
        if (statusRes.status === 'completed') {
          clearPollTimer()
          const resultRes = await fetchTaskResult(taskId)
          resolve(resultRes)
          return
        }
        if (statusRes.status === 'failed') {
          clearPollTimer()
          pageError.value = statusRes.error_message || '任务生成失败'
          resolve(statusRes)
          return
        }
        if (statusRes.status === 'cancelled') {
          clearPollTimer()
          taskStatus.value = 'cancelled'
          pollTimeoutMessage.value = '任务已取消'
          resolve(statusRes)
          return
        }
        pollTimer = window.setTimeout(tick, POLL_INTERVAL_MS)
      } catch (error) {
        handleTaskError(error)
        clearPollTimer()
        resolve(null)
      }
    }
    pollTimer = window.setTimeout(tick, POLL_INTERVAL_MS)
  })
}

async function loadHistoryTasks() {
  historyLoading.value = true
  try {
    const res = await listTasks({ limit: 20 })
    historyTasks.value = res.items || []
  } catch (error) {
    console.error('加载历史任务失败:', error)
  } finally {
    historyLoading.value = false
  }
}

async function loadTaskResult(taskId, persistSession = true) {
  if (!taskId || isTaskRunning.value) return
  pageError.value = ''
  pollTimeoutMessage.value = ''
  currentTaskId.value = taskId
  if (persistSession) setCurrentProducerTaskId(taskId)

  try {
    const statusRes = await getTaskStatus(taskId)
    applyTaskStatus(statusRes)
    const historyItem = historyTasks.value.find(item => item.task_id === taskId)
    if (historyItem) {
      currentTopic.value = historyItem.topic || currentTopic.value
      currentRequirement.value = historyItem.requirement || currentRequirement.value
    }
    if (statusRes.status === 'completed') {
      await fetchTaskResult(taskId)
      await typeAiMessage(`已恢复任务「${currentTopic.value}」的生成结果，可在左侧查看各资源。`)
    } else if (statusRes.status === 'failed') {
      pageError.value = statusRes.error_message || '任务生成失败'
    } else if (statusRes.status === 'cancelled') {
      pollTimeoutMessage.value = '任务已取消，可从历史任务中重试。'
    } else {
      isTaskRunning.value = true
      await pollTaskUntilDone(taskId)
      isTaskRunning.value = false
    }
  } catch (error) {
    handleTaskError(error)
  }
}

async function restoreTask(taskId) {
  await loadTaskResult(taskId, false)
}

async function startProducerTask(topic, requirement) {
  isTaskRunning.value = true
  pageError.value = ''
  pollTimeoutMessage.value = ''
  taskStatus.value = 'pending'
  taskProgress.value = 0
  resourceGenerated.value = false
  agentTraces.value = []

  try {
    const createRes = await createTask({
      topic,
      requirement,
      types: DEFAULT_TASK_TYPES,
      task_type: 'multi_agent_generation',
    })
    const taskId = createRes.task_id
    currentTaskId.value = taskId
    setCurrentProducerTaskId(taskId)
    applyTaskStatus(createRes)

    if (createRes.status === 'completed') {
      await fetchTaskResult(taskId)
    } else if (createRes.status === 'failed') {
      pageError.value = createRes.error_message || '任务生成失败'
    } else {
      await pollTaskUntilDone(taskId)
    }
    await loadHistoryTasks()
  } catch (error) {
    handleTaskError(error)
  } finally {
    isTaskRunning.value = false
  }
}

async function retryHistoryTask(item) {
  if (!item || isTaskRunning.value) return
  currentTopic.value = item.topic
  currentRequirement.value = item.requirement
  currentTaskId.value = item.task_id
  setCurrentProducerTaskId(item.task_id)
  isTaskRunning.value = true
  pageError.value = ''
  try {
    await typeAiMessage(`正在重试历史任务「${item.topic}」...`)
    const response = await retryProducerTask(item.task_id)
    applyTaskStatus(response)
    if (response.status === 'completed') {
      await fetchTaskResult(item.task_id)
    } else {
      await pollTaskUntilDone(item.task_id)
    }
    await loadHistoryTasks()
  } catch (error) {
    handleTaskError(error)
  } finally {
    isTaskRunning.value = false
  }
}

async function cancelHistoryTask(item) {
  if (!item) return
  pageError.value = ''
  try {
    const response = await cancelProducerTask(item.task_id)
    if (currentTaskId.value === item.task_id) {
      clearPollTimer()
      applyTaskStatus(response)
      isTaskRunning.value = false
      pollTimeoutMessage.value = '任务已取消，可随时重试。'
    }
    await loadHistoryTasks()
  } catch (error) {
    handleTaskError(error)
  }
}

function switchTab(key) {
  activeKey.value = key
  if (!resourceGenerated.value || !currentTopic.value) return
  if (key === 'mindmap' && !mindNodes.length) fetchMindmapFallback()
  if (key === 'doc' && !documentSections.length) fetchDocumentFallback()
  if (key === 'video' && !videos.length) fetchVideosFallback()
  if (key === 'exercise' && !quizQuestions.length) fetchExercisesFallback()
  if (key === 'reading' && !readings.length) fetchReadingsFallback()
  if (key === 'code' && !codeExamples.value.length && editableCode.value === defaultCode) fetchCodeFallback()
}

function usePrompt(prompt) {
  inputText.value = prompt
}

async function sendMessage() {
  const text = inputText.value.trim()
  if (!text || isSending.value || isTaskRunning.value) return

  const { topic, requirement } = extractTopicAndRequirement(text)
  currentTopic.value = topic
  currentRequirement.value = requirement

  messages.push({ id: Date.now(), role: 'user', avatar: '我', text })
  inputText.value = ''
  isSending.value = true
  scrollChat()

  try {
    const chatRes = await chatWithAI({
      message: text,
      session_id: sessionId.value,
      topic,
    })
    sessionId.value = chatRes.session_id || chatRes.sessionId || sessionId.value
    const aiReply = chatRes.reply || chatRes.message || chatRes.response || '已收到你的学习需求，正在创建生成任务...'
    await typeAiMessage(aiReply)

    await startProducerTask(topic, requirement)
    if (resourceGenerated.value) {
      await typeAiMessage('学习资源已生成！你可以点击左侧菜单查看思维导图、详解文档、视频资源、在线习题和拓展阅读。')
    }
  } catch (error) {
    console.error('发送消息失败:', error)
    handleTaskError(error)
    await typeAiMessage(pageError.value || error?.message || '请求失败，请稍后重试。')
  } finally {
    isSending.value = false
    scrollChat()
  }
}

async function fetchMindmapFallback() {
  if (!currentTopic.value) return
  isLoadingMindmap.value = true
  try {
    const res = await getRoadmap(currentTopic.value)
    mindNodes.splice(0, mindNodes.length, ...buildMindNodes(null, res, currentTopic.value))
    if (res.title) mindmapTitle.value = res.title
  } catch (error) {
    console.error('获取思维导图失败:', error)
  } finally {
    isLoadingMindmap.value = false
  }
}

async function fetchDocumentFallback() {
  if (!currentTopic.value) return
  isLoadingDoc.value = true
  try {
    const res = await getRoadmap(currentTopic.value)
    const nodes = pickList(res, ['nodes', 'items', 'list'])
    if (nodes.length) {
      documentSections.splice(0, documentSections.length, ...nodes.map((node, index) => ({
        title: node.title || `章节${index + 1}`,
        content: node.desc || node.description || `详细讲解${node.title || `章节${index + 1}`}的核心知识点。`,
        points: [
          `掌握${node.title || `章节${index + 1}`}的基本概念`,
          '理解相关应用场景',
          '完成配套练习巩固',
        ],
      })))
    }
  } catch (error) {
    console.error('获取文档失败:', error)
  } finally {
    isLoadingDoc.value = false
  }
}

async function fetchVideosFallback() {
  if (!currentTopic.value) return
  isLoadingVideo.value = true
  try {
    const res = await getVideos(currentTopic.value)
    videos.splice(0, videos.length, ...mapVideos(res))
    videoPage.value = 1
  } catch (error) {
    console.error('获取视频失败:', error)
  } finally {
    isLoadingVideo.value = false
  }
}

async function fetchExercisesFallback() {
  if (!currentTopic.value) return
  isLoadingExercise.value = true
  try {
    const res = await getExercises(currentTopic.value)
    quizQuestions.splice(0, quizQuestions.length, ...mapExercises(res))
    resetQuiz()
  } catch (error) {
    console.error('获取习题失败:', error)
  } finally {
    isLoadingExercise.value = false
  }
}

async function fetchReadingsFallback() {
  if (!currentTopic.value) return
  isLoadingReading.value = true
  try {
    const res = await getRoadmap(currentTopic.value)
    const nodes = pickList(res, ['nodes', 'items', 'list']).slice(0, 4)
    if (nodes.length) {
      readings.splice(0, readings.length, ...nodes.map((node, index) => ({
        title: `${node.title || `主题${index + 1}`}深度解析`,
        desc: `关于${node.title || `主题${index + 1}`}的拓展阅读，包含进阶知识和实践案例。`,
        tag: index === 0 ? '必读推荐' : '延伸阅读',
      })))
    }
  } catch (error) {
    console.error('获取阅读材料失败:', error)
  } finally {
    isLoadingReading.value = false
  }
}

async function fetchCodeFallback() {
  if (!currentTopic.value) return
  try {
    const res = await getCodeExamples(currentTopic.value, selectedLanguage.value)
    const mapped = mapCodeExamples(res)
    codeExamples.value = mapped
    if (mapped.length) editableCode.value = mapped[0].code || defaultCode
  } catch (error) {
    console.error('获取代码案例失败:', error)
  }
}

async function typeAiMessage(text, speed = 28) {
  const cleanText = String(text || '').trim()
  if (!cleanText) return

  const msg = reactive({
    id: Date.now() + Math.random(),
    role: 'ai',
    avatar: 'AI',
    text: '',
    typing: true,
  })

  messages.push(msg)
  scrollChat()

  for (let i = 0; i < cleanText.length; i++) {
    msg.text += cleanText[i]
    if (i % 2 === 0) scrollChat()
    await wait(speed)
  }

  msg.typing = false
  scrollChat()
}

function wait(ms) {
  return new Promise(resolve => setTimeout(resolve, ms))
}

function scrollChat() {
  nextTick(() => {
    if (chatBoxRef.value) chatBoxRef.value.scrollTop = chatBoxRef.value.scrollHeight
  })
}

async function downloadDocument(format = 'docx') {
  if (!currentTaskId.value) {
    pageError.value = '请先生成学习资源，再导出正式文件。'
    return
  }
  pageError.value = ''
  try {
    const blob = await downloadTaskExport(currentTaskId.value, format)
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `${currentTopic.value || '学习资源'}-个性化学习资源.${format}`
    link.click()
    URL.revokeObjectURL(url)
  } catch (error) {
    pageError.value = error?.message || '文件导出失败，请稍后重试。'
  }
}

function isCorrect(question) {
  if (!question.gradable) return false
  return String(answers[question.id] || '').trim().toUpperCase() === String(question.answer || '').trim().toUpperCase()
}

function submitQuiz() {
  quizSubmitted.value = true
}

function resetQuiz() {
  quizSubmitted.value = false
  quizQuestions.forEach(question => {
    answers[question.id] = ''
  })
}

async function runCode() {
  if (!editableCode.value.trim()) {
    codeOutput.value = '请先输入代码。'
    return
  }

  codeOutput.value = '正在提交后端运行接口...'
  try {
    const res = await runCodeApi({
      language: selectedLanguage.value,
      code: editableCode.value,
    })
    codeOutput.value = res.output || res.stdout || res.result || JSON.stringify(res, null, 2)
  } catch (error) {
    codeOutput.value = error?.message || '代码运行接口请求失败。'
  }
}

function resetCode() {
  if (codeExamples.value.length) {
    editableCode.value = codeExamples.value[0].code || defaultCode
  } else {
    editableCode.value = defaultCode
  }
  codeOutput.value = '代码已重置。'
}

async function changeLanguage() {
  codeOutput.value = `已切换到 ${currentLanguageLabel.value} 编辑器。`
  const matched = codeExamples.value.find(item => item.language === selectedLanguage.value)
  if (matched?.code) {
    editableCode.value = matched.code
    return
  }
  if (currentTopic.value && resourceGenerated.value) {
    await fetchCodeFallback()
  }
}

function insertTab(event) {
  const el = event.target
  const start = el.selectionStart
  const end = el.selectionEnd
  const value = editableCode.value
  editableCode.value = `${value.slice(0, start)}  ${value.slice(end)}`
  nextTick(() => {
    el.selectionStart = el.selectionEnd = start + 2
  })
}

const starCanvas = ref(null)
let stars = []
let animationId = 0
let resizeHandler = null

function initStars() {
  const canvas = starCanvas.value
  if (!canvas) return
  const ctx = canvas.getContext('2d')
  const resize = () => {
    canvas.width = canvas.offsetWidth
    canvas.height = canvas.offsetHeight
    stars = Array.from({ length: 70 }, () => ({
      x: Math.random() * canvas.width,
      y: Math.random() * canvas.height,
      r: Math.random() * 1.6 + 0.4,
      dx: (Math.random() - 0.5) * 0.35,
      dy: (Math.random() - 0.5) * 0.35,
      alpha: Math.random() * 0.5 + 0.2,
    }))
  }
  resize()
  resizeHandler = resize
  window.addEventListener('resize', resizeHandler)

  function animate() {
    ctx.clearRect(0, 0, canvas.width, canvas.height)
    stars.forEach(star => {
      star.x += star.dx
      star.y += star.dy
      if (star.x < 0 || star.x > canvas.width) star.dx *= -1
      if (star.y < 0 || star.y > canvas.height) star.dy *= -1
      ctx.beginPath()
      ctx.arc(star.x, star.y, star.r, 0, Math.PI * 2)
      ctx.fillStyle = `rgba(106,82,255,${star.alpha})`
      ctx.fill()
    })
    animationId = requestAnimationFrame(animate)
  }
  animate()
}

onMounted(async () => {
  initStars()
  await typeAiMessage(initialAiMessage, 18)
  await loadHistoryTasks()

  const savedTaskId = getCurrentProducerTaskId()
  if (savedTaskId) {
    await restoreTask(savedTaskId)
  } else if (historyTasks.value.length) {
    const latestCompleted = historyTasks.value.find(item => item.status === 'completed')
    if (latestCompleted) {
      await loadTaskResult(latestCompleted.task_id, true)
    }
  }
})

onBeforeUnmount(() => {
  clearPollTimer()
  clearVideoObjectUrls()
  if (animationId) cancelAnimationFrame(animationId)
  if (resizeHandler) window.removeEventListener('resize', resizeHandler)
})
</script>

<style scoped>
.agent-page {
  min-height: 100vh;
  padding: 32px;
  background: transparent;
  color: #1a1a2e;
  box-sizing: border-box;
  scroll-behavior: smooth;
}

.agent-shell {
  width: 100%;
  max-width: 1380px;
  margin: 0 auto;
}

.section-head {
  position: relative;
  overflow: hidden;
  border-radius: 20px;
  padding: 48px 34px 28px 34px;
  margin: 0 0 24px;
  text-align: center;
  background: #ffffff;
  border: 1px solid #e5e7eb;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.04);
}

.hero-head {
  width: 100%;
  box-sizing: border-box;
}

.page-back-link {
  position: absolute;
  left: 24px;
  top: 20px;
  background: #f3f4f6;
  border: 1px solid #e5e7eb;
  padding: 8px 16px;
  border-radius: 10px;
  font-weight: 600;
  font-size: 14px;
  color: #1a1a2e;
  cursor: pointer;
  transition: all 0.2s;
}

.page-back-link:hover {
  background: #e5e7eb;
}

.eyebrow {
  margin: 0 0 8px;
  font-size: 14px;
  font-weight: 700;
  letter-spacing: 0.06em;
  color: #4a5568;
}

.section-head h2 {
  max-width: 760px;
  margin: 0 auto 12px;
  font-size: 32px;
  line-height: 1.25;
  color: #1a1a2e;
}

.section-desc {
  max-width: 760px;
  margin-left: auto;
  margin-right: auto;
  color: #4a5568;
  font-size: 15px;
  line-height: 1.8;
}

.agent-layout {
  display: grid;
  grid-template-columns: 260px minmax(0, 1fr);
  gap: 30px;
  align-items: flex-start;
}

.agent-nav {
  position: sticky;
  top: 28px;
  height: fit-content;
  background: #ffffff;
  border: 1px solid #e5e7eb;
  border-radius: 18px;
  padding: 16px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.04);
}

.nav-item {
  width: 100%;
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 14px;
  margin: 4px 0;
  border: none;
  border-radius: 12px;
  background: transparent;
  color: #1a1a2e;
  text-align: left;
  cursor: pointer;
  transition: all 0.25s ease;
}

.nav-item:hover {
  background: #f3f4f6;
}

.nav-item.active {
  background: #1a1a2e;
  color: #ffffff;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.2);
}

.nav-item.active em {
  color: rgba(255,255,255,0.7);
}

.nav-item.active strong {
  color: #ffffff;
}

.nav-icon {
  font-size: 18px;
  flex-shrink: 0;
}

.nav-item strong {
  display: block;
  font-size: 14px;
  font-weight: 700;
  color: #1a1a2e;
}

.nav-item em {
  display: block;
  margin-top: 2px;
  font-style: normal;
  font-size: 12px;
  color: #6b7280;
}

.workspace {
  background: #ffffff;
  border: 1px solid #e5e7eb;
  border-radius: 18px;
  padding: 28px 32px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.04);
}

.workspace-top {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 18px;
  margin-bottom: 24px;
}

.workspace-label {
  margin: 0 0 6px;
  font-size: 13px;
  font-weight: 700;
  letter-spacing: 0.04em;
  color: #6b7280;
}

.workspace-top h3 {
  margin: 0 0 8px;
  font-size: 26px;
  line-height: 1.3;
  color: #1a1a2e;
}

.workspace-top p {
  margin: 0;
  color: #4a5568;
  font-size: 14px;
  line-height: 1.6;
}

.progress-card {
  min-width: 130px;
  padding: 14px 20px;
  background: #f8f9fc;
  border: 1px solid #e5e7eb;
  border-radius: 14px;
  text-align: right;
}

.progress-card span {
  display: block;
  margin-bottom: 6px;
  color: #6b7280;
  font-size: 13px;
  font-weight: 600;
}

.progress-card strong {
  font-size: 32px;
  line-height: 1;
  color: #1a1a2e;
}

.generation-panel {
  position: relative;
  border-radius: 18px;
  overflow: hidden;
  background: #fafbfc;
  border: 1px solid #e5e7eb;
}

.panel-content {
  position: relative;
  z-index: 1;
  padding: 20px 24px;
}

.typing-head {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
  color: #1a1a2e;
  font-weight: 700;
  font-size: 16px;
}

.resource-preview {
  background: #ffffff;
  border-radius: 16px;
  padding: 22px 24px;
  border: 1px solid #e5e7eb;
}

.section-title-row {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 16px;
  flex-wrap: wrap;
}

.resource-preview h4 {
  margin: 0 0 6px;
  font-size: 20px;
  font-weight: 800;
  color: #1a1a2e;
}

.section-title-row p {
  margin: 0;
  color: #6b7280;
  font-size: 14px;
  line-height: 1.6;
}

.section-title-row em {
  font-style: normal;
  padding: 4px 12px;
  border-radius: 999px;
  background: #f3f4f6;
  color: #1a1a2e;
  font-size: 13px;
  font-weight: 700;
}

.primary-btn, .ghost-btn {
  padding: 8px 18px;
  border-radius: 10px;
  font-weight: 700;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s ease;
  border: none;
}

.primary-btn {
  background: #1a1a2e;
  color: #ffffff;
}

.primary-btn:hover {
  background: #2d3748;
  transform: translateY(-1px);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.2);
}

.ghost-btn {
  background: #f3f4f6;
  color: #1a1a2e;
  border: 1px solid #e5e7eb;
}

.ghost-btn:hover {
  background: #e5e7eb;
}

.btn-group {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  align-items: center;
}

/* ===== 聊天样式 ===== */
.chat-box {
  display: flex;
  flex-direction: column;
  gap: 10px;
  max-height: 240px;
  overflow-y: auto;
  margin-bottom: 12px;
  padding-right: 4px;
}

.chat-item {
  display: flex;
  gap: 10px;
  align-items: flex-start;
}

.chat-item.user {
  flex-direction: row-reverse;
}

.chat-item > span {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: #e5e7eb;
  color: #1a1a2e;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 13px;
  font-weight: 700;
  flex-shrink: 0;
}

.chat-item.user > span {
  background: #1a1a2e;
  color: #ffffff;
}

.chat-item .ai-avatar {
  background: #1a1a2e;
  color: #ffffff;
  font-size: 16px;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
}

.chat-item .dot-loader {
  display: flex;
  align-items: center;
  gap: 2px;
  font-size: 20px;
  font-weight: 700;
  letter-spacing: 2px;
  animation: dotPulse 1.2s infinite;
}

.chat-item .dot-loader span {
  background: transparent;
  color: #ffffff;
  font-size: 20px;
  width: auto;
  height: auto;
  border-radius: 0;
  display: inline;
  padding: 0;
}

@keyframes dotPulse {
  0% { opacity: 0.3; }
  50% { opacity: 1; }
  100% { opacity: 0.3; }
}

.chat-item.ai p {
  max-width: 80%;
  margin: 0;
  padding: 6px 0;
  color: #1a1a2e;
  font-size: 15px;
  line-height: 1.7;
  background: transparent;
}

.chat-item.user p {
  max-width: 80%;
  margin: 0;
  padding: 10px 16px;
  border-radius: 14px;
  background: #1a1a2e;
  color: #ffffff;
  font-size: 15px;
  line-height: 1.6;
}

.prompt-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 12px;
}

.prompt-chips button {
  border: 1px solid #e5e7eb;
  padding: 6px 14px;
  border-radius: 999px;
  background: #f3f4f6;
  color: #1a1a2e;
  cursor: pointer;
  font-size: 13px;
  font-weight: 600;
  transition: all 0.2s;
}

.prompt-chips button:hover {
  background: #e5e7eb;
  border-color: #1a1a2e;
}

.input-row {
  display: flex;
  gap: 10px;
}

.input-row input {
  flex: 1;
  height: 44px;
  border: 1px solid #e5e7eb;
  outline: none;
  border-radius: 12px;
  padding: 0 14px;
  color: #1a1a2e;
  background: #ffffff;
  font-size: 14px;
  transition: border-color 0.2s;
}

.input-row input:focus {
  border-color: #1a1a2e;
  box-shadow: 0 0 0 3px rgba(0, 0, 0, 0.05);
}

.input-row button {
  border: none;
  padding: 0 20px;
  height: 44px;
  border-radius: 12px;
  background: #1a1a2e;
  color: #ffffff;
  font-weight: 700;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.2s;
}

.input-row button:hover:not(:disabled) {
  background: #2d3748;
  transform: translateY(-1px);
}

.input-row button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.generated-tip {
  margin-top: 14px;
  padding: 12px 16px;
  border-radius: 12px;
  background: #f0fdf4;
  border: 1px solid #bbf7d0;
  color: #166534;
  font-size: 14px;
  font-weight: 600;
}

.empty-state {
  padding: 24px;
  text-align: center;
  font-weight: 600;
  color: #6b7280;
  border-radius: 12px;
  background: #f9fafb;
  border: 1px dashed #d1d5db;
  cursor: pointer;
  transition: all 0.2s;
}

.empty-state:hover {
  border-color: #1a1a2e;
  color: #1a1a2e;
}

/* ===== 思维导图样式 - 简洁整齐，无连线 ===== */
.mindmap-wrapper {
  padding: 20px;
  background: #fafbfc;
  border-radius: 14px;
  border: 1px solid #e5e7eb;
  overflow-x: auto;
}

.mindmap-container.horizontal {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  min-height: 780px;
  padding: 20px 0 20px 20px;
}

.mindmap-center {
  position: absolute;
  left: 20px;
  top: 50%;
  transform: translateY(-50%);
  z-index: 2;
}

.center-node {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 24px 16px;
  background: #1a1a2e;
  border-radius: 16px;
  box-shadow: 0 6px 24px rgba(0, 0, 0, 0.15);
  color: #ffffff;
  min-width: 60px;
  min-height: 120px;
}

.center-title-vertical {
  font-size: 18px;
  font-weight: 800;
  letter-spacing: 6px;
  color: #ffffff;
  writing-mode: vertical-rl;
  text-orientation: upright;
  line-height: 1.8;
}

.mindmap-branches-horizontal {
  position: relative;
  z-index: 2;
  width: 100%;
  padding-left: 180px;
}

.branch-group-horizontal {
  position: absolute;
  left: 160px;
  display: flex;
  align-items: center;
  gap: 16px;
}

/* 分支垂直位置 */
.branch-group-horizontal:nth-child(1) { top: 38px; }
.branch-group-horizontal:nth-child(2) { top: 108px; }
.branch-group-horizontal:nth-child(3) { top: 178px; }
.branch-group-horizontal:nth-child(4) { top: 248px; }
.branch-group-horizontal:nth-child(5) { top: 318px; }
.branch-group-horizontal:nth-child(6) { top: 388px; }
.branch-group-horizontal:nth-child(7) { top: 458px; }
.branch-group-horizontal:nth-child(8) { top: 528px; }
.branch-group-horizontal:nth-child(9) { top: 598px; }

.branch-main-horizontal {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 10px 16px;
  background: #ffffff;
  border-radius: 10px;
  border: 2px solid #2d3748;
  box-shadow: 0 2px 8px rgba(0,0,0,0.06);
  font-weight: 700;
  font-size: 14px;
  color: #1a1a2e;
  min-width: 70px;
  min-height: 44px;
}

.branch-label-horizontal {
  font-weight: 700;
  color: #1a1a2e;
  font-size: 14px;
  white-space: nowrap;
}

.branch-children-horizontal {
  display: flex;
  gap: 8px 14px;
  flex-wrap: wrap;
  align-items: center;
  margin-left: 8px;
}

.child-node-horizontal {
  padding: 5px 14px;
  background: #ffffff;
  border-radius: 8px;
  border: 1px solid #e5e7eb;
  font-size: 13px;
  font-weight: 600;
  color: #1a1a2e;
  box-shadow: 0 1px 4px rgba(0,0,0,0.03);
  white-space: nowrap;
  transition: all 0.2s;
}

.child-node-horizontal:hover {
  border-color: #1a1a2e;
  background: #f3f4f6;
  transform: translateY(-1px);
}

/* 预览模式 */
.preview-mode .mindmap-branches-horizontal {
  padding-left: 180px;
}

.preview-mode .branch-group-horizontal {
  left: 160px;
}

/* ===== 视频样式 ===== */
.video-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 16px;
}

.video-card {
  padding: 16px;
  border-radius: 14px;
  background: #f9fafb;
  border: 1px solid #e5e7eb;
  display: flex;
  flex-direction: column;
  transition: all 0.25s;
}

.video-card:hover {
  transform: translateY(-3px);
  box-shadow: 0 8px 24px rgba(0,0,0,0.08);
}

.video-thumb {
  position: relative;
  height: 100px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 10px;
  cursor: pointer;
  background: #2d3748;
}

.video-thumb .play-icon {
  width: 44px;
  height: 44px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.2);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  color: #ffffff;
}

.video-thumb em {
  position: absolute;
  right: 10px;
  bottom: 8px;
  font-size: 11px;
  font-style: normal;
  background: rgba(0,0,0,0.6);
  padding: 2px 10px;
  border-radius: 4px;
  color: #ffffff;
}

.video-card strong {
  color: #1a1a2e;
  font-size: 15px;
  font-weight: 700;
  margin-bottom: 4px;
}

.video-card p {
  margin: 0 0 8px;
  color: #4a5568;
  font-size: 13px;
  line-height: 1.5;
  flex: 1;
}

.video-meta {
  display: flex;
  gap: 12px;
  font-size: 12px;
  font-weight: 600;
  color: #6b7280;
  margin-bottom: 8px;
}

.video-link {
  color: #1a1a2e;
  font-size: 13px;
  font-weight: 700;
  text-decoration: none;
  transition: color 0.2s;
}

.video-link:hover {
  color: #4a5568;
  text-decoration: underline;
}

.pagination {
  display: flex;
  justify-content: center;
  gap: 8px;
  margin-top: 18px;
  flex-wrap: wrap;
}

.pagination button {
  min-width: 36px;
  border: 1px solid #e5e7eb;
  background: #ffffff;
  color: #1a1a2e;
  padding: 6px 12px;
  border-radius: 8px;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.pagination button.active,
.pagination button:hover:not(:disabled) {
  background: #1a1a2e;
  color: #ffffff;
  border-color: #1a1a2e;
}

.pagination button:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

/* ===== 文档样式 ===== */
.doc-layout {
  display: grid;
  grid-template-columns: 200px 1fr;
  gap: 16px;
}

.doc-toc {
  display: grid;
  gap: 6px;
}

.doc-toc button {
  border: 1px solid #e5e7eb;
  border-radius: 10px;
  background: #ffffff;
  padding: 8px 12px;
  cursor: pointer;
  text-align: left;
  color: #1a1a2e;
  font-weight: 600;
  font-size: 13px;
  transition: all 0.2s;
}

.doc-toc button:hover,
.doc-toc button.active {
  background: #f3f4f6;
  border-color: #1a1a2e;
}

.doc-toc span {
  display: block;
  margin-bottom: 2px;
  color: #9ca3af;
  font-size: 11px;
}

.doc-card, .doc-preview {
  padding: 16px 20px;
  border-radius: 12px;
  background: #f9fafb;
  border: 1px solid #e5e7eb;
}

.doc-card h5 {
  margin: 0 0 10px;
  font-size: 18px;
  color: #1a1a2e;
}

.doc-card p {
  margin: 0 0 12px;
  color: #374151;
  line-height: 1.8;
  font-size: 14px;
}

.doc-card ul {
  margin: 0;
  padding-left: 20px;
}

.doc-card li {
  color: #374151;
  line-height: 1.7;
  font-size: 14px;
}

.doc-preview {
  margin-top: 14px;
  max-height: 260px;
  overflow-y: auto;
}

.doc-preview section {
  padding: 10px 0;
  border-bottom: 1px solid #e5e7eb;
}

.doc-preview strong {
  display: block;
  color: #1a1a2e;
  font-size: 15px;
}

.doc-preview p {
  margin: 4px 0 0;
  color: #4a5568;
  font-size: 14px;
  line-height: 1.6;
}

/* ===== 习题样式 ===== */
.quiz-list {
  display: grid;
  gap: 20px;
}

.quiz-card {
  padding: 20px 24px;
  border-radius: 14px;
  background: #f9fafb;
  border: 1px solid #e5e7eb;
  transition: all 0.2s;
}

.quiz-card:hover {
  border-color: #d1d5db;
}

.quiz-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  margin-bottom: 8px;
}

.quiz-head strong {
  color: #1a1a2e;
  font-size: 16px;
}

.quiz-question {
  margin: 0 0 12px;
  color: #374151;
  font-size: 15px;
  line-height: 1.6;
  font-weight: 500;
}

.option-row {
  display: flex;
  gap: 10px;
  align-items: center;
  padding: 10px 14px;
  border-radius: 8px;
  background: #ffffff;
  border: 1px solid #e5e7eb;
  cursor: pointer;
  color: #1a1a2e;
  font-size: 14px;
  transition: all 0.2s;
  margin: 4px 0;
}

.option-row:hover {
  border-color: #1a1a2e;
  background: #f8f9fc;
}

.option-row input[type="radio"] {
  accent-color: #1a1a2e;
  width: 17px;
  height: 17px;
  flex-shrink: 0;
}

.right, .wrong {
  padding: 4px 14px;
  border-radius: 999px;
  font-size: 13px;
  font-weight: 700;
}

.right {
  background: #dcfce7;
  color: #166534;
}

.wrong {
  background: #fee2e2;
  color: #991b1b;
}

.analysis-box {
  margin-top: 14px;
  padding: 16px 20px;
  border-radius: 10px;
  background: #f0f4ff;
  border: 1px solid #dbeafe;
  color: #1a1a2e;
  font-size: 14px;
  line-height: 1.7;
}

.analysis-answer {
  margin-bottom: 8px;
  font-weight: 600;
  color: #1a1a2e;
}

.analysis-answer strong {
  color: #166534;
}

.analysis-detail {
  color: #374151;
}

.quiz-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 16px;
  flex-wrap: wrap;
  gap: 12px;
}

.quiz-footer strong {
  color: #1a1a2e;
  font-size: 18px;
  font-weight: 800;
}

/* ===== 阅读样式 ===== */
.reading-list {
  display: grid;
  gap: 14px;
}

.reading-list article {
  padding: 16px 20px;
  border-radius: 14px;
  background: #f9fafb;
  border: 1px solid #e5e7eb;
  transition: all 0.2s;
}

.reading-list article:hover {
  border-color: #1a1a2e;
}

.reading-list article span {
  display: inline-block;
  margin-bottom: 6px;
  padding: 3px 12px;
  border-radius: 999px;
  background: #f3f4f6;
  color: #1a1a2e;
  font-size: 12px;
  font-weight: 700;
}

.reading-list article strong {
  display: block;
  color: #1a1a2e;
  font-size: 16px;
  margin-bottom: 4px;
}

.reading-list article p {
  margin: 0;
  color: #4a5568;
  font-size: 14px;
  line-height: 1.6;
}

/* ===== 代码编辑器样式 ===== */
.language-select {
  height: 38px;
  min-width: 110px;
  padding: 0 30px 0 12px;
  border: 1px solid #e5e7eb;
  border-radius: 10px;
  background: #ffffff;
  color: #1a1a2e;
  font-size: 13px;
  font-weight: 600;
  outline: none;
  cursor: pointer;
  appearance: none;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='10' height='6'%3E%3Cpath d='M0 0l5 6 5-6z' fill='%236b7280'/%3E%3C/svg%3E");
  background-repeat: no-repeat;
  background-position: right 10px center;
}

.language-select:focus {
  border-color: #1a1a2e;
}

.code-editor-wrap {
  display: grid;
  grid-template-columns: 1.35fr 0.65fr;
  gap: 16px;
}

.editor-panel, .code-output {
  overflow: hidden;
  border-radius: 14px;
  background: #0d1117;
  color: #e6edf3;
  border: 1px solid #21262d;
}

.editor-toolbar {
  height: 38px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 14px;
  background: #161b22;
  border-bottom: 1px solid #21262d;
  font-size: 13px;
  font-weight: 700;
  color: #e6edf3;
}

.editor-toolbar em {
  font-style: normal;
  color: #8b949e;
  font-size: 12px;
}

.editor-body {
  display: grid;
  grid-template-columns: 44px 1fr;
  min-height: 340px;
}

.line-numbers {
  margin: 0;
  padding: 12px 8px;
  background: #0d1117;
  color: #4a5568;
  text-align: right;
  user-select: none;
  font-family: 'JetBrains Mono', 'Fira Code', Consolas, monospace;
  font-size: 12px;
  line-height: 1.7;
  white-space: pre;
  overflow: hidden;
}

.code-editor {
  width: 100%;
  min-height: 340px;
  padding: 12px 16px;
  resize: vertical;
  border: none;
  outline: none;
  background: #0d1117;
  color: #e6edf3;
  font-family: 'JetBrains Mono', 'Fira Code', Consolas, monospace;
  font-size: 12px;
  line-height: 1.7;
  box-sizing: border-box;
  tab-size: 2;
}

.code-editor:focus {
  border: none;
  outline: none;
}

.code-output {
  padding: 16px;
  font-family: 'JetBrains Mono', 'Fira Code', Consolas, monospace;
  font-size: 12px;
  line-height: 1.7;
}

.code-output strong {
  display: block;
  margin-bottom: 10px;
  color: #e6edf3;
  font-size: 13px;
}

.code-output pre {
  white-space: pre-wrap;
  line-height: 1.6;
  margin: 0;
  font-size: 12px;
  color: #e6edf3;
}

/* ===== 历史任务 ===== */
.history-card {
  margin-bottom: 20px;
  padding: 18px 22px;
  border-radius: 16px;
  background: #ffffff;
  border: 1px solid #e5e7eb;
}

.history-item {
  padding: 14px 16px;
  margin-top: 10px;
  border-radius: 12px;
  background: #f9fafb;
  border: 1px solid #e5e7eb;
  display: flex;
  justify-content: space-between;
  gap: 16px;
  align-items: flex-start;
  transition: all 0.2s;
}

.history-item:hover {
  border-color: #1a1a2e;
}

.history-item.active {
  border-color: #1a1a2e;
  background: #f3f4f6;
}

.history-item strong {
  display: block;
  margin-bottom: 4px;
  color: #1a1a2e;
}

.history-item p {
  margin: 0 0 4px;
  color: #4a5568;
  font-size: 14px;
}

.history-item span {
  display: block;
  color: #6b7280;
  font-size: 13px;
}

.history-actions {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  flex-shrink: 0;
}

.page-error {
  padding: 12px 16px;
  border-radius: 12px;
  background: #fef2f2;
  border: 1px solid #fecaca;
  color: #991b1b;
  font-weight: 600;
  margin-bottom: 16px;
}

.page-info {
  padding: 10px 16px;
  border-radius: 12px;
  background: #eff6ff;
  border: 1px solid #bfdbfe;
  color: #1e40af;
  margin-bottom: 16px;
}

/* ===== 预览弹窗 ===== */
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
  border-radius: 24px;
  max-width: 860px;
  width: 92%;
  max-height: 90vh;
  overflow: hidden;
  box-shadow: 0 32px 80px rgba(0, 0, 0, 0.3);
  animation: modalSlideUp 0.3s ease;
}

@keyframes modalSlideUp {
  from { transform: translateY(30px) scale(0.95); opacity: 0; }
  to { transform: translateY(0) scale(1); opacity: 1; }
}

.modal-large {
  max-width: 860px;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 28px;
  border-bottom: 1px solid #eef0f3;
}

.modal-title {
  display: flex;
  align-items: center;
  gap: 12px;
}

.modal-title h2 {
  margin: 0;
  font-size: 20px;
  font-weight: 800;
  color: #1a1a2e;
}

.modal-close {
  width: 36px;
  height: 36px;
  border: none;
  border-radius: 50%;
  background: #f1f4f9;
  color: #6b7280;
  font-size: 18px;
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
}

.modal-close:hover {
  background: #e5e7eb;
  transform: rotate(90deg);
}

.modal-body {
  padding: 28px;
  max-height: calc(90vh - 80px);
  overflow-y: auto;
}

/* ===== 响应式 ===== */
@media (max-width: 1100px) {
  .agent-layout {
    grid-template-columns: minmax(0, 1fr);
  }

  .agent-nav {
    position: static;
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 4px;
  }

  .agent-nav,
  .workspace,
  .workspace-top,
  .trace-card,
  .history-card,
  .generation-panel,
  .panel-content,
  .resource-preview,
  .mindmap-wrapper {
    min-width: 0;
    max-width: 100%;
  }

  .nav-item {
    width: 100%;
    min-width: 0;
    box-sizing: border-box;
  }

  .nav-item strong,
  .nav-item em {
    overflow-wrap: anywhere;
    white-space: normal;
  }

  .video-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .doc-layout {
    grid-template-columns: 1fr;
  }

  .code-editor-wrap {
    grid-template-columns: 1fr;
  }

  .mindmap-container.horizontal {
    min-height: 700px;
  }

  .mindmap-branches-horizontal {
    padding-left: 160px;
  }

  .branch-group-horizontal {
    left: 140px;
  }

  .branch-group-horizontal:nth-child(1) { top: 30px; }
  .branch-group-horizontal:nth-child(2) { top: 95px; }
  .branch-group-horizontal:nth-child(3) { top: 160px; }
  .branch-group-horizontal:nth-child(4) { top: 225px; }
  .branch-group-horizontal:nth-child(5) { top: 290px; }
  .branch-group-horizontal:nth-child(6) { top: 355px; }
  .branch-group-horizontal:nth-child(7) { top: 420px; }
  .branch-group-horizontal:nth-child(8) { top: 485px; }
  .branch-group-horizontal:nth-child(9) { top: 550px; }

  .branch-main-horizontal {
    min-width: 60px;
    min-height: 38px;
    padding: 8px 12px;
    font-size: 13px;
  }

  .branch-label-horizontal {
    font-size: 13px;
  }

  .child-node-horizontal {
    font-size: 12px;
    padding: 4px 10px;
  }

  .center-node {
    padding: 18px 12px;
    min-height: 100px;
  }

  .center-title-vertical {
    font-size: 16px;
    letter-spacing: 4px;
  }
}

@media (max-width: 720px) {
  .agent-page {
    padding: 16px;
  }

  .section-head {
    padding: 32px 18px 20px;
  }

  .section-head h2 {
    font-size: 24px;
  }

  .workspace {
    padding: 16px;
  }

  .agent-nav {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .video-grid {
    grid-template-columns: 1fr;
  }

  .workspace-top {
    flex-direction: column;
    align-items: flex-start;
  }

  .progress-card {
    width: 100%;
    text-align: left;
  }

  .input-row {
    flex-direction: column;
  }

  .input-row button {
    height: 44px;
  }

  .btn-group {
    width: 100%;
    justify-content: flex-start;
  }

  .modal-content {
    width: 96%;
    border-radius: 18px;
  }

  .modal-header {
    padding: 16px 20px;
  }

  .modal-body {
    padding: 16px;
  }

  .mindmap-container.horizontal {
    min-height: 600px;
  }

  .mindmap-branches-horizontal {
    padding-left: 120px;
  }

  .branch-group-horizontal {
    left: 100px;
  }

  .branch-group-horizontal:nth-child(1) { top: 25px; }
  .branch-group-horizontal:nth-child(2) { top: 80px; }
  .branch-group-horizontal:nth-child(3) { top: 135px; }
  .branch-group-horizontal:nth-child(4) { top: 190px; }
  .branch-group-horizontal:nth-child(5) { top: 245px; }
  .branch-group-horizontal:nth-child(6) { top: 300px; }
  .branch-group-horizontal:nth-child(7) { top: 355px; }
  .branch-group-horizontal:nth-child(8) { top: 410px; }
  .branch-group-horizontal:nth-child(9) { top: 465px; }

  .branch-main-horizontal {
    min-width: 50px;
    min-height: 32px;
    padding: 6px 10px;
    font-size: 11px;
  }

  .branch-label-horizontal {
    font-size: 11px;
  }

  .child-node-horizontal {
    font-size: 10px;
    padding: 3px 8px;
  }

  .center-node {
    padding: 14px 10px;
    min-height: 80px;
    min-width: 40px;
  }

  .center-title-vertical {
    font-size: 13px;
    letter-spacing: 3px;
  }
}

/* ?????????????????? */

.hero-bg,
.hero-mask,
.star-canvas {
  display: none;
}

.section-head p,
.workspace-top p,
.section-title-row p,
.doc-card p,
.doc-card li,
.doc-preview p,
.reading-list p,
.quiz-card p,
.video-card p,
.analysis-box,
.mind-node small {
  line-height: 1.9;
  font-size: 15px;
  color: #111827;
}

.pulse-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: #111827;
  animation: pulse 1.8s infinite;
}

.danger-btn {
  color: #b42318;
  border-color: rgba(180, 35, 24, 0.28);
}

.danger-btn:hover {
  color: #912018;
  border-color: rgba(180, 35, 24, 0.5);
  background: #fff1f0;
}

.mind-lines {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
}

.mind-lines line {
  stroke: #d1d5db;
  stroke-width: 2;
  stroke-dasharray: 7 7;
}

.mind-center,
.mind-node {
  position: absolute;
  max-width: calc(100% - 36px);
  border-radius: 18px;
  padding: 13px 17px;
  font-weight: 800;
  box-shadow: 0 12px 28px rgba(0, 0, 0, 0.08);
  box-sizing: border-box;
}

.mind-center {
  left: 50%;
  top: 48%;
  transform: translate(-50%, -50%);
  background: #111827;
  color: #ffffff;
  font-size: 18px;
}

.mind-node {
  width: clamp(150px, 22%, 190px);
  background: #ffffff;
  color: #111827;
  border: 1px solid #e5e7eb;
  overflow-wrap: anywhere;
}

.mind-node strong,
.mind-node small {
  display: block;
}

.mind-node small {
  margin-top: 6px;
  font-size: 12px;
  line-height: 1.6;
}

.preview-badge {
  align-self: flex-start;
  padding: 3px 8px;
  border: 1px solid #a5f3fc;
  border-radius: 999px;
  background: #ecfeff;
  color: #155e75;
  font-size: 11px;
  font-weight: 800;
}

.ready-badge {
  align-self: flex-start;
  padding: 3px 8px;
  border: 1px solid #6ee7b7;
  border-radius: 999px;
  background: #d1fae5;
  color: #065f46;
  font-size: 11px;
  font-weight: 700;
}

.trace-card,
.history-card {
  margin-bottom: 20px;
  padding: 20px;
  border-radius: 18px;
  background: #ffffff;
  border: 1px solid #e5e7eb;
  box-shadow: var(--shadow-md);
}

.trace-item,
.history-item {
  padding: 14px;
  margin-top: 12px;
  border-radius: 16px;
  background: #f9fafb;
  border: 1px solid #e5e7eb;
}

.trace-item strong,
.history-item strong {
  display: block;
  margin-bottom: 6px;
  color: #111827;
}

.trace-item p,
.history-item p {
  margin: 0 0 6px;
  color: #374151;
  font-size: 14px;
}

.trace-item span,
.history-item span {
  display: block;
  color: #6b7280;
  font-size: 13px;
}

.trace-item em {
  display: inline-block;
  margin-top: 8px;
  font-style: normal;
  font-size: 12px;
  color: #111827;
  font-weight: 700;
}

@keyframes cursorBlink {
  0%, 50% { opacity: 1; }
  51%, 100% { opacity: 0; }
}

@keyframes pulse {
  0% { box-shadow: 0 0 0 0 rgba(0, 0, 0, 0.35); }
  70% { box-shadow: 0 0 0 12px rgba(0, 0, 0, 0); }
  100% { box-shadow: 0 0 0 0 rgba(0, 0, 0, 0); }
}

@media (max-width: 720px) {

  .mind-lines {
    display: none;
  }

  .mind-center,
  .mind-node {
    position: static;
    transform: none;
    width: auto;
    margin-bottom: 10px;
  }
}

/* Product-grade presentation overrides */
.markdown-body :deep(h1),
.markdown-body :deep(h2),
.markdown-body :deep(h3) { margin: 1.2em 0 0.55em; color: var(--text-primary); line-height: 1.35; }
.markdown-body :deep(h1) { font-size: 22px; }
.markdown-body :deep(h2) { font-size: 18px; }
.markdown-body :deep(h3) { font-size: 16px; }
.markdown-body :deep(p) { margin: 0.55em 0; color: #344054; line-height: 1.8; }
.markdown-body :deep(ul), .markdown-body :deep(ol) { margin: 0.7em 0; padding-left: 1.5em; }
.markdown-body :deep(li) { margin: 0.35em 0; color: #344054; }
.markdown-body :deep(code) { padding: 0.15em 0.4em; border-radius: 6px; background: #eef1f7; color: #6941c6; font-family: var(--font-mono); font-size: 0.9em; }
.markdown-body :deep(pre) { overflow-x: auto; padding: 16px; border-radius: 12px; background: #111827; color: #e5e7eb; }
.markdown-body :deep(pre code) { padding: 0; background: transparent; color: inherit; }
.markdown-body :deep(table) { width: 100%; border-collapse: collapse; }
.markdown-body :deep(th), .markdown-body :deep(td) { padding: 10px 12px; border: 1px solid var(--border-default); text-align: left; }

.short-answer-input {
  width: 100%;
  margin-top: 10px;
  padding: 14px 16px;
  resize: vertical;
  border: 1px solid var(--border-default);
  border-radius: 12px;
  background: #fff;
  color: var(--text-primary);
  line-height: 1.7;
}

.review { padding: 4px 12px; border-radius: 999px; background: #fff4e5; color: #a15c07; font-size: 12px; font-weight: 750; }
.review-hint { color: var(--text-secondary); font-size: 13px; font-weight: 650; }

.agent-layout { grid-template-columns: 232px minmax(0, 1fr); gap: 20px; }
.section-head { border: 0; background: linear-gradient(135deg, #171b2e 0%, #292654 56%, #4338ca 100%); box-shadow: var(--shadow-lg); }
.section-head h2, .section-head .eyebrow { color: #fff; }
.section-head .section-desc { color: rgba(255,255,255,.72); }
.page-back-link { border-color: rgba(255,255,255,.15); background: rgba(255,255,255,.1); color: #fff; }
.page-back-link:hover { background: rgba(255,255,255,.18); }
.agent-nav, .workspace { border-color: var(--border-default); box-shadow: var(--shadow-md); }
.agent-nav { border-radius: var(--radius-xl); }
.nav-item.active { background: linear-gradient(135deg, var(--accent-primary), #5046dc); box-shadow: 0 10px 24px rgba(99,91,255,.22); }
.workspace { border-radius: var(--radius-xl); }
.generation-panel { background: #f7f8fc; border-color: var(--border-default); }
.resource-preview { border-radius: 18px; box-shadow: 0 8px 28px rgba(31,42,68,.05); }
.primary-btn, .input-row button { background: var(--accent-primary); }
.primary-btn:hover, .input-row button:hover:not(:disabled) { background: var(--accent-hover); box-shadow: 0 8px 18px rgba(99,91,255,.2); }
.chat-item.user p { background: var(--accent-primary); }
.chat-item.ai .ai-avatar { background: var(--accent-primary); }

.mindmap-wrapper { padding: 24px; overflow: visible; background: linear-gradient(145deg, #fafaff, #f5f7ff); }
.mindmap-container.horizontal { display: grid; grid-template-columns: 160px minmax(0,1fr); gap: 28px; min-height: auto; padding: 8px; align-items: center; }
.mindmap-center { position: static; transform: none; }
.center-node { min-height: 150px; background: linear-gradient(145deg, #635bff, #4941c8); box-shadow: 0 16px 36px rgba(99,91,255,.25); }
.mindmap-branches-horizontal, .preview-mode .mindmap-branches-horizontal { display: grid; grid-template-columns: repeat(2, minmax(0,1fr)); gap: 12px; width: auto; padding-left: 0; }
.branch-group-horizontal, .preview-mode .branch-group-horizontal,
.branch-group-horizontal:nth-child(n) { position: static; display: block; min-width: 0; }
.branch-main-horizontal { justify-content: flex-start; min-height: 48px; border: 1px solid #d9d6ff; background: #fff; color: #302c73; }
.branch-children-horizontal { margin: 8px 0 0; gap: 6px; }
.child-node-horizontal { white-space: normal; border-color: #e7e5ff; background: #f8f7ff; color: #4a4678; }

@media (max-width: 760px) {
  .mindmap-container.horizontal { grid-template-columns: 1fr; }
  .center-node { min-height: 84px; }
  .center-title-vertical { writing-mode: horizontal-tb; letter-spacing: .04em; }
  .mindmap-branches-horizontal, .preview-mode .mindmap-branches-horizontal { grid-template-columns: 1fr; }
}

/* 真实问答结构：光标不能继承头像方块样式。 */
.chat-cursor {
  display: inline-block;
  width: 2px;
  height: 1.1em;
  margin-left: 4px;
  border-radius: 1px;
  background: #6366f1;
  vertical-align: -0.12em;
  animation: cursorBlink 0.9s steps(1) infinite;
}

/* 动态思维导图：使用流式网格，避免固定坐标造成重叠或超出画布。 */
.mindmap-wrapper {
  padding: 24px;
  overflow-x: auto;
  background: linear-gradient(145deg, #f8faff, #f8fafc);
  border-color: #dbe3f0;
}

.mindmap-container.horizontal {
  display: grid;
  grid-template-columns: minmax(150px, 0.28fr) minmax(520px, 1fr);
  align-items: center;
  gap: 44px;
  min-width: 760px;
  min-height: 420px;
  padding: 28px;
}

.mindmap-center {
  position: relative;
  left: auto;
  top: auto;
  transform: none;
}

.center-node {
  min-width: 132px;
  min-height: 132px;
  padding: 22px;
  border-radius: 24px;
  background: linear-gradient(145deg, #4f46e5, #6366f1);
  box-shadow: 0 18px 40px rgba(79, 70, 229, 0.24);
}

.center-title-vertical {
  max-width: 160px;
  color: #ffffff;
  writing-mode: horizontal-tb;
  text-orientation: mixed;
  letter-spacing: 0.04em;
  line-height: 1.5;
  text-align: center;
  overflow-wrap: anywhere;
}

.mindmap-branches-horizontal,
.preview-mode .mindmap-branches-horizontal {
  display: grid;
  gap: 14px;
  width: 100%;
  padding-left: 0;
}

.branch-group-horizontal,
.preview-mode .branch-group-horizontal,
.branch-group-horizontal:nth-child(n) {
  position: relative;
  left: auto;
  top: auto;
  display: grid;
  grid-template-columns: minmax(118px, 0.32fr) minmax(260px, 1fr);
  align-items: center;
  gap: 18px;
}

.branch-group-horizontal::before {
  content: '';
  position: absolute;
  left: -44px;
  top: 50%;
  width: 44px;
  height: 1px;
  background: linear-gradient(90deg, #a5b4fc, #6366f1);
}

.branch-main-horizontal {
  min-width: 0;
  min-height: 48px;
  padding: 10px 14px;
  border-color: #818cf8;
  color: #3730a3;
  background: #eef2ff;
}

.branch-label-horizontal {
  color: inherit;
  white-space: normal;
  text-align: center;
  overflow-wrap: anywhere;
}

.branch-children-horizontal {
  margin-left: 0;
}

.child-node-horizontal {
  color: #334155;
  white-space: normal;
  overflow-wrap: anywhere;
}

@media (max-width: 820px) {
  .mindmap-container.horizontal {
    grid-template-columns: 1fr;
    min-width: 560px;
    gap: 24px;
  }

  .mindmap-center {
    justify-self: center;
  }

  .branch-group-horizontal::before {
    display: none;
  }
}
</style>
