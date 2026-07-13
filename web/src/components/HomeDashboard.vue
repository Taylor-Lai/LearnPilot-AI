<template>
  <section class="home-dashboard">
    <div v-if="!isLoggedIn" class="dashboard-shell guest-shell">
      <div class="guest-card">
        <p class="eyebrow">LEARNING OVERVIEW</p>
        <h2>登录后查看你的学习进展</h2>
        <p class="guest-desc">
          登录后可在此查看学习画像、当前路径、最近评测、资源生成任务与学习统计。
        </p>
        <div class="guest-actions">
          <RouterLink class="primary-btn" to="/login">登录</RouterLink>
          <RouterLink class="ghost-btn" to="/register">注册</RouterLink>
        </div>
      </div>
    </div>

    <div v-else class="dashboard-shell">
      <div v-if="loading" class="loading-box">正在加载学习概览...</div>

      <template v-else>
        <section class="dash-card welcome-card">
          <p class="eyebrow">WELCOME</p>
          <h2>你好，{{ displayName }}</h2>
          <p v-if="userError" class="section-error">{{ userError }}</p>
          <div class="welcome-meta">
            <span>{{ profile?.major || '专业未设置' }}</span>
            <span>{{ profile?.grade || '年级未设置' }}</span>
            <span>{{ profile?.course || '课程未设置' }}</span>
          </div>
        </section>

        <section class="dash-card">
          <div class="card-head">
            <div>
              <p class="eyebrow">GOAL</p>
              <h3>当前学习目标</h3>
            </div>
            <RouterLink class="ghost-btn link-btn" :to="{ name: 'profileBuilder' }">
              {{ hasProfile ? '查看或更新画像' : '构建学习画像' }}
            </RouterLink>
          </div>
          <p v-if="profileError" class="section-error">{{ profileError }}</p>
          <div v-else-if="!hasProfile" class="empty-box">
            尚未构建学习画像，建议先完成对话式画像构建。
          </div>
          <div v-else class="info-grid">
            <div class="info-item full">
              <label>学习目标</label>
              <p class="ellipsis-2">{{ profile.goal || '未设置' }}</p>
            </div>
            <div class="info-item">
              <label>当前课程</label>
              <p class="ellipsis">{{ profile.course || '未设置' }}</p>
            </div>
            <div class="info-item">
              <label>基础水平</label>
              <p>{{ knowledgeLevelText(profile.knowledge_level) }}</p>
            </div>
            <div class="info-item full">
              <label>薄弱知识点</label>
              <p class="ellipsis-2">{{ weakPointsLabel }}</p>
            </div>
          </div>
        </section>

        <div class="summary-grid">
          <section class="dash-card clickable-card" @click="openCurrentPath">
            <div class="card-head">
              <div>
                <p class="eyebrow">PATH</p>
                <h3>当前学习路径</h3>
              </div>
            </div>
            <p v-if="pathsError" class="section-error">{{ pathsError }}</p>
            <div v-else-if="!currentPath" class="empty-box">
              尚未生成学习路径
              <RouterLink class="inline-link" :to="{ name: 'learningPath' }" @click.stop>去生成路径</RouterLink>
            </div>
            <div v-else class="record-body">
              <strong class="ellipsis">{{ currentPath.title }}</strong>
              <p class="ellipsis-2">{{ currentPath.goal }}</p>
              <span class="meta">{{ formatDate(currentPath.createdAt) }} · {{ pathStatusText(currentPath.status) }}</span>
              <div class="progress-row">
                <div class="progress-track"><i :style="{ width: `${currentPath.progress}%` }"></i></div>
                <span>{{ currentPath.progress }}%</span>
              </div>
            </div>
          </section>

          <section class="dash-card clickable-card" @click="openLatestEvaluation">
            <div class="card-head">
              <div>
                <p class="eyebrow">EVALUATION</p>
                <h3>最近学习评测</h3>
              </div>
            </div>
            <p v-if="evaluationsError" class="section-error">{{ evaluationsError }}</p>
            <div v-else-if="!latestEvaluation" class="empty-box">
              暂无评测记录
              <RouterLink class="inline-link" :to="{ name: 'evaluation' }" @click.stop>去开始评测</RouterLink>
            </div>
            <div v-else class="record-body">
              <strong>分数 {{ latestEvaluation.score ?? '-' }}</strong>
              <p class="ellipsis-2">{{ latestEvaluation.feedback }}</p>
              <span class="meta">{{ formatDate(latestEvaluation.created_at) }} · {{ formatAccuracy(latestEvaluation.accuracy) }}</span>
            </div>
          </section>

          <section class="dash-card clickable-card" @click="openLatestTask">
            <div class="card-head">
              <div>
                <p class="eyebrow">PRODUCER</p>
                <h3>最近资源生成任务</h3>
              </div>
            </div>
            <p v-if="tasksError" class="section-error">{{ tasksError }}</p>
            <div v-else-if="!latestTask" class="empty-box">
              暂无资源生成任务
              <RouterLink class="inline-link" :to="{ name: 'multiAgentResource' }" @click.stop>去创建任务</RouterLink>
            </div>
            <div v-else class="record-body">
              <strong class="ellipsis">{{ latestTask.topic }}</strong>
              <p class="ellipsis">{{ summarizeRequirement(latestTask.requirement) }}</p>
              <span class="meta">{{ formatDate(latestTask.created_at) }} · {{ producerStatusText(latestTask.status) }}</span>
              <div class="progress-row">
                <div class="progress-track"><i :style="{ width: `${latestTask.progress || 0}%` }"></i></div>
                <span>{{ latestTask.progress || 0 }}%</span>
              </div>
            </div>
          </section>
        </div>

        <section class="dash-card">
          <div class="card-head">
            <div>
              <p class="eyebrow">STATISTICS</p>
              <h3>学习统计</h3>
            </div>
            <RouterLink class="ghost-btn link-btn" :to="{ name: 'profile' }">个人中心</RouterLink>
          </div>
          <div class="stats-grid">
            <article class="stat-item">
              <span>学习路径</span>
              <strong>{{ statistics.learningPathCount }}</strong>
            </article>
            <article class="stat-item">
              <span>已完成路径</span>
              <strong>{{ statistics.completedPathCount }}</strong>
            </article>
            <article class="stat-item">
              <span>平均路径进度</span>
              <strong>{{ statistics.averagePathProgress }}%</strong>
            </article>
            <article class="stat-item">
              <span>评测次数</span>
              <strong>{{ statistics.evaluationCount }}</strong>
            </article>
            <article class="stat-item">
              <span>平均评测分</span>
              <strong>{{ statistics.averageScore }}</strong>
            </article>
            <article class="stat-item">
              <span>资源生成任务</span>
              <strong>{{ statistics.producerTaskCount }}</strong>
            </article>
          </div>
        </section>

        <section class="dash-card">
          <div class="card-head">
            <div>
              <p class="eyebrow">RESOURCES</p>
              <h3>推荐学习资源</h3>
            </div>
            <RouterLink class="ghost-btn link-btn" :to="{ name: 'resources' }">浏览资源库</RouterLink>
          </div>
          <p v-if="resourcesLoading" class="empty-box">正在加载推荐资源...</p>
          <p v-else-if="resourcesError" class="section-error">{{ resourcesError }}</p>
          <div v-else-if="!recommendedResources.length" class="empty-box">暂无匹配资源</div>
          <div v-else class="resource-list">
            <button
              v-for="item in recommendedResources"
              :key="item.id"
              type="button"
              class="resource-item"
              @click="openResource(item)"
            >
              <strong class="ellipsis">{{ item.title }}</strong>
              <span class="meta ellipsis">{{ item.typeLabel }}</span>
              <p class="ellipsis-2">{{ item.description }}</p>
              <span v-if="item.metaStats" class="meta">{{ item.metaStats }}</span>
            </button>
          </div>
        </section>
      </template>
    </div>
  </section>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { RouterLink, useRouter } from 'vue-router'
import { getResourceList } from '../api/resource'
import { userStore } from '../stores/userStore'
import {
  buildResourceQuery,
  buildStatistics,
  fetchDashboardData,
  formatAccuracy,
  formatDate,
  hasProfileSummary,
  knowledgeLevelText,
  pathStatusText,
  pickCurrentPath,
  producerStatusText,
  summarizeRequirement,
  summarizeText,
  weakPointsPreview,
} from '../utils/dashboard'
import { setCurrentPathId } from '../utils/pathSession'
import { setCurrentProducerTaskId } from '../utils/producerSession'
import { setCurrentEvaluationId } from '../utils/evaluationSession'

const router = useRouter()

const loading = ref(false)
const user = ref(null)
const profile = ref(null)
const pathItems = ref([])
const pathTotal = ref(0)
const evaluationItems = ref([])
const evaluationTotal = ref(0)
const producerItems = ref([])
const producerTotal = ref(0)

const userError = ref('')
const profileError = ref('')
const pathsError = ref('')
const evaluationsError = ref('')
const tasksError = ref('')

const resourcesLoading = ref(false)
const resourcesError = ref('')
const recommendedResources = ref([])

const isLoggedIn = computed(() => userStore.state.isLoggedIn)

const displayName = computed(() => {
  return user.value?.nickname
    || user.value?.username
    || userStore.state.nickname
    || userStore.state.username
    || '学习者'
})

const hasProfile = computed(() => hasProfileSummary(profile.value))

const weakPointsLabel = computed(() => {
  const points = weakPointsPreview(profile.value?.weak_points, 3)
  return points.length ? points.join('、') : '未设置'
})

const statistics = computed(() => buildStatistics(
  pathItems.value,
  pathTotal.value,
  evaluationItems.value,
  evaluationTotal.value,
  producerTotal.value,
))

const currentPath = computed(() => pickCurrentPath(pathItems.value))
const latestEvaluation = computed(() => evaluationItems.value[0] || null)
const latestTask = computed(() => producerItems.value[0] || null)

function resetState() {
  user.value = null
  profile.value = null
  pathItems.value = []
  pathTotal.value = 0
  evaluationItems.value = []
  evaluationTotal.value = 0
  producerItems.value = []
  producerTotal.value = 0
  userError.value = ''
  profileError.value = ''
  pathsError.value = ''
  evaluationsError.value = ''
  tasksError.value = ''
  resourcesError.value = ''
  recommendedResources.value = []
  loading.value = false
  resourcesLoading.value = false
}

function formatResourceItem(item) {
  const views = Number(item.views)
  const likes = Number(item.likes)
  const stats = []
  if (Number.isFinite(views)) stats.push(`浏览 ${views}`)
  if (Number.isFinite(likes)) stats.push(`点赞 ${likes}`)

  return {
    id: item.id,
    title: item.title || '未命名资源',
    typeLabel: item.category || item.type || item.resource_type || '资源',
    description: summarizeText(item.description || item.summary || '', 90),
    detailUrl: item.detail_url || '',
    metaStats: stats.join(' · '),
  }
}

async function loadRecommendedResources(currentProfile) {
  resourcesLoading.value = true
  resourcesError.value = ''
  try {
    const query = buildResourceQuery(currentProfile)
    const response = await getResourceList({
      type: 'all',
      keyword: query.keyword || undefined,
      sort: query.sort,
    })
    const items = Array.isArray(response?.items) ? response.items : []
    recommendedResources.value = items.slice(0, 3).map(formatResourceItem)
  } catch (error) {
    resourcesError.value = `推荐资源加载失败：${error.message || '请稍后重试'}`
    recommendedResources.value = []
  } finally {
    resourcesLoading.value = false
  }
}

async function loadDashboard() {
  if (!isLoggedIn.value) return

  loading.value = true
  userError.value = ''
  profileError.value = ''
  pathsError.value = ''
  evaluationsError.value = ''
  tasksError.value = ''

  try {
    const data = await fetchDashboardData()

    user.value = data.user
    profile.value = data.profile
    pathItems.value = data.paths.items
    pathTotal.value = data.paths.total
    evaluationItems.value = data.evaluations.items
    evaluationTotal.value = data.evaluations.total
    producerItems.value = data.tasks.items
    producerTotal.value = data.tasks.total

    userError.value = data.errors.user || ''
    profileError.value = data.errors.profile || ''
    pathsError.value = data.errors.paths || ''
    evaluationsError.value = data.errors.evaluations || ''
    tasksError.value = data.errors.tasks || ''
  } catch (error) {
    userError.value = error.message || '学习概览加载失败'
  } finally {
    loading.value = false
  }

  await loadRecommendedResources(profile.value)
}

function openCurrentPath() {
  if (!currentPath.value) {
    router.push({ name: 'learningPath' })
    return
  }
  setCurrentPathId(currentPath.value.pathId)
  router.push({ name: 'learningPath' })
}

function openLatestEvaluation() {
  if (!latestEvaluation.value) {
    router.push({ name: 'evaluation' })
    return
  }
  setCurrentEvaluationId(latestEvaluation.value.evaluation_id)
  router.push({ name: 'evaluation' })
}

function openLatestTask() {
  if (!latestTask.value) {
    router.push({ name: 'multiAgentResource' })
    return
  }
  setCurrentProducerTaskId(latestTask.value.task_id)
  router.push({ name: 'multiAgentResource' })
}

function openResource() {
  router.push({ name: 'resources' })
}

watch(isLoggedIn, (loggedIn) => {
  if (loggedIn) {
    loadDashboard()
  } else {
    resetState()
  }
})

onMounted(() => {
  if (isLoggedIn.value) {
    loadDashboard()
  }
})
</script>

<style scoped>
.home-dashboard {
  width: 100%;
  padding: 48px 0;
  background: #f7f8fa;
  box-sizing: border-box;
}

.dashboard-shell {
  width: calc(100% - 48px);
  max-width: 1200px;
  margin: 0 auto;
  display: grid;
  gap: 24px;
  box-sizing: border-box;
}

.guest-shell {
  padding-top: 0;
}

.guest-card,
.dash-card,
.loading-box {
  border-radius: 18px;
  background: #ffffff;
  border: 1px solid #e5e7eb;
  box-shadow: var(--shadow-md);
}

.guest-card,
.dash-card,
.loading-box {
  padding: 24px;
}

.guest-card {
  text-align: center;
}

.guest-card h2,
.welcome-card h2,
.card-head h3 {
  margin: 0;
  color: #111827;
  font-weight: 800;
}

.guest-card h2 {
  font-size: clamp(24px, 3vw, 32px);
  line-height: 1.3;
}

.welcome-card h2 {
  font-size: clamp(26px, 3.2vw, 34px);
  margin-bottom: 14px;
  line-height: 1.25;
}

.card-head h3 {
  font-size: clamp(20px, 2.4vw, 24px);
  line-height: 1.3;
}

.eyebrow {
  margin: 0 0 10px;
  color: #111827;
  font-size: 13px;
  font-weight: 700;
  letter-spacing: 0.08em;
}

.guest-desc {
  margin: 14px auto 24px;
  max-width: 640px;
  color: #4b5563;
  font-size: 16px;
  line-height: 1.8;
}

.guest-actions {
  display: flex;
  justify-content: center;
  gap: 14px;
  flex-wrap: wrap;
}

.primary-btn,
.ghost-btn,
.link-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-height: 44px;
  padding: 0 20px;
  border-radius: 14px;
  font-size: 15px;
  font-weight: 700;
  text-decoration: none;
  cursor: pointer;
  transition: background 0.2s ease, border-color 0.2s ease, box-shadow 0.2s ease;
}

.primary-btn {
  border: none;
  background: #111827;
  color: #ffffff;
}

.ghost-btn,
.link-btn {
  border: 1px solid #e5e7eb;
  background: #ffffff;
  color: #111827;
}

.primary-btn:hover,
.ghost-btn:hover,
.link-btn:hover {
  box-shadow: 0 8px 20px rgba(0, 0, 0, 0.08);
}

.card-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 18px;
}

.welcome-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}

.welcome-meta span,
.meta {
  display: inline-flex;
  align-items: center;
  padding: 8px 12px;
  border-radius: 999px;
  background: #f3f4f6;
  color: #374151;
  font-size: 14px;
  font-weight: 600;
}

.section-error {
  margin: 0 0 14px;
  padding: 12px 14px;
  border-radius: 12px;
  background: #fef2f2;
  border: 1px solid #fecaca;
  color: #991b1b;
  font-size: 14px;
  font-weight: 600;
}

.empty-box {
  padding: 20px;
  border-radius: 16px;
  background: #f9fafb;
  border: 1px dashed #d1d5db;
  color: #374151;
  font-size: 15px;
  font-weight: 600;
  line-height: 1.75;
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
}

.info-item {
  padding: 18px;
  border-radius: 16px;
  background: #f9fafb;
  border: 1px solid #e5e7eb;
}

.info-item.full {
  grid-column: 1 / -1;
}

.info-item label {
  display: block;
  margin-bottom: 8px;
  color: #111827;
  font-size: 13px;
  font-weight: 700;
}

.info-item p {
  margin: 0;
  color: #374151;
  font-size: 15px;
  line-height: 1.75;
}

.summary-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 20px;
}

.clickable-card {
  cursor: pointer;
  transition: border-color 0.2s ease, box-shadow 0.2s ease;
}

.clickable-card:hover {
  border-color: #111827;
  box-shadow: 0 14px 28px rgba(0, 0, 0, 0.08);
}

.record-body strong {
  display: block;
  margin-bottom: 10px;
  color: #111827;
  font-size: 18px;
  line-height: 1.4;
}

.record-body p {
  margin: 0 0 10px;
  color: #4b5563;
  font-size: 15px;
  line-height: 1.65;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(6, minmax(0, 1fr));
  gap: 16px;
}

.stat-item {
  padding: 20px;
  border-radius: 16px;
  background: #f9fafb;
  border: 1px solid #e5e7eb;
}

.stat-item span {
  display: block;
  margin-bottom: 10px;
  color: #6b7280;
  font-size: 13px;
  font-weight: 700;
}

.stat-item strong {
  color: #111827;
  font-size: clamp(24px, 3vw, 30px);
  line-height: 1;
}

.progress-row {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-top: 12px;
}

.progress-track {
  flex: 1;
  min-width: 0;
  height: 10px;
  border-radius: 999px;
  background: #e5e7eb;
  overflow: hidden;
}

.progress-track i {
  display: block;
  height: 100%;
  background: #111827;
  border-radius: inherit;
}

.progress-row span {
  flex-shrink: 0;
  color: #111827;
  font-size: 13px;
  font-weight: 700;
}

.resource-list {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 16px;
}

.resource-item {
  width: 100%;
  padding: 20px;
  border-radius: 16px;
  background: #f9fafb;
  border: 1px solid #e5e7eb;
  text-align: left;
  font: inherit;
  color: inherit;
  cursor: pointer;
  transition: border-color 0.2s ease, box-shadow 0.2s ease;
  box-sizing: border-box;
}

.resource-item:hover {
  border-color: #111827;
  box-shadow: 0 10px 24px rgba(0, 0, 0, 0.06);
}

.resource-item strong {
  display: block;
  margin-bottom: 8px;
  color: #111827;
  font-size: 16px;
  line-height: 1.4;
}

.resource-item p {
  margin: 8px 0 0;
  color: #4b5563;
  font-size: 14px;
  line-height: 1.65;
}

.inline-link {
  margin-left: 6px;
  color: #111827;
  font-weight: 700;
  text-decoration: underline;
}

.ellipsis {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.ellipsis-2 {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.loading-box {
  text-align: center;
  color: #374151;
  font-size: 16px;
  font-weight: 700;
}

@media (max-width: 1199px) {
  .dashboard-shell {
    width: calc(100% - 48px);
  }

  .summary-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .stats-grid {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }

  .resource-list {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 767px) {
  .home-dashboard {
    padding: 32px 0;
  }

  .dashboard-shell {
    width: calc(100% - 32px);
    gap: 20px;
  }

  .guest-card,
  .dash-card,
  .loading-box {
    padding: 20px;
  }

  .info-grid,
  .summary-grid,
  .stats-grid,
  .resource-list {
    grid-template-columns: 1fr;
  }

  .card-head {
    flex-direction: column;
    align-items: stretch;
  }

  .ghost-btn,
  .link-btn,
  .primary-btn {
    width: 100%;
  }
}
</style>
