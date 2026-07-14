<template>
  <section class="agent-page">
    <div class="agent-shell">
      <header class="section-head hero-head">
        <div class="hero-bg"></div>
        <div class="hero-mask"></div>
        <button class="ui-back-link page-back-link" type="button" @click="goHome">
          ← 返回首页
        </button>
        <p class="eyebrow">MULTI-AGENT RESOURCE GENERATION</p>
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
                    <button class="ghost-btn" @click="activeKey = 'doc'">查看详解文档</button>
                  </div>

                  <div v-if="isLoadingMindmap" class="empty-state">加载中...</div>
                  <div v-else-if="!mindNodes.length" class="empty-state" @click="activeKey = 'qa'">待生成，请先完成问答</div>
                  <div v-else class="mindmap">
                    <svg class="mind-lines" viewBox="0 0 900 430" preserveAspectRatio="none">
                      <line x1="450" y1="210" x2="155" y2="70" />
                      <line x1="450" y1="210" x2="735" y2="80" />
                      <line x1="450" y1="210" x2="140" y2="340" />
                      <line x1="450" y1="210" x2="750" y2="335" />
                      <line x1="450" y1="210" x2="450" y2="382" />
                    </svg>
                    <div class="mind-center">{{ mindmapTitle }}</div>
                    <div
                      v-for="(node, idx) in mindNodes"
                      :key="idx"
                      class="mind-node"
                      :style="{ left: node.x || (150 + idx * 180) + 'px', top: node.y || (70 + (idx % 4) * 90) + 'px' }"
                    >
                      <strong>{{ node.title }}</strong>
                      <small>{{ node.desc }}</small>
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

                    <article class="doc-card">
                      <h5>{{ activeDoc.title }}</h5>
                      <p>{{ activeDoc.content }}</p>
                      <ul>
                        <li v-for="point in activeDoc.points" :key="point">{{ point }}</li>
                      </ul>
                    </article>
                  </div>

                  <div v-if="showDocPreview && documentSections.length" class="doc-preview">
                    <h5>完整文档预览</h5>
                    <section v-for="section in documentSections" :key="section.title">
                      <strong>{{ section.title }}</strong>
                      <p>{{ section.content }}</p>
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
                      <iframe
                        v-if="video.animationHtml"
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
                      <span v-if="video.mediaStatus === 'preview'" class="preview-badge">动画预览</span>
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
                        <span v-if="quizSubmitted" :class="isCorrect(q) ? 'right' : 'wrong'">
                          {{ isCorrect(q) ? '正确' : '错误' }}
                        </span>
                      </div>
                      <p>{{ q.question }}</p>
                      <label v-for="option in q.options" :key="option.value" class="option-row">
                        <input v-model="answers[q.id]" type="radio" :name="q.id" :value="option.value" :disabled="quizSubmitted" />
                        <span>{{ option.value }}. {{ option.text }}</span>
                      </label>
                      <div v-if="quizSubmitted" class="analysis-box">
                        正确答案：{{ q.answer }}。{{ q.analysis }}
                      </div>
                    </article>
                  </div>

                  <div v-if="quizQuestions.length" class="quiz-footer">
                    <button class="primary-btn" @click="submitQuiz">提交批改</button>
                    <strong v-if="quizSubmitted">得分：{{ quizScore }} / {{ quizQuestions.length }}</strong>
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

const router = useRouter()

const POLL_INTERVAL_MS = 2000
const POLL_MAX_MS = 60000
const DEFAULT_TASK_TYPES = ['lecture', 'mind_map', 'exercise', 'video', 'code', 'dataset', 'roadmap']

const activeKey = ref('qa')
const inputText = ref('')
const resourceGenerated = ref(false)
const showDocPreview = ref(true)
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
  { key: 'qa', title: '智能问答', desc: '需求采集', longDesc: '通过问答收集学习需求，AI自动生成课程资源。' },
  { key: 'mindmap', title: '思维导图', desc: '知识结构', longDesc: '根据学习需求生成知识结构导图。' },
  { key: 'doc', title: '详解文档', desc: '预览下载', longDesc: '生成支持预览和下载的课程详解文档。' },
  { key: 'video', title: '视频资源', desc: '分页学习', longDesc: '推荐的视频学习资源，支持分页切换。' },
  { key: 'exercise', title: '在线习题', desc: '答题批改', longDesc: '生成练习题，支持在线作答和自动批改。' },
  { key: 'reading', title: '拓展阅读', desc: '延伸学习', longDesc: '推荐的拓展阅读材料。' },
  { key: 'code', title: '代码实操', desc: '可编辑运行', longDesc: '多语言代码编辑器，可编辑并运行代码。' },
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
const documentSections = reactive([])
const activeDoc = computed(() => documentSections[activeDocIndex.value] || { title: '', content: '', points: [] })

const videos = reactive([])
const totalVideoPages = computed(() => Math.max(1, Math.ceil(videos.length / pageSize)))
const pagedVideos = computed(() => videos.slice((videoPage.value - 1) * pageSize, videoPage.value * pageSize))

const quizQuestions = reactive([])
const quizScore = computed(() => quizQuestions.reduce((sum, q) => sum + (answers[q.id] === q.answer ? 1 : 0), 0))

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
    return [
      { value: 'A', text: '选项A' },
      { value: 'B', text: '选项B' },
      { value: 'C', text: '选项C' },
      { value: 'D', text: '选项D' },
    ]
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
    return [{ title: '讲解文档', content: lecture, points: [] }]
  }
  const content = lecture.content || ''
  const sections = content
    .split(/\n(?=##\s)/)
    .map(part => part.trim())
    .filter(Boolean)
    .map((part, index) => {
      const lines = part.split('\n')
      const title = lines[0].replace(/^#+\s*/, '').trim() || `章节${index + 1}`
      const body = lines.slice(1).join('\n').trim()
      return {
        title,
        content: body || part,
        points: [],
      }
    })
  if (sections.length) return sections
  return [{
    title: lecture.title || '讲解文档',
    content,
    points: pickList(lecture.references).map(item => item.title || item.name || '').filter(Boolean),
  }]
}

function buildMindNodes(mindMap, roadmap, topic) {
  const roadmapNodes = pickList(roadmap, ['nodes', 'items', 'list'])
  if (roadmapNodes.length) {
    return roadmapNodes.map((node, index) => ({
      title: node.title || node.name || `节点${index + 1}`,
      desc: node.desc || node.description || '',
      x: `${120 + (index % 3) * 200}px`,
      y: `${60 + Math.floor(index / 3) * 100}px`,
    }))
  }
  if (mindMap?.content) {
    const lines = String(mindMap.content).split('\n').filter(line => line.trim().startsWith('-'))
    if (lines.length) {
      return lines.slice(0, 8).map((line, index) => ({
        title: line.replace(/^-\s*/, '').trim(),
        desc: '',
        x: `${120 + (index % 3) * 200}px`,
        y: `${60 + Math.floor(index / 3) * 100}px`,
      }))
    }
  }
  if (mindMap?.title) mindmapTitle.value = mindMap.title
  return [{ title: topic || '知识结构', desc: '暂无详细节点，已降级为树状列表。', x: '180px', y: '120px' }]
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
  return questions.map((question, index) => ({
    id: question.id || index + 1,
    title: question.title || `习题${index + 1}`,
    question: question.question || question.content || '',
    options: normalizeOptions(question.options),
    answer: question.answer || 'A',
    analysis: question.analysis || question.explanation || '解析内容',
  }))
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
    url: video.url || '',
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
  return answers[question.id] === question.answer
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
  if (animationId) cancelAnimationFrame(animationId)
  if (resizeHandler) window.removeEventListener('resize', resizeHandler)
})
</script>

<style scoped>
/* 样式保持不变，与原文件相同 */
.agent-page {
  min-height: 100vh;
  padding: 32px;
  background: var(--bg-page);
  color: #111827;
  box-sizing: border-box;
  scroll-behavior: smooth;
}

.agent-shell {
  width: 100%;
  max-width: 1380px;
  margin: 0 auto;
}

.section-head,
.workspace,
.generation-panel,
.resource-preview,
.doc-card,
.doc-preview,
.video-card,
.reading-list article,
.quiz-card,
.progress-card {
  background: #ffffff;
  border: 1px solid #e5e7eb;
  box-shadow: var(--shadow-md);
}

.section-head {
  position: relative;
  overflow: hidden;
  border-radius: 18px;
  padding: 54px 34px 24px 34px;
  margin: 0 0 24px;
  text-align: center;
}

.hero-head {
  width: 100%;
  box-sizing: border-box;
}

.hero-bg,
.hero-mask,
.star-canvas {
  display: none;
}

.page-back-link {
  position: absolute;
  left: 24px;
  top: 22px;
  margin: 0 0 16px;
}

.eyebrow,
.workspace-label {
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
  font-size: 30px;
  line-height: 1.25;
  color: #111827;
}

.section-desc {
  max-width: 760px;
  margin-left: auto;
  margin-right: auto;
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
  padding: 18px;
  box-shadow: var(--shadow-md);
}

.nav-item {
  width: 100%;
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 14px;
  margin: 8px 0;
  border: none;
  border-radius: 14px;
  background: transparent;
  color: #111827;
  text-align: left;
  cursor: pointer;
  transition: all 0.2s ease;
}

.nav-item:hover,
.nav-item.active {
  background: #f1f5f9;
  transform: translateX(4px);
}

.nav-icon {
  width: 34px;
  height: 34px;
  flex-shrink: 0;
  display: grid;
  place-items: center;
  border-radius: 12px;
  background: #f3f4f6;
  border: 1px solid #e5e7eb;
  font-size: 16px;
}

.nav-item strong,
.nav-item em {
  display: block;
}

.nav-item strong {
  font-size: 14px;
  font-weight: 700;
  color: #111827;
}

.nav-item em {
  margin-top: 3px;
  font-style: normal;
  font-size: 12px;
  color: #4b5563;
}

.workspace {
  border-radius: 18px;
  padding: 34px;
  overflow: hidden;
}

.workspace-top {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 18px;
  margin-bottom: 24px;
}

.workspace-top h3 {
  margin: 0 0 10px;
  font-size: 25px;
  line-height: 1.35;
  color: #111827;
}

.progress-card {
  min-width: 148px;
  padding: 16px;
  border-radius: 18px;
  text-align: right;
}

.progress-card span {
  display: block;
  margin-bottom: 8px;
  color: #4b5563;
  font-size: 13px;
  font-weight: 600;
}

.progress-card strong {
  font-size: 34px;
  line-height: 1;
  color: #111827;
}

.generation-panel {
  position: relative;
  border-radius: 18px;
  padding: 22px;
  overflow: hidden;
}

.panel-content {
  position: relative;
  z-index: 1;
}

.typing-head {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 18px;
  color: #111827;
  font-weight: 700;
}

.pulse-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: #111827;
  animation: pulse 1.8s infinite;
}

.resource-preview {
  border-radius: 18px;
  padding: 24px;
}

.section-title-row {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 18px;
}

.resource-preview h4 {
  margin: 0 0 8px;
  font-size: 22px;
  font-weight: 800;
  color: #111827;
}

.primary-btn,
.ghost-btn,
.input-row button,
.pagination button {
  border-radius: 14px;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.2s ease;
}

.primary-btn,
.input-row button {
  border: none;
  background: #111827;
  color: #ffffff;
}

.primary-btn,
.ghost-btn {
  padding: 11px 16px;
  white-space: nowrap;
}

.primary-btn:hover,
.input-row button:hover {
  background: #1f2937;
  transform: translateY(-2px);
  box-shadow: 0 12px 24px rgba(0, 0, 0, 0.15);
}

.ghost-btn {
  border: 1px solid #e5e7eb;
  background: #ffffff;
  color: #111827;
}

.ghost-btn:hover {
  background: #f1f5f9;
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

.btn-group {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
  justify-content: flex-end;
}

.chat-box {
  display: flex;
  flex-direction: column;
  gap: 12px;
  max-height: 245px;
  overflow-y: auto;
  margin-bottom: 14px;
  padding-right: 4px;
}

.chat-item {
  display: flex;
  gap: 10px;
}

.chat-item.user {
  flex-direction: row-reverse;
}

.chat-item span {
  width: 34px;
  height: 34px;
  border-radius: 12px;
  background: #111827;
  color: #ffffff;
  display: grid;
  place-items: center;
  font-size: 12px;
  font-weight: 800;
}

.chat-item p {
  max-width: 76%;
  margin: 0;
  padding: 11px 13px;
  border-radius: 15px;
  background: #f9fafb;
  border: 1px solid #e5e7eb;
}

.chat-item.user p {
  background: #111827;
  color: #ffffff;
  border-color: #111827;
}

.prompt-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-bottom: 12px;
}

.prompt-chips button,
.page-info,
.reading-list article span,
.right,
.wrong {
  border-radius: 999px;
  font-size: 13px;
  font-weight: 600;
}

.prompt-chips button {
  border: 1px solid #e5e7eb;
  padding: 7px 13px;
  background: #f3f4f6;
  color: #111827;
  cursor: pointer;
}

.prompt-chips button:hover {
  background: #f1f5f9;
}

.input-row {
  display: flex;
  gap: 10px;
}

.input-row input {
  flex: 1;
  height: 46px;
  border: 1px solid #e5e7eb;
  outline: none;
  border-radius: 14px;
  padding: 0 14px;
  color: #111827;
}

.input-row input:focus,
.code-editor:focus {
  border-color: #111827;
}

.input-row button {
  border: none;
  padding: 0 18px;
}

.input-row button:disabled {
  opacity: 0.55;
  cursor: not-allowed;
  transform: none;
  box-shadow: none;
}

.empty-state {
  margin-top: 14px;
  padding: 28px;
  text-align: center;
  font-weight: 700;
  cursor: pointer;
  user-select: none;
  border-radius: 16px;
  background: #f9fafb;
  border: 1px solid #e5e7eb;
  color: #111827;
}

.generated-tip,
.analysis-box {
  margin-top: 14px;
  padding: 12px 14px;
  border-radius: 14px;
  background: #f9fafb;
  border: 1px solid #e5e7eb;
  color: #111827;
  font-size: 13px;
  font-weight: 600;
}

.mindmap {
  position: relative;
  width: 100%;
  height: 430px;
  padding: 18px;
  border-radius: 18px;
  background: #f9fafb;
  border: 1px solid #e5e7eb;
  overflow: hidden;
  box-sizing: border-box;
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

.doc-layout {
  display: grid;
  grid-template-columns: 240px 1fr;
  gap: 14px;
}

.doc-toc {
  display: grid;
  gap: 10px;
}

.doc-toc button {
  border: 1px solid #e5e7eb;
  border-radius: 14px;
  background: #ffffff;
  padding: 12px;
  cursor: pointer;
  text-align: left;
  color: #111827;
  font-weight: 700;
  transition: all 0.2s ease;
}

.doc-toc button:hover,
.doc-toc button.active {
  background: #f1f5f9;
}

.doc-toc span {
  display: block;
  margin-bottom: 4px;
  color: #9ca3af;
}

.doc-card,
.doc-preview,
.video-card,
.reading-list article,
.quiz-card {
  padding: 16px;
  border-radius: 18px;
}

.doc-card h5,
.doc-preview h5 {
  margin: 0 0 10px;
  font-size: 20px;
  color: #111827;
}

.doc-preview {
  margin-top: 14px;
  max-height: 280px;
  overflow-y: auto;
}

.doc-preview section {
  padding: 12px 0;
  border-bottom: 1px solid #e5e7eb;
}

.video-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 14px;
}

.video-card {
  min-height: 240px;
  display: flex;
  flex-direction: column;
}

.animation-preview {
  width: 100%;
  height: 220px;
  margin-bottom: 12px;
  border: 0;
  border-radius: 15px;
  background: #07111f;
}

.video-thumb {
  position: relative;
  height: 112px;
  border-radius: 15px;
  background: #111827;
  display: grid;
  place-items: center;
  color: #ffffff;
  margin-bottom: 12px;
}

.video-thumb span {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.14);
  display: grid;
  place-items: center;
}

.video-thumb em {
  position: absolute;
  right: 10px;
  bottom: 8px;
  font-size: 11px;
  font-style: normal;
}

.video-card strong,
.reading-list strong,
.quiz-head strong {
  color: #111827;
  font-size: 15px;
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

.video-meta {
  margin-top: auto;
  display: flex;
  justify-content: space-between;
  color: #111827;
  font-size: 12px;
  font-weight: 700;
}

.page-info {
  padding: 8px 12px;
  background: #f3f4f6;
  border: 1px solid #e5e7eb;
  color: #111827;
}

.page-error {
  margin: 0 0 16px;
  padding: 10px 14px;
  border-radius: 14px;
  background: #fef2f2;
  border: 1px solid #fecaca;
  color: #991b1b;
  font-size: 14px;
  font-weight: 600;
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

.history-item {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  align-items: flex-start;
}

.history-item.active {
  border-color: #111827;
}

.history-actions {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.video-link {
  display: inline-block;
  margin-top: 10px;
  color: #111827;
  font-size: 13px;
  font-weight: 700;
  text-decoration: underline;
}

.pagination {
  display: flex;
  justify-content: center;
  gap: 8px;
  margin-top: 18px;
}

.pagination button {
  min-width: 36px;
  border: 1px solid #e5e7eb;
  background: #ffffff;
  color: #111827;
  padding: 8px 10px;
}

.pagination button.active,
.pagination button:hover:not(:disabled) {
  background: #111827;
  color: #ffffff;
}

.pagination button:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}

.quiz-list,
.reading-list {
  display: grid;
  gap: 14px;
}

.quiz-head {
  display: flex;
  justify-content: space-between;
  gap: 12px;
}

.right,
.wrong {
  padding: 4px 9px;
  border: 1px solid #e5e7eb;
  background: #f3f4f6;
  color: #111827;
}

.option-row {
  display: flex;
  gap: 8px;
  align-items: center;
  margin: 8px 0;
  padding: 9px 10px;
  border-radius: 12px;
  background: #f9fafb;
  border: 1px solid #e5e7eb;
  cursor: pointer;
  color: #111827;
  font-size: 13px;
}

.quiz-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 16px;
}

.reading-list article span {
  display: inline-block;
  margin-bottom: 8px;
  padding: 4px 9px;
  background: #f3f4f6;
  border: 1px solid #e5e7eb;
  color: #111827;
}

.language-select {
  height: 42px;
  min-width: 132px;
  padding: 0 38px 0 14px;
  border: 1px solid #e5e7eb;
  border-radius: 14px;
  background: #ffffff;
  color: #111827;
  font-size: 14px;
  font-weight: 700;
  outline: none;
  cursor: pointer;
}

.language-select:focus {
  border-color: #111827;
}

.code-editor-wrap {
  display: grid;
  grid-template-columns: 1.35fr 0.65fr;
  gap: 14px;
}

.editor-panel,
.code-output {
  overflow: hidden;
  border-radius: 18px;
  background: #111827;
  color: #f9fafb;
  border: 1px solid #111827;
  box-shadow: 0 14px 30px rgba(17, 24, 39, 0.12);
}

.editor-toolbar {
  height: 44px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 16px;
  background: #0b1220;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
  font-size: 13px;
  font-weight: 800;
}

.editor-toolbar em {
  font-style: normal;
  color: #9ca3af;
  font-size: 12px;
}

.editor-body {
  display: grid;
  grid-template-columns: 52px 1fr;
  min-height: 430px;
}

.line-numbers {
  margin: 0;
  padding: 18px 12px;
  background: #0b1220;
  color: #6b7280;
  text-align: right;
  user-select: none;
  font-family: Consolas, Monaco, monospace;
  font-size: 13px;
  line-height: 1.75;
  white-space: pre;
}

.code-editor {
  width: 100%;
  min-height: 430px;
  padding: 18px;
  resize: vertical;
  border: none;
  outline: none;
  background: #111827;
  color: #f9fafb;
  font-family: Consolas, Monaco, monospace;
  font-size: 13px;
  line-height: 1.75;
  box-sizing: border-box;
}

.code-editor:focus {
  border-color: transparent;
}

.code-output {
  padding: 18px;
  font-family: Consolas, Monaco, monospace;
  font-size: 13px;
  line-height: 1.75;
}

.code-output strong {
  display: block;
  margin-bottom: 12px;
  color: #ffffff;
}

.code-output pre {
  white-space: pre-wrap;
  line-height: 1.7;
  margin: 0;
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

@media (max-width: 1100px) {
  .agent-layout,
  .doc-layout,
  .code-editor-wrap {
    grid-template-columns: 1fr;
  }

  .agent-nav {
    position: static;
    display: grid;
    grid-template-columns: repeat(2, 1fr);
  }

  .video-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 720px) {
  .agent-page {
    padding: 18px;
  }

  .section-head,
  .workspace {
    padding: 24px;
    border-radius: 18px;
  }

  .section-head h2 {
    font-size: 28px;
  }

  .agent-nav,
  .video-grid {
    grid-template-columns: 1fr;
  }

  .workspace-top,
  .section-title-row,
  .quiz-footer {
    flex-direction: column;
    align-items: flex-start;
  }

  .progress-card {
    width: 100%;
    box-sizing: border-box;
    text-align: left;
  }

  .input-row {
    flex-direction: column;
  }

  .input-row button {
    height: 44px;
  }

  .mindmap {
    height: auto;
    padding: 16px;
    overflow: hidden;
  }

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
</style>
