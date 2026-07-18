<template>
  <section class="learning-path-page">
    <RouterLink class="ui-back-link page-back-link" to="/">
      ← 返回首页
    </RouterLink>

    <main class="path-content">
      <section class="hero-card">
        <div class="hero-badge">智能学习规划</div>
        <h1>个性化学习路径规划与资源推送</h1>
        <p class="description">
          系统动态读取学生学习画像，结合详细学习目标生成真实的个性化学习路线图，
          并支持历史路径恢复、节点进度跟踪与资源推荐。
        </p>
      </section>

      <p v-if="restoreMessage" class="info-text">{{ restoreMessage }}</p>

      <section class="history-card">
        <div class="panel-head">
          <div>
            <span>我的学习路径</span>
            <small>查看、恢复或删除历史路径</small>
          </div>
          <em>{{ pathHistory.length ? `${pathHistory.length} 条` : '暂无' }}</em>
        </div>

        <div v-if="historyLoading" class="pending-block">正在加载历史路径...</div>
        <div v-else-if="!pathHistory.length" class="pending-block">暂无历史路径，生成后将自动保存。</div>
        <div v-else class="history-list">
          <article
            v-for="item in pathHistory"
            :key="item.pathId"
            class="history-item"
            :class="{ active: String(pathResult.pathId) === String(item.pathId) }"
          >
            <div class="history-main">
              <strong>{{ item.title }}</strong>
              <p>{{ item.goal || '暂无学习目标' }}</p>
              <div class="history-meta">
                <span v-if="item.course">{{ item.course }}</span>
                <span>{{ item.progress }}%</span>
                <span>{{ item.statusLabel }}</span>
                <span v-if="item.createdAt">{{ formatDate(item.createdAt) }}</span>
              </div>
            </div>
            <div class="history-actions">
              <button
                class="ghost-button"
                type="button"
                :disabled="!!viewLoadingId || deleteLoadingId === item.pathId"
                @click="openPath(item.pathId)"
              >
                {{ viewLoadingId === String(item.pathId) ? '加载中' : '查看' }}
              </button>
              <button
                class="ghost-button danger"
                type="button"
                :disabled="!!viewLoadingId || pathLoading || deleteLoadingId === item.pathId"
                @click="confirmDeletePath(item)"
              >
                {{ deleteLoadingId === item.pathId ? '删除中...' : '删除' }}
              </button>
            </div>
          </article>
        </div>
        <p v-if="pathError" class="error-text history-error">{{ pathError }}</p>
      </section>

      <section class="main-grid">
        <aside class="profile-card">
          <div class="panel-head">
            <div>
              <span>学习画像输入</span>
              <small>动态更新画像</small>
            </div>
            <em>{{ profileLoaded ? '已获取' : '待获取' }}</em>
          </div>

          <div v-if="profileLoading" class="pending-block">正在获取学习画像...</div>
          <div v-else-if="profileError" class="error-block">{{ profileError }}</div>
          <div v-else-if="!profileLoaded" class="pending-block">暂无学习画像数据，请先完成画像构建。</div>

          <template v-else>
            <div class="profile-summary">
              <strong>{{ profileView.major || '未返回专业方向' }}</strong>
              <p>{{ profileView.summary || '后端暂未返回画像摘要。' }}</p>
            </div>

            <div class="profile-list">
              <div v-for="item in profileItems" :key="item.label">
                <span>{{ item.label }}</span>
                <strong>{{ item.value || '后端未返回' }}</strong>
              </div>
            </div>

            <div class="tag-list" v-if="profileView.preferences.length">
              <span v-for="item in profileView.preferences" :key="item">{{ item }}</span>
            </div>
          </template>

          <button class="ghost-button" type="button" :disabled="profileLoading" @click="loadProfile">
            重新获取画像
          </button>
        </aside>

        <section class="planner-card">
          <div class="panel-head">
            <div>
              <span>学习目标</span>
              <small>目标将与动态学习画像一起提交</small>
            </div>
            <em>{{ pathGenerated ? '已生成' : '待生成' }}</em>
          </div>

          <textarea
            v-model="learningGoal"
            placeholder="请输入详细学习目标，例如：我想在 8 周内掌握机器学习基础，并完成一个图像识别项目。"
          ></textarea>

          <div class="action-row">
            <button
              class="primary-button"
              type="button"
              :disabled="loading || !profileLoaded"
              @click="generatePath"
            >
              {{ loading ? '正在生成...' : '生成学习路线' }}
            </button>
            <button class="ghost-button" type="button" :disabled="loading || pathLoading" @click="resetPath">
              清空结果
            </button>
          </div>

          <p v-if="!profileLoaded" class="form-tip">需要先获取学习画像，才能生成个性化路线。</p>
          <p v-if="pathError" class="error-text">{{ pathError }}</p>
        </section>
      </section>

      <section ref="pathDetailSection" class="result-card">
        <p v-if="loadedPathHint" class="loaded-hint">{{ loadedPathHint }}</p>

        <div class="empty-state" v-if="!pathGenerated && !pathLoading">
          <div class="empty-icon">AI</div>
          <h2>等待生成或选择学习路径</h2>
          <p>可从上方历史列表打开已有路径，或填写目标后生成新路线。</p>
        </div>

        <div v-else-if="pathLoading" class="pending-block">正在加载学习路径...</div>

        <template v-else>
          <div class="result-head">
            <div>
              <span>STEP ROADMAP</span>
              <h2>{{ pathResult.title || '个性化学习路线图' }}</h2>
              <p>{{ pathResult.summary || '后端已返回学习路线结果。' }}</p>
            </div>
            <strong v-if="pathResult.duration">预计周期：{{ pathResult.duration }}</strong>
          </div>

          <section class="progress-panel">
            <div class="progress-stats">
              <strong>{{ progressData.progress }}%</strong>
              <span>{{ progressData.completedNodes }} / {{ progressData.totalNodes }} 节点已完成</span>
              <span v-if="progressData.currentNode">
                当前节点：{{ progressData.currentNode.title }}
              </span>
            </div>
            <div class="progress-bar">
              <div class="progress-fill" :style="{ width: `${progressData.progress}%` }"></div>
            </div>
          </section>

          <div class="roadmap-flow">
            <template v-for="(step, index) in learningSteps" :key="step.id || step.title || index">
              <article
                class="road-step"
                :class="{
                  active: activeStepIndex === index,
                  current: isCurrentNode(step),
                  completed: step.status === 'completed',
                }"
                @click="selectStep(index)"
              >
                <div class="step-index">{{ index + 1 }}</div>
                <span>{{ step.period || step.duration || `阶段${index + 1}` }}</span>
                <h3>{{ step.title || '未命名步骤' }}</h3>
                <p>{{ step.short || step.description || '后端暂未返回步骤说明。' }}</p>
                <em class="step-status">{{ step.statusLabel || getNodeStatusLabel(step.status) }}</em>
              </article>

              <div v-if="index < learningSteps.length - 1" class="step-arrow">
                <span>→</span>
              </div>
            </template>
          </div>

          <section v-if="activeStep" class="detail-panel">
            <div>
              <span>{{ activeStep.period || activeStep.duration || '当前阶段' }}</span>
              <h3>{{ activeStep.title || '未命名步骤' }}</h3>
              <p>{{ activeStep.description || activeStep.short || '后端暂未返回详细说明。' }}</p>
              <div class="node-actions">
                <button
                  v-if="activeStep.status === 'not_started'"
                  class="primary-button"
                  type="button"
                  :disabled="!!nodeActionLoading"
                  @click="startNode(activeStep)"
                >
                  {{ nodeActionLoading === activeStep.id ? '处理中...' : '开始学习' }}
                </button>
                <button
                  v-else-if="activeStep.status === 'in_progress'"
                  class="primary-button"
                  type="button"
                  :disabled="!!nodeActionLoading"
                  @click="completeNode(activeStep)"
                >
                  {{ nodeActionLoading === activeStep.id ? '处理中...' : '标记完成' }}
                </button>
                <button
                  v-else
                  class="ghost-button"
                  type="button"
                  disabled
                >
                  已完成
                </button>
              </div>
            </div>
            <div class="detail-tags" v-if="activeStep.tags?.length">
              <em v-for="tag in activeStep.tags" :key="tag">{{ tag }}</em>
            </div>
          </section>

          <section class="resource-section">
            <div class="section-head">
              <span>RESOURCE RECOMMENDATION</span>
              <h2>精准学习资源推送</h2>
              <p>优先展示生成时返回的资源，也可从资源中心加载更多。</p>
            </div>

            <div class="resource-actions" v-if="activeStep">
              <button
                class="ghost-button"
                type="button"
                :disabled="resourcesLoading"
                @click="loadMoreResources(activeStep)"
              >
                {{ resourcesLoading ? '加载中...' : '查看更多资源' }}
              </button>
            </div>

            <div v-if="resourcesLoading" class="pending-block">正在加载节点资源...</div>
            <div v-else-if="!displayResourceGroups.length" class="pending-block">暂无关联资源</div>
            <div v-else class="resource-grid">
              <article v-for="group in displayResourceGroups" :key="group.type" class="resource-group">
                <div class="resource-group-head">
                  <div>
                    <h3>{{ group.type }}</h3>
                    <span>{{ group.desc || '推荐资源' }}</span>
                  </div>
                </div>

                <div class="resource-list">
                  <button
                    v-for="item in group.items"
                    :key="item.id || item.title"
                    class="resource-item"
                    type="button"
                    @click="openLearningResource(item)"
                  >
                    <strong>{{ item.title || '未命名资源' }}</strong>
                    <span>{{ item.meta || item.description || item.source || '学习资源' }}</span>
                  </button>
                </div>
              </article>
            </div>
          </section>

          <section v-if="progressData.progress >= 100" class="feedback-panel">
            <div class="section-head">
              <span>PATH FEEDBACK</span>
              <h2>路径学习反馈</h2>
              <p>你已完成全部节点，欢迎对本次学习路径进行评价。</p>
            </div>

            <div v-if="feedbackSubmitted" class="info-text">感谢反馈，已提交成功。</div>
            <template v-else>
              <div class="feedback-rating">
                <span>评分</span>
                <button
                  v-for="n in 5"
                  :key="n"
                  type="button"
                  class="rating-star"
                  :class="{ active: feedbackRating >= n }"
                  :disabled="feedbackSubmitting"
                  @click="feedbackRating = n"
                >
                  {{ n }}
                </button>
              </div>
              <textarea
                v-model="feedbackComment"
                placeholder="可选：写下你对这条学习路径的建议或感受"
                :disabled="feedbackSubmitting"
              ></textarea>
              <button
                class="primary-button"
                type="button"
                :disabled="feedbackSubmitting || !feedbackRating"
                @click="submitFeedback"
              >
                {{ feedbackSubmitting ? '提交中...' : '提交反馈' }}
              </button>
            </template>
          </section>
        </template>
      </section>
    </main>
  </section>
</template>

<script setup>
import { computed, nextTick, onMounted, reactive, ref, watch } from 'vue'
import { RouterLink, useRouter } from 'vue-router'
import {
  getCurrentProfile,
  generateLearningPath,
  getUserPathList,
  getLearningPathDetail,
  getPathProgress,
  deleteLearningPath,
  updatePathProgress,
  getNodeResources,
  submitPathFeedback,
} from '@/api/path'

const router = useRouter()
import { normalizeProfileResult } from '@/utils/profile'
import {
  adaptPathResponse,
  adaptPathListResponse,
  adaptPathProgressResponse,
  normalizePathStatus,
} from '@/utils/path'
import { getCurrentPathId, setCurrentPathId, clearCurrentPathId } from '@/utils/pathSession'

const learningGoal = ref('')
const loading = ref(false)
const profileLoading = ref(false)
const profileLoaded = ref(false)
const pathGenerated = ref(false)
const pathError = ref('')
const profileError = ref('')
const activeStepIndex = ref(0)
const historyLoading = ref(false)
const pathLoading = ref(false)
const progressLoading = ref(false)
const nodeActionLoading = ref('')
const deleteLoadingId = ref('')
const resourcesLoading = ref(false)
const restoreMessage = ref('')
const loadedPathHint = ref('')
const viewLoadingId = ref('')
const pathDetailSection = ref(null)
const feedbackRating = ref(0)
const feedbackComment = ref('')
const feedbackSubmitting = ref(false)
const feedbackSubmitted = ref(false)

const pathHistory = ref([])
const progressData = reactive({
  pathId: '',
  totalNodes: 0,
  completedNodes: 0,
  progress: 0,
  currentNode: null,
})
const extraResources = ref([])

const profileData = reactive(emptyProfileData())
const pathResult = reactive(emptyPathResult())

const learningSteps = computed(() => pathResult.steps)
const resourceGroups = computed(() => pathResult.resources)

const activeStep = computed(() => learningSteps.value[activeStepIndex.value] || null)

const displayResourceGroups = computed(() => {
  const step = activeStep.value
  if (!step) return resourceGroups.value

  const embedded = step.stepResources?.length
    ? [
        {
          type: step.title || '节点资源',
          desc: step.short || step.description || '',
          items: step.stepResources.map((item, index) => ({
            id: item.id || `embedded-${index}`,
            title: item.title || item.name || '未命名资源',
            meta: item.type || item.resource_type || '',
            description: item.description || item.summary || '',
            url: item.url || item.link || item.detail_url || '',
          })),
        },
      ]
    : []

  if (extraResources.value.length) {
    return [
      ...embedded,
      {
        type: '资源中心推荐',
        desc: '根据节点关键词匹配',
        items: extraResources.value,
      },
    ]
  }

  if (embedded.length) return embedded
  return resourceGroups.value
})

const profileView = computed(() => ({
  major: profileData.major || '',
  stage: profileData.stage || profileData.learning_stage || '',
  foundation: profileData.knowledge_level || profileData.foundation || '',
  goal: profileData.goal?.analysis || profileData.goalText || '',
  cognition: profileData.cognition?.main || profileData.cognitive_style || '',
  summary: profileData.summary || profileData.feedback?.analysis || '',
  preferences: profileData.preferences || [],
}))

const profileItems = computed(() => [
  { label: '学习阶段', value: profileView.value.stage },
  { label: '知识基础', value: profileView.value.foundation },
  { label: '学习目标', value: profileView.value.goal },
  { label: '认知风格', value: profileView.value.cognition },
])

function emptyProfileData() {
  return normalizeProfileResult({ profile: {}, dashboard: {} })
}

function emptyPathResult() {
  return {
    title: '',
    summary: '',
    duration: '',
    steps: [],
    resources: [],
    pathId: '',
  }
}

function emptyProgressData() {
  return {
    pathId: '',
    totalNodes: 0,
    completedNodes: 0,
    progress: 0,
    currentNode: null,
  }
}

function applyProfileData(nextData) {
  Object.assign(profileData, emptyProfileData(), nextData)
}

function applyPathResult(nextData) {
  Object.assign(pathResult, emptyPathResult(), nextData)
  activeStepIndex.value = 0
  pathGenerated.value = pathResult.steps.length > 0
  extraResources.value = []
  feedbackSubmitted.value = false
  feedbackRating.value = 0
  feedbackComment.value = ''
}

function applyProgressData(nextData) {
  Object.assign(progressData, emptyProgressData(), nextData)
}

function formatDate(value) {
  if (!value) return ''
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  })
}

function getNodeStatusLabel(status) {
  return normalizePathStatus(status).label
}

function isCurrentNode(step) {
  if (!progressData.currentNode || !step) return false
  return String(progressData.currentNode.id) === String(step.id)
}

function isPathNotFoundError(error) {
  const message = error?.message || ''
  return message.includes('404') || message.includes('不存在') || message.includes('not found')
}

async function loadProfile() {
  profileLoading.value = true
  profileError.value = ''
  profileLoaded.value = false

  try {
    const result = await getCurrentProfile()
    applyProfileData(normalizeProfileResult(result))
    profileLoaded.value = true
  } catch (error) {
    profileError.value = `学习画像获取失败：${error.message}`
  } finally {
    profileLoading.value = false
  }
}

async function loadPathHistory() {
  historyLoading.value = true
  try {
    const result = await getUserPathList()
    const adapted = adaptPathListResponse(result)
    pathHistory.value = adapted.items
  } catch (error) {
    pathError.value = `历史路径加载失败：${error.message}`
  } finally {
    historyLoading.value = false
  }
}

async function loadPathProgress(pathId) {
  progressLoading.value = true
  try {
    const result = await getPathProgress({ pathId })
    applyProgressData(adaptPathProgressResponse(result))
    syncStepIndexWithCurrentNode()
  } catch (error) {
    if (isPathNotFoundError(error)) {
      await handlePathNotFound()
      return
    }
    pathError.value = `路径进度加载失败：${error.message}`
  } finally {
    progressLoading.value = false
  }
}

function syncStepIndexWithCurrentNode() {
  if (!progressData.currentNode) return
  const index = learningSteps.value.findIndex(
    (step) => String(step.id) === String(progressData.currentNode.id),
  )
  if (index >= 0) activeStepIndex.value = index
}

async function loadPathById(pathId, options = {}) {
  const { silent = false } = options
  if (!pathId) return false

  if (!silent) pathLoading.value = true
  pathError.value = ''
  restoreMessage.value = ''

  try {
    const detailResult = await getLearningPathDetail({ pathId })
    applyPathResult(adaptPathResponse(detailResult))
    setCurrentPathId(pathId)
    await loadPathProgress(pathId)
    syncStatusesFromProgress()
    syncStepIndexWithCurrentNode()
    return true
  } catch (error) {
    if (isPathNotFoundError(error)) {
      await handlePathNotFound()
      return false
    }
    pathError.value = `路径加载失败：${error.message}`
    return false
  } finally {
    if (!silent) pathLoading.value = false
  }
}

async function refreshPathState() {
  if (!pathResult.pathId) return
  const currentId = learningSteps.value[activeStepIndex.value]?.id
  const detailResult = await getLearningPathDetail({ pathId: pathResult.pathId })
  applyPathResult(adaptPathResponse(detailResult))
  if (currentId) {
    const index = learningSteps.value.findIndex((step) => String(step.id) === String(currentId))
    if (index >= 0) activeStepIndex.value = index
  }
  await loadPathProgress(pathResult.pathId)
  syncStatusesFromProgress()
  syncStepIndexWithCurrentNode()
}

function syncStatusesFromProgress() {
  // Detail already carries authoritative node.status; ensure labels are present.
  pathResult.steps = pathResult.steps.map((step) => ({
    ...step,
    statusLabel: getNodeStatusLabel(step.status),
  }))
}

async function handlePathNotFound() {
  clearCurrentPathId()
  pathGenerated.value = false
  Object.assign(pathResult, emptyPathResult())
  applyProgressData(emptyProgressData())
  restoreMessage.value = '当前路径不存在或已删除，已为你刷新历史列表。'
  await loadPathHistory()
}

async function restoreCurrentPath() {
  const storedId = getCurrentPathId()
  if (storedId) {
    const ok = await loadPathById(storedId)
    if (ok) return
  }

  if (pathHistory.value.length) {
    const latestActive = pathHistory.value.find((item) => item.status === 'active') || pathHistory.value[0]
    if (latestActive?.pathId) {
      await loadPathById(latestActive.pathId)
    }
  }
}

async function scrollToPathDetail() {
  await nextTick()
  pathDetailSection.value?.scrollIntoView({
    behavior: 'smooth',
    block: 'start',
  })
}

async function openPath(pathId) {
  if (viewLoadingId.value) return

  const normalizedId = String(pathId)
  const isSamePath = String(pathResult.pathId) === normalizedId && pathGenerated.value

  viewLoadingId.value = normalizedId
  pathError.value = ''
  loadedPathHint.value = ''

  try {
    if (isSamePath) {
      loadedPathHint.value = `已加载：${pathResult.title || '当前路径'}`
      await scrollToPathDetail()
      return
    }

    const ok = await loadPathById(pathId)
    if (ok) {
      loadedPathHint.value = `已加载：${pathResult.title || '学习路径'}`
      await scrollToPathDetail()
      return
    }

    if (!pathError.value) {
      pathError.value = '路径查看失败，请稍后重试。'
    }
  } catch (error) {
    pathError.value = `路径查看失败：${error.message}`
  } finally {
    viewLoadingId.value = ''
  }
}

function selectStep(index) {
  activeStepIndex.value = index
  extraResources.value = []
}

async function generatePath() {
  if (!learningGoal.value.trim()) {
    pathError.value = '请输入详细学习目标。'
    return
  }

  if (!profileLoaded.value) {
    pathError.value = '请先从后端获取学习画像。'
    return
  }

  loading.value = true
  pathError.value = ''

  try {
    const result = await generateLearningPath(learningGoal.value.trim(), profileData)
    applyPathResult(adaptPathResponse(result))

    if (!pathGenerated.value) {
      pathError.value = '后端已响应，但未返回学习节点数据。'
      return
    }

    setCurrentPathId(pathResult.pathId)
    await loadPathHistory()
    await loadPathProgress(pathResult.pathId)
    syncStepIndexWithCurrentNode()
  } catch (error) {
    pathError.value = `学习路线生成失败：${error.message}`
  } finally {
    loading.value = false
  }
}

async function startNode(step) {
  if (!pathResult.pathId || nodeActionLoading.value) return
  nodeActionLoading.value = step.id
  try {
    await updatePathProgress({
      pathId: pathResult.pathId,
      nodeId: step.id,
      completed: false,
    })
    await refreshPathState()
    await loadPathHistory()
  } catch (error) {
    pathError.value = `开始学习失败：${error.message}`
  } finally {
    nodeActionLoading.value = ''
  }
}

async function completeNode(step) {
  if (!pathResult.pathId || nodeActionLoading.value) return
  nodeActionLoading.value = step.id
  try {
    await updatePathProgress({
      pathId: pathResult.pathId,
      nodeId: step.id,
      completed: true,
    })
    await refreshPathState()
    await loadPathHistory()
  } catch (error) {
    pathError.value = `标记完成失败：${error.message}`
  } finally {
    nodeActionLoading.value = ''
  }
}

async function loadMoreResources(step) {
  if (!step?.id || resourcesLoading.value) return
  resourcesLoading.value = true
  try {
    const result = await getNodeResources({ nodeId: step.id })
    const items = Array.isArray(result.items) ? result.items : []
    extraResources.value = items.map((item, index) => ({
      id: item.id || `remote-${index}`,
      title: item.title || '未命名资源',
      meta: item.type || item.resource_type || '',
      description: item.description || item.summary || '',
      url: item.url || item.detail_url || '',
    }))
  } catch (error) {
    pathError.value = `资源加载失败：${error.message}`
    extraResources.value = []
  } finally {
    resourcesLoading.value = false
  }
}

function openLearningResource(item) {
  const url = String(item?.url || '').trim()
  const detailMatch = url.match(/^\/resources\/(\d+)\/view(?:[?#].*)?$/)
  if (detailMatch) {
    router.push({ path: '/resources', query: { open: detailMatch[1] } })
    return
  }
  if (/^https?:\/\//i.test(url)) {
    window.open(url, '_blank', 'noopener,noreferrer')
    return
  }
  if (item?.id && /^\d+$/.test(String(item.id))) {
    router.push({ path: '/resources', query: { open: String(item.id) } })
    return
  }
  router.push('/resources')
}

async function confirmDeletePath(item) {
  if (deleteLoadingId.value) return
  const confirmed = window.confirm(`确定删除路径「${item.title}」吗？此操作不可恢复。`)
  if (!confirmed) return

  deleteLoadingId.value = item.pathId
  pathError.value = ''

  try {
    await deleteLearningPath({ pathId: item.pathId })
    const wasCurrent = String(pathResult.pathId) === String(item.pathId)
    if (wasCurrent) {
      clearCurrentPathId()
      Object.assign(pathResult, emptyPathResult())
      applyProgressData(emptyProgressData())
      pathGenerated.value = false
    }
    await loadPathHistory()
    if (wasCurrent && pathHistory.value.length) {
      const next = pathHistory.value.find((row) => row.status === 'active') || pathHistory.value[0]
      if (next?.pathId) await loadPathById(next.pathId)
    }
  } catch (error) {
    pathError.value = `删除路径失败：${error.message}`
  } finally {
    deleteLoadingId.value = ''
  }
}

async function submitFeedback() {
  if (!pathResult.pathId || !feedbackRating.value || feedbackSubmitting.value) return
  feedbackSubmitting.value = true
  try {
    await submitPathFeedback({
      pathId: pathResult.pathId,
      rating: feedbackRating.value,
      comment: feedbackComment.value.trim(),
    })
    feedbackSubmitted.value = true
  } catch (error) {
    pathError.value = `反馈提交失败：${error.message}`
  } finally {
    feedbackSubmitting.value = false
  }
}

function resetPath() {
  learningGoal.value = ''
  pathError.value = ''
  restoreMessage.value = ''
  pathGenerated.value = false
  activeStepIndex.value = 0
  clearCurrentPathId()
  Object.assign(pathResult, emptyPathResult())
  applyProgressData(emptyProgressData())
  extraResources.value = []
  feedbackSubmitted.value = false
  feedbackRating.value = 0
  feedbackComment.value = ''
}

watch(activeStep, () => {
  extraResources.value = []
})

onMounted(async () => {
  await loadProfile()
  await loadPathHistory()
  await restoreCurrentPath()
})
</script>

<style scoped>
.learning-path-page {
  position: relative;
  min-height: 100vh;
  padding: 32px;
  background: #f5f7fa;
  color: #1a2332;
  box-sizing: border-box;
}

.page-back-link {
  position: absolute;
  left: 32px;
  top: 28px;
  z-index: 10;
}

.path-content {
  max-width: 1440px;
  margin: 0 auto;
  padding-top: 52px;
}

/* 通用卡片样式 */
.hero-card,
.history-card,
.profile-card,
.planner-card,
.result-card {
  background: #ffffff;
  border: 1px solid #e8ecf1;
  border-radius: 16px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.04);
  transition: box-shadow 0.3s ease;
}

.hero-card:hover,
.history-card:hover,
.profile-card:hover,
.planner-card:hover,
.result-card:hover {
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.06);
}

/* Hero */
.hero-card {
  padding: 48px 52px;
  margin-bottom: 28px;
  background: #ffffff;
  border: 1px solid #e8ecf1;
  position: relative;
  overflow: hidden;
}

.hero-badge {
  display: inline-block;
  padding: 6px 18px;
  margin-bottom: 16px;
  border-radius: 20px;
  background: #eef0f5;
  color: #2c3e50;
  font-size: 13px;
  font-weight: 600;
  letter-spacing: 0.3px;
  position: relative;
  z-index: 1;
}

.hero-card h1 {
  margin: 0 0 14px;
  font-size: 38px;
  font-weight: 700;
  line-height: 1.2;
  color: #1a2332;
  position: relative;
  z-index: 1;
}

.hero-card .description {
  max-width: 800px;
  margin: 0;
  line-height: 1.8;
  font-size: 16px;
  color: #4a5a6e;
  position: relative;
  z-index: 1;
}

/* 历史路径 */
.history-card {
  padding: 28px 32px;
  margin-bottom: 28px;
}

.panel-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 20px;
}

.panel-head span {
  display: block;
  font-size: 20px;
  font-weight: 700;
  color: #1a2332;
}

.panel-head small {
  color: #6b7a8f;
  font-size: 13px;
  font-weight: 400;
}

.panel-head em {
  padding: 4px 14px;
  border-radius: 20px;
  background: #f0f2f5;
  color: #4a5a6e;
  font-size: 12px;
  font-style: normal;
  font-weight: 600;
  white-space: nowrap;
}

.history-list {
  display: grid;
  gap: 12px;
}

.history-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 16px 20px;
  border: 1px solid #e8ecf1;
  border-radius: 12px;
  background: #fafbfc;
  transition: all 0.3s ease;
}

.history-item:hover {
  border-color: #b0b8c8;
  background: #f5f7fa;
}

.history-item.active {
  border-color: #4a6cf7;
  background: #f0f4ff;
}

.history-main {
  flex: 1;
  min-width: 0;
}

.history-main strong {
  display: block;
  margin-bottom: 4px;
  font-size: 15px;
  color: #1a2332;
}

.history-main p {
  margin: 0 0 8px;
  color: #4a5a6e;
  font-size: 13px;
}

.history-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.history-meta span {
  padding: 2px 12px;
  border-radius: 20px;
  background: #ffffff;
  color: #4a5a6e;
  font-size: 12px;
  font-weight: 500;
  border: 1px solid #e8ecf1;
}

.history-actions {
  display: flex;
  gap: 8px;
  flex-shrink: 0;
}

/* 主网格 */
.main-grid {
  display: grid;
  grid-template-columns: 380px 1fr;
  gap: 28px;
  align-items: stretch;
  margin-bottom: 28px;
}

.profile-card,
.planner-card {
  padding: 28px 30px;
}

.profile-card .full-width {
  width: 100%;
  justify-content: center;
  margin-top: 16px;
}

.profile-summary {
  padding: 16px 20px;
  border-radius: 12px;
  background: #f0f4ff;
  border: 1px solid #d6e0f5;
  margin-bottom: 16px;
}

.profile-summary strong {
  display: block;
  margin-bottom: 4px;
  font-size: 18px;
  color: #1a2332;
}

.profile-summary p {
  margin: 0;
  color: #2c3e50;
  line-height: 1.6;
  font-size: 14px;
}

.profile-list {
  display: grid;
  gap: 10px;
  margin-bottom: 16px;
}

.profile-list div {
  display: grid;
  gap: 2px;
  padding: 12px 16px;
  border-radius: 10px;
  background: #ffffff;
  border: 1px solid #e8ecf1;
}

.profile-list span {
  color: #6b7a8f;
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.3px;
}

.profile-list strong {
  color: #1a2332;
  font-size: 14px;
}

.tag-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.tag-list span {
  padding: 4px 14px;
  border-radius: 20px;
  background: #f0f2f5;
  color: #2c3e50;
  font-size: 12px;
  font-weight: 600;
}

.planner-card textarea {
  width: 100%;
  min-height: 140px;
  resize: vertical;
  border: 1px solid #d6dce6;
  border-radius: 12px;
  padding: 16px 18px;
  box-sizing: border-box;
  outline: none;
  background: #fafbfc;
  color: #1a2332;
  line-height: 1.8;
  font-size: 15px;
  transition: all 0.3s ease;
  font-family: inherit;
}

.planner-card textarea:focus {
  border-color: #4a6cf7;
  background: #ffffff;
  box-shadow: 0 0 0 4px rgba(74, 108, 247, 0.06);
}

.planner-card textarea::placeholder {
  color: #9aabb8;
}

.action-row {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  margin-top: 16px;
}

/* 按钮 */
.primary-button,
.ghost-button {
  border: none;
  border-radius: 12px;
  padding: 12px 24px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  display: inline-flex;
  align-items: center;
  gap: 8px;
}

.primary-button {
  background: #2c3e50;
  color: #ffffff;
  box-shadow: 0 2px 8px rgba(44, 62, 80, 0.15);
}

.primary-button:hover {
  background: #1a2a3a;
  transform: translateY(-1px);
  box-shadow: 0 4px 16px rgba(44, 62, 80, 0.2);
}

.primary-button:disabled {
  cursor: not-allowed;
  opacity: 0.6;
  transform: none;
}

.ghost-button {
  background: #f0f2f5;
  color: #1a2332;
  border: 1px solid #d6dce6;
}

.ghost-button:hover {
  background: #e4e8ee;
  transform: translateY(-1px);
}

.ghost-button.danger {
  color: #b91c1c;
}

.ghost-button.danger:hover {
  background: #fee2e2;
  border-color: #b91c1c;
}

.ghost-button.full-width {
  width: 100%;
  justify-content: center;
}

/* 结果卡片 */
.result-card {
  padding: 32px 36px;
  min-height: 400px;
}

.empty-state {
  min-height: 320px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
}

.empty-icon {
  width: 64px;
  height: 64px;
  margin-bottom: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 16px;
  background: #eef0f5;
  color: #2c3e50;
  font-size: 32px;
  font-weight: 300;
}

.empty-state h2 {
  margin: 0 0 10px;
  font-size: 24px;
  color: #1a2332;
}

.empty-state p {
  margin: 0;
  color: #6b7a8f;
  font-size: 15px;
}

/* 结果头部 */
.result-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 20px;
  padding-bottom: 20px;
  border-bottom: 1px solid #e8ecf1;
  margin-bottom: 20px;
}

.result-head span {
  display: block;
  margin-bottom: 4px;
  font-size: 12px;
  font-weight: 600;
  letter-spacing: 0.08em;
  color: #6b7a8f;
  text-transform: uppercase;
}

.result-head h2 {
  margin: 0 0 8px;
  font-size: 26px;
  font-weight: 700;
  color: #1a2332;
}

.result-head p {
  margin: 0;
  color: #4a5a6e;
  line-height: 1.7;
  font-size: 14px;
}

.duration-badge {
  padding: 6px 18px;
  border-radius: 20px;
  background: #f0f4ff;
  color: #4a6cf7;
  font-size: 14px;
  font-weight: 600;
  white-space: nowrap;
  border: 1px solid #d6e0f5;
}

/* 进度面板 */
.progress-panel {
  padding: 16px 24px;
  margin: 0 0 20px;
  border-radius: 12px;
  background: #f8f9fb;
  border: 1px solid #e8ecf1;
}

.progress-stats {
  display: flex;
  flex-wrap: wrap;
  gap: 16px 24px;
  align-items: center;
  margin-bottom: 12px;
  color: #4a5a6e;
  font-size: 13px;
}

.progress-stats strong {
  font-size: 28px;
  font-weight: 700;
  color: #1a2332;
}

.progress-bar {
  height: 6px;
  border-radius: 20px;
  background: #e8ecf1;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: #4a6cf7;
  border-radius: 20px;
  transition: width 0.6s ease;
}

/* 路线步骤 */
.roadmap-flow {
  display: flex;
  align-items: stretch;
  gap: 10px;
  overflow-x: auto;
  padding: 16px 4px 24px;
  scroll-behavior: smooth;
}

.roadmap-flow::-webkit-scrollbar {
  height: 4px;
}

.roadmap-flow::-webkit-scrollbar-track {
  background: #f0f2f5;
  border-radius: 20px;
}

.roadmap-flow::-webkit-scrollbar-thumb {
  background: #b0b8c8;
  border-radius: 20px;
}

.road-step {
  flex: 0 0 220px;
  padding: 16px 20px;
  border: 1px solid #e8ecf1;
  border-radius: 14px;
  background: #ffffff;
  cursor: pointer;
  transition: all 0.3s ease;
  position: relative;
}

.road-step:hover {
  transform: translateY(-3px);
  border-color: #b0b8c8;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.04);
}

.road-step.active {
  border-color: #4a6cf7;
  box-shadow: 0 4px 20px rgba(74, 108, 247, 0.08);
}

.road-step.current {
  border-color: #e6a000;
  background: #fffcf0;
}

.road-step.completed {
  border-color: #2e7d5e;
  background: #f0f9f5;
}

.step-index {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 10px;
  background: #eef0f5;
  color: #2c3e50;
  font-weight: 700;
  font-size: 14px;
  margin-bottom: 10px;
}

.road-step .step-period {
  display: block;
  color: #6b7a8f;
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.3px;
}

.road-step h3 {
  margin: 4px 0 4px;
  color: #1a2332;
  font-size: 16px;
  font-weight: 600;
}

.road-step p {
  margin: 0 0 8px;
  color: #4a5a6e;
  line-height: 1.5;
  font-size: 13px;
  display: -webkit-box;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.step-status {
  display: inline-block;
  padding: 2px 12px;
  border-radius: 20px;
  background: #f0f2f5;
  color: #4a5a6e;
  font-size: 11px;
  font-style: normal;
  font-weight: 600;
}

.road-step.completed .step-status {
  background: #2e7d5e;
  color: #ffffff;
}

.road-step.current .step-status {
  background: #e6a000;
  color: #ffffff;
}

.road-step.active .step-status {
  background: #4a6cf7;
  color: #ffffff;
}

.step-resources-badge {
  margin-top: 10px;
  padding: 3px 12px;
  border-radius: 20px;
  background: #f0f4ff;
  color: #4a6cf7;
  font-size: 11px;
  font-weight: 600;
  display: inline-block;
}

.step-arrow {
  flex: 0 0 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #b0b8c8;
  font-size: 20px;
  font-weight: 300;
}

/* 详情面板 */
.detail-panel {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 20px;
  padding: 24px 28px;
  margin-bottom: 24px;
  border-radius: 14px;
  background: #f8f9fb;
  border: 1px solid #e8ecf1;
}

.detail-content {
  flex: 1;
}

.detail-period {
  display: block;
  color: #6b7a8f;
  font-size: 12px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.3px;
}

.detail-panel h3 {
  margin: 4px 0 8px;
  font-size: 20px;
  font-weight: 700;
  color: #1a2332;
}

.detail-panel p {
  margin: 0 0 14px;
  color: #4a5a6e;
  line-height: 1.8;
  font-size: 15px;
}

.detail-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  flex-shrink: 0;
}

.detail-tags em {
  padding: 4px 14px;
  border-radius: 20px;
  background: #f0f4ff;
  color: #4a6cf7;
  font-size: 12px;
  font-style: normal;
  font-weight: 600;
}

.node-actions {
  display: flex;
  gap: 10px;
  margin-top: 4px;
}

/* 资源区域 - 四列布局 */
.resource-section {
  margin-top: 8px;
}

.section-head {
  margin-bottom: 20px;
}

.section-head span {
  display: block;
  margin-bottom: 4px;
  font-size: 12px;
  font-weight: 600;
  letter-spacing: 0.08em;
  color: #6b7a8f;
  text-transform: uppercase;
}

.section-head h2 {
  margin: 0 0 6px;
  font-size: 22px;
  font-weight: 700;
  color: #1a2332;
}

.section-head p {
  margin: 0;
  color: #6b7a8f;
  font-size: 14px;
}

.resource-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 18px;
}

.resource-group {
  padding: 18px 20px;
  border-radius: 14px;
  background: #f8f9fb;
  border: 1px solid #e8ecf1;
  transition: all 0.3s ease;
}

.resource-group:hover {
  border-color: #b0b8c8;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.02);
}

.resource-group-head {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 14px;
}

.resource-icon {
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 10px;
  background: #f0f2f5;
  font-size: 18px;
}

.resource-group h3 {
  margin: 0;
  font-size: 15px;
  font-weight: 600;
  color: #1a2332;
}

.resource-group-head span {
  display: block;
  color: #6b7a8f;
  font-size: 11px;
  font-weight: 400;
}

.resource-list {
  display: grid;
  gap: 10px;
}

.resource-item {
  display: block;
  width: 100%;
  padding: 12px 14px;
  border-radius: 10px;
  background: #ffffff;
  border: 1px solid #e8ecf1;
  text-decoration: none;
  transition: all 0.3s ease;
  cursor: pointer;
  color: inherit;
  font: inherit;
  text-align: left;
}

.resource-item:hover {
  transform: translateY(-2px);
  border-color: #4a6cf7;
  box-shadow: 0 4px 16px rgba(74, 108, 247, 0.06);
}

.resource-item strong {
  display: block;
  color: #1a2332;
  font-size: 14px;
  font-weight: 600;
}

.resource-item span {
  display: block;
  color: #6b7a8f;
  font-size: 12px;
  font-weight: 400;
}

.resource-item p {
  margin: 4px 0 0;
  color: #4a5a6e;
  font-size: 12px;
  line-height: 1.5;
}

/* 反馈面板 */
.feedback-panel {
  margin-top: 28px;
  padding: 24px 28px;
  border-radius: 14px;
  background: #f8f9fb;
  border: 1px solid #e8ecf1;
}

.feedback-success {
  padding: 14px 20px;
  border-radius: 10px;
  background: #e6f5ed;
  color: #1e5a44;
  font-weight: 600;
  font-size: 14px;
}

.feedback-rating {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 14px;
}

.feedback-rating span {
  font-weight: 600;
  color: #1a2332;
  font-size: 15px;
}

.rating-star {
  width: 36px;
  height: 36px;
  border: 1px solid #d6dce6;
  border-radius: 10px;
  background: #ffffff;
  cursor: pointer;
  font-size: 18px;
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #d6dce6;
}

.rating-star:hover {
  border-color: #e6a000;
  transform: scale(1.05);
}

.rating-star.active {
  background: #fffcf0;
  border-color: #e6a000;
  color: #e6a000;
}

.feedback-panel textarea {
  width: 100%;
  min-height: 80px;
  resize: vertical;
  border: 1px solid #d6dce6;
  border-radius: 10px;
  padding: 14px 16px;
  box-sizing: border-box;
  outline: none;
  background: #ffffff;
  color: #1a2332;
  font-size: 14px;
  line-height: 1.7;
  font-family: inherit;
  transition: all 0.3s ease;
}

.feedback-panel textarea:focus {
  border-color: #4a6cf7;
  box-shadow: 0 0 0 4px rgba(74, 108, 247, 0.06);
}

.feedback-panel .primary-button {
  margin-top: 14px;
}

/* 响应式 */
@media (max-width: 1200px) {
  .resource-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 1024px) {
  .main-grid {
    grid-template-columns: 1fr;
  }

  .hero-card h1 {
    font-size: 30px;
  }
}

@media (max-width: 768px) {
  .learning-path-page {
    padding: 16px;
  }

  .page-back-link {
    left: 16px;
    top: 16px;
  }

  .path-content {
    padding-top: 44px;
  }

  .hero-card {
    padding: 24px 20px;
  }

  .hero-card h1 {
    font-size: 22px;
  }

  .history-card,
  .profile-card,
  .planner-card,
  .result-card {
    padding: 16px;
  }

  .history-item {
    flex-direction: column;
    align-items: stretch;
  }

  .resource-grid {
    grid-template-columns: 1fr;
  }

  .detail-panel {
    flex-direction: column;
  }

  .road-step {
    flex: 0 0 180px;
  }

  .result-head {
    flex-direction: column;
  }

  .duration-badge {
    align-self: flex-start;
  }

  .step-arrow {
    display: none;
  }

  .panel-head {
    flex-direction: column;
  }

  .roadmap-flow {
    padding: 12px 2px 16px;
  }
}

/* ?????????????????? */

.history-error {
  margin-top: 12px;
}

.action-row,
.node-actions,
.resource-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  margin-top: 16px;
}

.form-tip,
.error-text,
.info-text {
  margin: 12px 0 0;
  font-size: 13px;
  line-height: 1.7;
}

.form-tip,
.info-text {
  color: #6b7280;
}

.error-text,
.error-block {
  color: #b91c1c;
}

.pending-block,
.error-block {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 120px;
  border: 1px dashed #d1d5db;
  border-radius: 18px;
  background: #f9fafb;
  color: #6b7280;
  line-height: 1.7;
  text-align: center;
  padding: 16px;
}

.loaded-hint {
  margin: 0 0 16px;
  padding: 12px 16px;
  border-radius: 14px;
  background: #ecfdf5;
  border: 1px solid #a7f3d0;
  color: #065f46;
  font-size: 14px;
  font-weight: 800;
  line-height: 1.6;
}

</style>
