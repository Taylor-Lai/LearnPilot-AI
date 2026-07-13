<template>
  <div class="profile-page">
    <Header />

    <div class="back-wrap">
      <RouterLink to="/" class="ui-back-link">
        ← 返回首页
      </RouterLink>
    </div>

    <main class="profile-container">
      <section class="profile-card">
        <div class="section-head">
          <div>
            <p class="eyebrow">PERSONAL CENTER</p>
            <h2>个人中心</h2>
          </div>

          <button class="edit-btn" @click="toggleEdit">
            {{ isEditing ? '取消编辑' : '编辑资料' }}
          </button>
        </div>

        <div class="profile-top">
          <div class="avatar-area">
            <div class="avatar-box">
              <img
                v-if="form.avatar"
                :src="form.avatar"
                alt="avatar"
                class="avatar-img"
              />
              <span v-else class="avatar-text">
                {{ avatarText }}
              </span>
            </div>

            <label v-if="isEditing" class="avatar-upload-btn">
              更换头像
              <input
                type="file"
                accept="image/*"
                class="hidden-input"
                @change="handleAvatarChange"
              />
            </label>
          </div>

          <div class="info-grid">
            <div class="info-item">
              <label>昵称</label>
              <input
                v-if="isEditing"
                v-model="form.nickname"
                class="info-input"
                placeholder="请输入昵称"
              />
              <div v-else class="info-value">
                {{ form.nickname || '未设置' }}
              </div>
            </div>

            <div class="info-item">
              <label>用户名</label>
              <div class="info-value">
                {{ form.username || '未设置' }}
              </div>
            </div>

            <div class="info-item">
              <label>邮箱</label>
              <div class="info-value">
                {{ form.email || '未设置' }}
              </div>
            </div>

            <div class="info-item">
              <label>性别</label>
              <select
                v-if="isEditing"
                v-model="form.gender"
                class="info-input"
              >
                <option value="">未设置</option>
                <option value="男">男</option>
                <option value="女">女</option>
              </select>
              <div v-else class="info-value">
                {{ form.gender || '未设置' }}
              </div>
            </div>

            <div class="info-item">
              <label>手机号</label>
              <input
                v-if="isEditing"
                v-model="form.phone"
                class="info-input"
                placeholder="请输入手机号"
              />
              <div v-else class="info-value">
                {{ form.phone || '未设置' }}
              </div>
            </div>

            <div class="info-item">
              <label>角色</label>
              <div class="info-value">
                {{ roleText }}
              </div>
            </div>
          </div>
        </div>

        <div v-if="isEditing" class="save-row">
          <button class="save-btn" :disabled="saving" @click="saveProfile">
            {{ saving ? '保存中...' : '保存修改' }}
          </button>
        </div>
      </section>

      <section class="summary-card">
        <div class="section-head">
          <div>
            <p class="eyebrow">LEARNING PROFILE</p>
            <h2>学习画像摘要</h2>
          </div>
          <RouterLink :to="{ name: 'profileBuilder' }" class="action-btn link-btn">
            {{ hasProfileSummary ? '查看或更新画像' : '构建学习画像' }}
          </RouterLink>
        </div>

        <div v-if="profileSummaryLoading" class="empty-box">正在加载学习画像...</div>
        <p v-else-if="profileSummaryError" class="section-error">{{ profileSummaryError }}</p>
        <div v-else-if="!hasProfileSummary" class="empty-box">
          尚未构建学习画像，点击右上角开始对话式画像构建。
        </div>
        <div v-else class="summary-grid">
          <div class="summary-item">
            <label>专业</label>
            <div class="summary-value ellipsis">{{ profileSummary.major || '未设置' }}</div>
          </div>
          <div class="summary-item">
            <label>年级</label>
            <div class="summary-value">{{ profileSummary.grade || '未设置' }}</div>
          </div>
          <div class="summary-item">
            <label>当前课程</label>
            <div class="summary-value ellipsis">{{ profileSummary.course || '未设置' }}</div>
          </div>
          <div class="summary-item full-width">
            <label>学习目标</label>
            <div class="summary-value ellipsis-2">{{ profileSummary.goal || '未设置' }}</div>
          </div>
          <div class="summary-item full-width">
            <label>薄弱知识点</label>
            <div class="summary-value ellipsis-2">{{ weakPointsText }}</div>
          </div>
          <div class="summary-item">
            <label>学习偏好</label>
            <div class="summary-value">{{ profileSummary.preference || '未设置' }}</div>
          </div>
          <div class="summary-item">
            <label>认知风格</label>
            <div class="summary-value">{{ profileSummary.cognitive_style || '未设置' }}</div>
          </div>
          <div class="summary-item">
            <label>基础水平</label>
            <div class="summary-value">{{ knowledgeLevelTextValue }}</div>
          </div>
        </div>
      </section>

      <section class="stats-card">
        <div class="section-head">
          <div>
            <p class="eyebrow">STATISTICS</p>
            <h2>学习统计</h2>
          </div>
        </div>

        <div v-if="statsLoading" class="empty-box">正在汇总学习统计...</div>
        <p v-else-if="statsError" class="section-error">{{ statsError }}</p>
        <div v-else class="stats-grid">
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

      <section class="history-card">
        <div class="section-head">
          <div>
            <p class="eyebrow">RECENT PATHS</p>
            <h2>最近学习路径</h2>
          </div>
          <RouterLink :to="{ name: 'learningPath' }" class="action-btn link-btn">前往路径页</RouterLink>
        </div>

        <div v-if="pathsLoading" class="empty-box">正在加载学习路径...</div>
        <p v-else-if="pathsError" class="section-error">{{ pathsError }}</p>
        <div v-else-if="!recentPaths.length" class="empty-box">
          暂无学习路径，
          <RouterLink :to="{ name: 'learningPath' }" class="inline-link">去生成路径</RouterLink>
        </div>
        <div v-else class="record-list">
          <button
            v-for="item in recentPaths"
            :key="item.pathId"
            type="button"
            class="record-item clickable"
            @click="openPath(item)"
          >
            <div class="record-main">
              <div class="record-title ellipsis">{{ item.title }}</div>
              <div class="record-meta ellipsis">{{ item.goal }}</div>
              <div class="record-time">{{ formatDate(item.createdAt) }}</div>
              <div class="progress-row">
                <div class="progress-track">
                  <i :style="{ width: `${item.progress}%` }"></i>
                </div>
                <span>{{ item.progress }}%</span>
              </div>
            </div>
            <span class="record-status">{{ pathStatusText(item.status) }}</span>
          </button>
        </div>
      </section>

      <section class="history-card">
        <div class="section-head">
          <div>
            <p class="eyebrow">RECENT EVALUATIONS</p>
            <h2>最近学习评测</h2>
          </div>
          <RouterLink :to="{ name: 'evaluation' }" class="action-btn link-btn">前往评测页</RouterLink>
        </div>

        <div v-if="evaluationsLoading" class="empty-box">正在加载评测记录...</div>
        <p v-else-if="evaluationsError" class="section-error">{{ evaluationsError }}</p>
        <div v-else-if="!recentEvaluations.length" class="empty-box">
          暂无评测记录，
          <RouterLink :to="{ name: 'evaluation' }" class="inline-link">去开始评测</RouterLink>
        </div>
        <div v-else class="record-list">
          <button
            v-for="item in recentEvaluations"
            :key="item.evaluation_id"
            type="button"
            class="record-item clickable"
            @click="openEvaluation(item)"
          >
            <div class="record-main">
              <div class="record-title">评测 #{{ item.evaluation_id }}</div>
              <div class="record-meta ellipsis-2">{{ item.feedback }}</div>
              <div class="record-time">{{ formatDate(item.created_at) }}</div>
            </div>
            <div class="record-side">
              <span class="record-score">分数 {{ item.score ?? '-' }}</span>
              <span class="record-status">{{ formatAccuracy(item.accuracy) }}</span>
            </div>
          </button>
        </div>
      </section>

      <section class="history-card">
        <div class="section-head">
          <div>
            <p class="eyebrow">RECENT TASKS</p>
            <h2>最近资源生成任务</h2>
          </div>
          <RouterLink :to="{ name: 'multiAgentResource' }" class="action-btn link-btn">前往生成页</RouterLink>
        </div>

        <div v-if="producerLoading" class="empty-box">正在加载生成任务...</div>
        <p v-else-if="producerError" class="section-error">{{ producerError }}</p>
        <div v-else-if="!recentProducerTasks.length" class="empty-box">
          暂无生成任务，
          <RouterLink :to="{ name: 'multiAgentResource' }" class="inline-link">去创建任务</RouterLink>
        </div>
        <div v-else class="record-list">
          <button
            v-for="item in recentProducerTasks"
            :key="item.task_id"
            type="button"
            class="record-item clickable"
            @click="openProducerTask(item)"
          >
            <div class="record-main">
              <div class="record-title ellipsis">{{ item.topic }}</div>
              <div class="record-meta ellipsis">{{ summarizeRequirement(item.requirement) }}</div>
              <div class="record-time">{{ formatDate(item.created_at) }}</div>
              <div class="progress-row">
                <div class="progress-track">
                  <i :style="{ width: `${item.progress || 0}%` }"></i>
                </div>
                <span>{{ item.progress || 0 }}%</span>
              </div>
            </div>
            <span class="record-status">{{ producerStatusText(item.status) }}</span>
          </button>
        </div>
      </section>
    </main>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { RouterLink, useRouter } from 'vue-router'
import Header from '../components/AppHeader.vue'
import { getUserInfo, updateUserInfo } from '../api/auth'
import { getCurrentProfile, getUserPathList } from '../api/path'
import { getEvaluationHistory } from '../api/evaluation'
import { listTasks } from '../api/producer'
import { userStore } from '../stores/userStore'
import { adaptPathListResponse } from '../utils/path'
import { setCurrentPathId } from '../utils/pathSession'
import { setCurrentProducerTaskId } from '../utils/producerSession'
import { setCurrentEvaluationId } from '../utils/evaluationSession'
import {
  buildStatistics,
  formatAccuracy,
  formatDate,
  knowledgeLevelText,
  parseProfileSummary,
  pathStatusText,
  producerStatusText,
  summarizeRequirement,
} from '../utils/dashboard'

const router = useRouter()
const isEditing = ref(false)
const saving = ref(false)
const isLoading = ref(true)

const form = reactive({
  username: '',
  nickname: '',
  email: '',
  gender: '',
  phone: '',
  role: '',
  avatar: '',
})

const oldForm = reactive({
  username: '',
  nickname: '',
  email: '',
  gender: '',
  phone: '',
  role: '',
  avatar: '',
})

const profileSummary = reactive({
  major: '',
  grade: '',
  course: '',
  goal: '',
  weak_points: [],
  preference: '',
  cognitive_style: '',
  knowledge_level: '',
})

const profileSummaryLoading = ref(false)
const profileSummaryError = ref('')
const pathsLoading = ref(false)
const pathsError = ref('')
const evaluationsLoading = ref(false)
const evaluationsError = ref('')
const producerLoading = ref(false)
const producerError = ref('')

const pathItems = ref([])
const pathTotal = ref(0)
const evaluationItems = ref([])
const evaluationTotal = ref(0)
const producerItems = ref([])
const producerTotal = ref(0)

const avatarText = computed(() => {
  const name = form.nickname || form.username || 'U'
  return name.slice(0, 1).toUpperCase()
})

const roleText = computed(() => {
  if (form.role === 'ADMIN') return '管理员'
  if (form.role === 'USER') return '普通用户'
  return form.role || '普通用户'
})

const hasProfileSummary = computed(() => {
  const weakPoints = profileSummary.weak_points
  return !!(
    profileSummary.major
    || profileSummary.course
    || profileSummary.goal
    || (Array.isArray(weakPoints) && weakPoints.length)
  )
})

const weakPointsText = computed(() => {
  const points = profileSummary.weak_points
  if (!Array.isArray(points) || !points.length) return '未设置'
  return points.map((item) => (typeof item === 'string' ? item : item.name || item.label || '')).filter(Boolean).join('、')
})

const knowledgeLevelTextValue = computed(() => knowledgeLevelText(profileSummary.knowledge_level))

const statsLoading = computed(() => pathsLoading.value || evaluationsLoading.value || producerLoading.value)

const statsError = computed(() => {
  const errors = [pathsError.value, evaluationsError.value, producerError.value].filter(Boolean)
  if (!errors.length) return ''
  if (errors.length === 3) return '学习统计数据暂时无法加载，请稍后刷新。'
  return ''
})

const statistics = computed(() => buildStatistics(
  pathItems.value,
  pathTotal.value,
  evaluationItems.value,
  evaluationTotal.value,
  producerTotal.value,
))

const recentPaths = computed(() => pathItems.value.slice(0, 5))
const recentEvaluations = computed(() => evaluationItems.value.slice(0, 5))
const recentProducerTasks = computed(() => producerItems.value.slice(0, 5))

function openPath(item) {
  const pathId = item.pathId || item.path_id
  if (!pathId) return
  setCurrentPathId(pathId)
  router.push({ name: 'learningPath' })
}

function openEvaluation(item) {
  if (!item?.evaluation_id) return
  setCurrentEvaluationId(item.evaluation_id)
  router.push({ name: 'evaluation' })
}

function openProducerTask(item) {
  if (!item?.task_id) return
  setCurrentProducerTaskId(item.task_id)
  router.push({ name: 'multiAgentResource' })
}

const syncOldForm = () => {
  Object.assign(oldForm, {
    username: form.username,
    nickname: form.nickname,
    email: form.email,
    gender: form.gender,
    phone: form.phone,
    role: form.role,
    avatar: form.avatar,
  })
}

const restoreOldForm = () => {
  Object.assign(form, {
    username: oldForm.username,
    nickname: oldForm.nickname,
    email: oldForm.email,
    gender: oldForm.gender,
    phone: oldForm.phone,
    role: oldForm.role,
    avatar: oldForm.avatar,
  })
}

function showMessage(message, isError = false) {
  const msgDiv = document.createElement('div')
  msgDiv.textContent = message
  msgDiv.style.cssText = `
    position: fixed;
    bottom: 20px;
    left: 50%;
    transform: translateX(-50%);
    padding: 10px 20px;
    background: ${isError ? '#ef4444' : '#10b981'};
    color: white;
    border-radius: 8px;
    font-size: 14px;
    z-index: 10000;
    animation: fadeOut 2s ease forwards;
  `
  document.body.appendChild(msgDiv)
  setTimeout(() => msgDiv.remove(), 2000)
}

function applyProfileSummary(raw = {}) {
  Object.assign(profileSummary, parseProfileSummary(raw))
}

async function fetchProfileSummary() {
  profileSummaryLoading.value = true
  profileSummaryError.value = ''
  try {
    const response = await getCurrentProfile()
    applyProfileSummary(response)
  } catch (error) {
    profileSummaryError.value = `画像加载失败：${error.message || '请稍后重试'}`
  } finally {
    profileSummaryLoading.value = false
  }
}

async function fetchPaths() {
  pathsLoading.value = true
  pathsError.value = ''
  try {
    const response = await getUserPathList()
    const adapted = adaptPathListResponse(response)
    pathItems.value = adapted.items
    pathTotal.value = adapted.total
  } catch (error) {
    pathsError.value = `路径加载失败：${error.message || '请稍后重试'}`
    pathItems.value = []
    pathTotal.value = 0
  } finally {
    pathsLoading.value = false
  }
}

async function fetchEvaluations() {
  evaluationsLoading.value = true
  evaluationsError.value = ''
  try {
    const response = await getEvaluationHistory()
    const items = response?.items || []
    evaluationItems.value = items
    evaluationTotal.value = Number(response?.total) || items.length
  } catch (error) {
    evaluationsError.value = `评测加载失败：${error.message || '请稍后重试'}`
    evaluationItems.value = []
    evaluationTotal.value = 0
  } finally {
    evaluationsLoading.value = false
  }
}

async function fetchProducerTasks() {
  producerLoading.value = true
  producerError.value = ''
  try {
    const response = await listTasks({ limit: 20 })
    const items = response?.items || []
    producerItems.value = items
    producerTotal.value = Number(response?.total) || items.length
  } catch (error) {
    producerError.value = `生成任务加载失败：${error.message || '请稍后重试'}`
    producerItems.value = []
    producerTotal.value = 0
  } finally {
    producerLoading.value = false
  }
}

const loadUserInfo = async () => {
  const token = localStorage.getItem('token')
  if (!token) {
    showMessage('请先登录', true)
    setTimeout(() => {
      router.push('/login')
    }, 1000)
    return
  }

  if (userStore.state.isLoggedIn) {
    form.username = userStore.state.username || ''
    form.nickname = userStore.state.nickname || ''
    form.email = userStore.state.email || ''
    form.role = userStore.state.userRole || 'USER'
    form.avatar = userStore.state.avatar || ''
  } else {
    try {
      const userInfoStr = localStorage.getItem('userInfo')
      if (userInfoStr) {
        const userInfo = JSON.parse(userInfoStr)
        form.username = userInfo.username || ''
        form.nickname = userInfo.nickname || ''
        form.email = userInfo.email || ''
        form.role = userInfo.role || 'USER'
        form.avatar = userInfo.avatar || ''
      }
    } catch (error) {
      console.error('读取 localStorage 失败:', error)
    }
  }

  try {
    isLoading.value = true
    const data = await getUserInfo()

    form.username = data.username || form.username
    form.nickname = data.nickname || form.nickname
    form.email = data.email || form.email
    form.gender = data.gender || ''
    form.phone = data.phone || ''
    form.role = data.role || form.role || 'USER'
    form.avatar = data.avatar || form.avatar

    syncOldForm()

    const tokenValue = localStorage.getItem('token')
    if (tokenValue) {
      userStore.updateUserInfo({
        username: form.username,
        nickname: form.nickname,
        email: form.email,
        role: form.role,
        avatar: form.avatar,
        token: tokenValue,
      })
    }

    localStorage.setItem(
      'userInfo',
      JSON.stringify({
        username: form.username,
        nickname: form.nickname,
        email: form.email,
        gender: form.gender,
        phone: form.phone,
        role: form.role,
        avatar: form.avatar,
      }),
    )

    window.dispatchEvent(new Event('userInfoUpdated'))
  } catch (error) {
    console.error('获取用户信息失败:', error)
    if (!form.username && !form.nickname) {
      showMessage('获取用户信息失败，请刷新重试', true)
    }
  } finally {
    isLoading.value = false
  }
}

const toggleEdit = () => {
  if (isEditing.value) {
    restoreOldForm()
    isEditing.value = false
  } else {
    syncOldForm()
    isEditing.value = true
  }
}

const saveProfile = async () => {
  try {
    saving.value = true

    const data = await updateUserInfo({
      nickname: form.nickname,
      gender: form.gender,
      phone: form.phone,
      avatar: form.avatar,
    })

    form.nickname = data.nickname ?? form.nickname
    form.gender = data.gender ?? form.gender
    form.phone = data.phone ?? form.phone
    form.avatar = data.avatar ?? form.avatar

    syncOldForm()

    const token = localStorage.getItem('token')
    if (token) {
      userStore.updateUserInfo({
        username: form.username,
        nickname: form.nickname,
        email: form.email,
        role: form.role,
        avatar: form.avatar,
        token,
      })
    }

    localStorage.setItem(
      'userInfo',
      JSON.stringify({
        username: form.username,
        nickname: form.nickname,
        email: form.email,
        gender: form.gender,
        phone: form.phone,
        role: form.role,
        avatar: form.avatar,
      }),
    )

    window.dispatchEvent(new Event('userInfoUpdated'))
    isEditing.value = false
    showMessage('个人信息已保存')
  } catch (error) {
    console.error('保存失败:', error)
    showMessage(error.message || '保存失败', true)
  } finally {
    saving.value = false
  }
}

const handleAvatarChange = (event) => {
  const file = event.target.files?.[0]
  if (!file) return

  if (file.size > 2 * 1024 * 1024) {
    showMessage('图片大小不能超过 2MB', true)
    return
  }

  const reader = new FileReader()
  reader.onload = () => {
    form.avatar = reader.result
  }
  reader.readAsDataURL(file)
}

onMounted(async () => {
  await Promise.allSettled([
    loadUserInfo(),
    fetchProfileSummary(),
    fetchPaths(),
    fetchEvaluations(),
    fetchProducerTasks(),
  ])
})
</script>

<style scoped>
/* 添加动画 */
@keyframes fadeOut {
  0% {
    opacity: 0;
    transform: translateX(-50%) translateY(10px);
  }
  15% {
    opacity: 1;
    transform: translateX(-50%) translateY(0);
  }
  85% {
    opacity: 1;
    transform: translateX(-50%) translateY(0);
  }
  100% {
    opacity: 0;
    transform: translateX(-50%) translateY(-10px);
  }
}

.profile-page {
  min-height: 100vh;
  background: #f7f8fa;
  color: #111827;
}

.back-wrap {
  width: min(94%, 1280px);
  margin: 24px auto 0;
}

.profile-container {
  width: min(94%, 1280px);
  margin: 0 auto;
  padding: 24px 0 60px;
  display: grid;
  gap: 24px;
}

.profile-card,
.history-card,
.summary-card,
.stats-card {
  position: relative;
  overflow: hidden;
  padding: 34px;
  border-radius: 18px;
  background: #ffffff;
  border: 1px solid #e5e7eb;
  box-shadow: var(--shadow-md);
}

.section-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 18px;
  margin-bottom: 26px;
}

.eyebrow {
  margin: 0 0 10px;
  color: #111827;
  font-size: 13px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

h2 {
  margin: 0;
  color: #111827;
  font-size: 28px;
  font-weight: 800;
  line-height: 1.25;
}

.history-head-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.link-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  text-decoration: none;
}

.section-error {
  margin: 0;
  padding: 12px 14px;
  border-radius: 14px;
  background: #fef2f2;
  border: 1px solid #fecaca;
  color: #991b1b;
  font-size: 14px;
  font-weight: 600;
}

.summary-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px;
}

.summary-item {
  padding: 16px;
  border-radius: 16px;
  background: #f9fafb;
  border: 1px solid #e5e7eb;
}

.summary-item.full-width {
  grid-column: 1 / -1;
}

.summary-item label {
  display: block;
  margin-bottom: 8px;
  color: #111827;
  font-size: 13px;
  font-weight: 700;
}

.summary-value {
  color: #111827;
  font-size: 15px;
  font-weight: 600;
  line-height: 1.7;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 14px;
}

.stat-item {
  padding: 18px;
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
  font-size: 28px;
  line-height: 1;
}

.record-list {
  display: grid;
  gap: 14px;
}

.record-item {
  width: 100%;
  display: grid;
  grid-template-columns: 1fr auto;
  align-items: center;
  gap: 20px;
  padding: 18px 20px;
  border-radius: 18px;
  background: #f9fafb;
  border: 1px solid #e5e7eb;
  text-align: left;
  font: inherit;
  color: inherit;
}

.record-item.clickable {
  cursor: pointer;
  transition: all 0.2s ease;
}

.record-item.clickable:hover {
  transform: translateY(-2px);
  border-color: #111827;
  box-shadow: 0 10px 24px rgba(0, 0, 0, 0.06);
}

.record-main {
  min-width: 0;
}

.record-title {
  margin-bottom: 6px;
  color: #111827;
  font-size: 16px;
  font-weight: 800;
}

.record-meta {
  margin-bottom: 6px;
  color: #4b5563;
  font-size: 13px;
  line-height: 1.6;
}

.record-time {
  color: #6b7280;
  font-size: 12px;
}

.record-side {
  display: grid;
  gap: 8px;
  justify-items: end;
}

.record-score {
  color: #111827;
  font-size: 13px;
  font-weight: 700;
}

.record-status {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 86px;
  height: 32px;
  padding: 0 12px;
  border-radius: 999px;
  background: #f3f4f6;
  color: #111827;
  font-size: 13px;
  font-weight: 800;
}

.progress-row {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-top: 10px;
}

.progress-track {
  flex: 1;
  height: 8px;
  border-radius: 999px;
  background: #e5e7eb;
  overflow: hidden;
}

.progress-track i {
  display: block;
  height: 100%;
  border-radius: inherit;
  background: #111827;
}

.progress-row span {
  min-width: 42px;
  color: #111827;
  font-size: 12px;
  font-weight: 700;
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

.inline-link {
  color: #111827;
  font-weight: 700;
  text-decoration: underline;
}

.edit-btn,
.save-btn,
.action-btn,
.item-delete-btn {
  height: 42px;
  padding: 0 18px;
  border: none;
  border-radius: 14px;
  background: #111827;
  color: #ffffff;
  cursor: pointer;
  font-size: 14px;
  font-weight: 700;
  text-decoration: none;
  transition: all 0.2s ease;
}

.edit-btn:hover,
.save-btn:hover:not(:disabled),
.action-btn:hover:not(:disabled),
.item-delete-btn:hover {
  transform: translateY(-2px);
  background: #1f2937;
  box-shadow: 0 12px 24px rgba(0, 0, 0, 0.15);
}

.action-btn:disabled,
.save-btn:disabled {
  opacity: 0.45;
  cursor: not-allowed;
  transform: none;
  box-shadow: none;
}

.danger-btn,
.danger-solid-btn,
.item-delete-btn {
  background: #ef6464;
}

.danger-btn:hover:not(:disabled),
.danger-solid-btn:hover:not(:disabled),
.item-delete-btn:hover {
  background: #dc5252;
  box-shadow: 0 12px 24px rgba(239, 100, 100, 0.22);
}

.profile-top {
  display: grid;
  grid-template-columns: 220px 1fr;
  gap: 30px;
  align-items: start;
}

.avatar-area {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 18px;
}

.avatar-box {
  width: 142px;
  height: 142px;
  border-radius: 50%;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #ffffff;
  border: 1px solid #e5e7eb;
  box-shadow: var(--shadow-md);
}

.avatar-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.avatar-text {
  color: #111827;
  font-size: 46px;
  font-weight: 900;
}

.avatar-upload-btn {
  padding: 10px 14px;
  border-radius: 14px;
  background: #f9fafb;
  color: #111827;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  text-align: center;
  font-size: 13px;
  font-weight: 700;
  cursor: pointer;
  border: 1px solid #e5e7eb;
  white-space: nowrap;
  transition: all 0.2s ease;
}

.avatar-upload-btn:hover {
  transform: translateY(-2px);
  background: #f1f5f9;
}

.hidden-input {
  display: none;
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 18px;
}

.info-item {
  min-width: 0;
  padding: 18px;
  border-radius: 18px;
  background: #f9fafb;
  border: 1px solid #e5e7eb;
}

.info-item label {
  display: block;
  margin-bottom: 8px;
  color: #111827;
  font-size: 13px;
  font-weight: 700;
}

.info-value {
  color: #111827;
  font-size: 15px;
  font-weight: 600;
  line-height: 1.7;
  word-break: break-all;
}

.info-input {
  width: 100%;
  height: 42px;
  padding: 0 12px;
  border: 1px solid #e5e7eb;
  border-radius: 14px;
  background: #ffffff;
  color: #111827;
  font-size: 14px;
  outline: none;
}

.info-input:focus {
  border-color: #111827;
  box-shadow: 0 0 0 3px rgba(0, 0, 0, 0.08);
}

.save-row {
  display: flex;
  justify-content: flex-end;
  margin-top: 24px;
}

.empty-box {
  min-height: 180px;
  margin-top: 8px;
  border-radius: 18px;
  border: 1px dashed #cbd5e1;
  background: #ffffff;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #111827;
  font-size: 15px;
  font-weight: 700;
}

@media (max-width: 900px) {
  .back-wrap,
  .profile-container {
    width: min(94%, 760px);
  }

  .profile-container {
    padding: 24px 0 48px;
  }

  .profile-card,
  .history-card,
  .summary-card,
  .stats-card {
    padding: 24px;
    border-radius: 18px;
  }

  .profile-top {
    grid-template-columns: 1fr;
  }

  .summary-grid,
  .stats-grid,
  .info-grid {
    grid-template-columns: 1fr;
  }

  .section-head,
  .history-head-actions,
  .batch-bar {
    align-items: stretch;
    flex-direction: column;
  }

  .history-item,
  .record-item {
    grid-template-columns: 1fr;
    align-items: flex-start;
  }

  .history-left,
  .history-right,
  .record-side {
    width: 100%;
  }
}

@media (max-width: 520px) {
  .back-wrap,
  .profile-container {
    width: calc(100% - 24px);
  }

  .profile-container {
    padding: 20px 0 38px;
  }

  .profile-card,
  .history-card,
  .summary-card,
  .stats-card {
    padding: 18px;
    border-radius: 18px;
  }

  h2 {
    font-size: 22px;
  }

  .avatar-box {
    width: 118px;
    height: 118px;
  }

  .avatar-upload-btn {
    width: 118px;
  }

  .avatar-text {
    font-size: 38px;
  }

  .edit-btn,
  .save-btn,
  .action-btn,
  .item-delete-btn,
  .link-btn {
    width: 100%;
  }

  .record-item {
    padding: 16px;
  }
}
</style>
