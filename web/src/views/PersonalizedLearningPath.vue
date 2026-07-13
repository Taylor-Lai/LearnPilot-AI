<template>
  <section class="learning-path-page">
    <RouterLink class="ui-back-link page-back-link" to="/">
      ← 返回首页
    </RouterLink>

    <main class="path-content">
      <section class="hero-card">
        <p class="eyebrow">PERSONALIZED LEARNING PATH</p>
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
                  <a
                    v-for="item in group.items"
                    :key="item.id || item.title"
                    :href="item.url || 'javascript:void(0)'"
                    class="resource-item"
                    :target="item.url ? '_blank' : undefined"
                    :rel="item.url ? 'noopener noreferrer' : undefined"
                  >
                    <strong>{{ item.title || '未命名资源' }}</strong>
                    <span>{{ item.meta || item.description || item.source || '学习资源' }}</span>
                  </a>
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
import { RouterLink } from 'vue-router'
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
  background: var(--bg-page);
  color: #111827;
  box-sizing: border-box;
}

.page-back-link {
  position: absolute;
  left: 32px;
  top: 28px;
}

.path-content {
  max-width: 1640px;
  margin: 0 auto;
  padding-top: 52px;
}

.hero-card,
.profile-card,
.planner-card,
.result-card,
.detail-panel,
.resource-group,
.history-card,
.feedback-panel,
.progress-panel {
  background: var(--bg-card);
  border: 1px solid #e5e7eb;
  border-radius: 18px;
  box-shadow: var(--shadow-md);
}

.hero-card,
.history-card {
  padding: 42px;
  margin-bottom: 24px;
}

.history-error {
  margin-top: 12px;
}

.history-list {
  display: grid;
  gap: 12px;
}

.history-item {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  padding: 16px;
  border: 1px solid #e5e7eb;
  border-radius: 18px;
  background: #f9fafb;
}

.history-item.active {
  border-color: #111827;
  background: #ffffff;
}

.history-main strong {
  display: block;
  margin-bottom: 6px;
  font-size: 16px;
}

.history-main p {
  margin: 0 0 8px;
  color: #4b5563;
  font-size: 13px;
  line-height: 1.6;
}

.history-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.history-meta span {
  padding: 4px 10px;
  border-radius: 999px;
  background: #f3f4f6;
  color: #4b5563;
  font-size: 12px;
  font-weight: 700;
}

.history-actions {
  display: flex;
  gap: 8px;
  flex-shrink: 0;
}

.ghost-button.danger {
  color: #b91c1c;
}

.eyebrow {
  margin: 0 0 10px;
  font-size: 13px;
  font-weight: 800;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: #111827;
}

.hero-card h1 {
  margin: 0 0 14px;
  font-size: 34px;
  line-height: 1.25;
  color: #111827;
}

.description {
  max-width: 900px;
  margin: 0;
  line-height: 1.9;
  font-size: 15px;
  color: #374151;
}

.main-grid {
  display: grid;
  grid-template-columns: minmax(320px, 0.82fr) minmax(520px, 1.18fr);
  gap: 24px;
  align-items: stretch;
  margin-bottom: 24px;
}

.profile-card,
.planner-card,
.result-card {
  padding: 22px;
}

.panel-head,
.result-head,
.section-head,
.resource-group-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 18px;
}

.panel-head span,
.result-head h2,
.section-head h2,
.resource-group h3 {
  color: #111827;
  font-weight: 900;
}

.panel-head span {
  display: block;
  margin-bottom: 6px;
  font-size: 21px;
}

.panel-head small {
  color: #6b7280;
  font-size: 13px;
}

.panel-head em,
.result-head strong {
  padding: 7px 12px;
  border-radius: 999px;
  background: #f3f4f6;
  color: #4b5563;
  font-size: 12px;
  font-style: normal;
  font-weight: 800;
  white-space: nowrap;
}

.profile-summary {
  padding: 18px;
  border-radius: 18px;
  background: #f9fafb;
  border: 1px solid #e5e7eb;
  margin-bottom: 14px;
}

.profile-summary strong {
  display: block;
  margin-bottom: 8px;
  font-size: 20px;
  color: #111827;
}

.profile-summary p,
.result-head p,
.section-head p {
  margin: 0;
  color: #4b5563;
  line-height: 1.8;
  font-size: 14px;
}

.profile-list {
  display: grid;
  gap: 10px;
  margin-bottom: 16px;
}

.profile-list div {
  display: grid;
  gap: 6px;
  padding: 14px;
  border: 1px solid #e5e7eb;
  border-radius: 18px;
  background: #ffffff;
}

.profile-list span {
  color: #6b7280;
  font-size: 12px;
  font-weight: 800;
}

.profile-list strong {
  color: #111827;
  line-height: 1.7;
  font-size: 14px;
}

.tag-list,
.detail-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.tag-list span,
.detail-tags em {
  padding: 7px 12px;
  border-radius: 999px;
  background: #f3f4f6;
  color: #374151;
  font-size: 12px;
  font-style: normal;
  font-weight: 800;
}

textarea {
  width: 100%;
  min-height: 194px;
  resize: vertical;
  border: 1px solid #e5e7eb;
  border-radius: 18px;
  padding: 18px;
  box-sizing: border-box;
  outline: none;
  background: #f9fafb;
  color: #111827;
  line-height: 1.8;
  font-size: 15px;
  transition: border-color 0.2s ease, box-shadow 0.2s ease;
}

textarea:focus {
  border-color: #111827;
  box-shadow: 0 0 0 4px rgba(17, 24, 39, 0.08);
}

.action-row,
.node-actions,
.resource-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  margin-top: 16px;
}

.primary-button,
.ghost-button {
  border: none;
  border-radius: 16px;
  padding: 12px 18px;
  font-size: 14px;
  font-weight: 900;
  cursor: pointer;
  transition: transform 0.2s ease, opacity 0.2s ease, background 0.2s ease;
}

.primary-button {
  background: #111827;
  color: #ffffff;
}

.ghost-button {
  background: #f3f4f6;
  color: #111827;
  border: 1px solid #e5e7eb;
}

.profile-card > .ghost-button {
  width: 100%;
  margin-top: 16px;
}

.primary-button:hover,
.ghost-button:hover {
  transform: translateY(-2px);
}

.primary-button:disabled,
.ghost-button:disabled {
  cursor: not-allowed;
  opacity: 0.55;
  transform: none;
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

.result-card {
  min-height: 420px;
  scroll-margin-top: 24px;
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

.empty-state {
  min-height: 340px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
}

.empty-icon {
  width: 76px;
  height: 76px;
  margin-bottom: 18px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 18px;
  background: #111827;
  color: #ffffff;
  font-weight: 900;
}

.empty-state h2 {
  margin: 0 0 10px;
  font-size: 24px;
  color: #111827;
}

.empty-state p {
  margin: 0;
  color: #6b7280;
}

.result-head {
  align-items: center;
  padding-bottom: 18px;
  border-bottom: 1px solid #e5e7eb;
}

.result-head span,
.section-head span {
  display: block;
  margin-bottom: 8px;
  font-size: 12px;
  font-weight: 900;
  letter-spacing: 0.08em;
  color: #6b7280;
}

.result-head h2,
.section-head h2 {
  margin: 0 0 8px;
  font-size: 26px;
}

.progress-panel {
  padding: 18px 20px;
  margin: 18px 0 8px;
  background: #f9fafb;
}

.progress-stats {
  display: flex;
  flex-wrap: wrap;
  gap: 12px 18px;
  align-items: center;
  margin-bottom: 12px;
  color: #4b5563;
  font-size: 13px;
}

.progress-stats strong {
  font-size: 28px;
  color: #111827;
}

.progress-bar {
  height: 10px;
  border-radius: 999px;
  background: #e5e7eb;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: #111827;
  border-radius: 999px;
  transition: width 0.25s ease;
}

.roadmap-flow {
  display: flex;
  align-items: stretch;
  gap: 14px;
  overflow-x: auto;
  padding: 16px 2px 24px;
}

.road-step {
  position: relative;
  min-width: 230px;
  padding: 20px 18px;
  border: 1px solid #e5e7eb;
  border-radius: 18px;
  background: #ffffff;
  cursor: pointer;
  transition: transform 0.2s ease, border-color 0.2s ease, box-shadow 0.2s ease;
}

.road-step:hover,
.road-step.active,
.road-step.current {
  transform: translateY(-3px);
  border-color: #111827;
  box-shadow: 0 14px 28px rgba(17, 24, 39, 0.08);
}

.road-step.completed {
  background: #f9fafb;
}

.step-index {
  width: 38px;
  height: 38px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 14px;
  background: #111827;
  color: #ffffff;
  font-weight: 900;
  margin-bottom: 14px;
}

.road-step span,
.detail-panel span {
  color: #6b7280;
  font-size: 12px;
  font-weight: 900;
}

.road-step h3,
.detail-panel h3 {
  margin: 8px 0;
  color: #111827;
  font-size: 18px;
}

.road-step p,
.detail-panel p {
  margin: 0;
  color: #4b5563;
  line-height: 1.75;
  font-size: 13px;
}

.step-status {
  display: inline-block;
  margin-top: 10px;
  padding: 4px 10px;
  border-radius: 999px;
  background: #f3f4f6;
  color: #374151;
  font-size: 11px;
  font-style: normal;
  font-weight: 800;
}

.step-arrow {
  min-width: 46px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #111827;
  font-size: 30px;
  font-weight: 900;
}

.detail-panel {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 20px;
  padding: 20px;
  margin-bottom: 24px;
  background: #f9fafb;
}

.detail-panel > div:first-child {
  flex: 1;
}

.resource-section,
.feedback-panel {
  padding-top: 4px;
}

.feedback-panel {
  margin-top: 24px;
  padding: 20px;
  background: #f9fafb;
}

.feedback-rating {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
}

.rating-star {
  width: 36px;
  height: 36px;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  background: #ffffff;
  cursor: pointer;
  font-weight: 800;
}

.rating-star.active {
  background: #111827;
  color: #ffffff;
  border-color: #111827;
}

.section-head {
  display: block;
}

.resource-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 16px;
}

.resource-group {
  padding: 18px;
}

.resource-group-head {
  justify-content: flex-start;
  margin-bottom: 14px;
}

.resource-group-head i {
  width: 42px;
  height: 42px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 16px;
  background: #f3f4f6;
  font-style: normal;
  font-size: 22px;
}

.resource-group h3 {
  margin: 0 0 5px;
  font-size: 18px;
}

.resource-group-head span {
  color: #6b7280;
  font-size: 12px;
}

.resource-list {
  display: grid;
  gap: 10px;
}

.resource-item {
  display: block;
  padding: 13px;
  border-radius: 16px;
  background: #f9fafb;
  border: 1px solid #e5e7eb;
  text-decoration: none;
  transition: transform 0.2s ease, border-color 0.2s ease;
}

.resource-item:hover {
  transform: translateY(-2px);
  border-color: #111827;
}

.resource-item strong {
  display: block;
  margin-bottom: 5px;
  color: #111827;
  font-size: 14px;
}

.resource-item span {
  color: #6b7280;
  font-size: 12px;
  line-height: 1.6;
}

@media (max-width: 1100px) {
  .main-grid,
  .resource-grid {
    grid-template-columns: 1fr;
  }

  .roadmap-flow {
    align-items: stretch;
  }

  .history-item {
    flex-direction: column;
  }
}

@media (max-width: 720px) {
  .learning-path-page {
    padding: 24px 16px;
  }

  .page-back-link {
    left: 16px;
  }

  .hero-card,
  .profile-card,
  .planner-card,
  .result-card,
  .history-card {
    padding: 18px;
  }

  .hero-card h1 {
    font-size: 27px;
  }

  .detail-panel,
  .result-head {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>
