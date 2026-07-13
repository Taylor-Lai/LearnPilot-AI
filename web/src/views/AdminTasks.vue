<template>
  <div class="admin-page">
    <Header />

    <div class="admin-layout admin-container">
      <AdminSidebar />

      <main class="main-content">
        <section class="page-header card">
          <div class="header-left">
            <button class="ui-back-link" @click="goHome">← 返回首页</button>
            <div class="section-title">Producer 任务监控</div>
            <div class="section-subtitle">查看全体用户的资源生成任务状态、产物与失败原因</div>
          </div>
        </section>

        <section class="stats-grid">
          <div class="stat-card card">
            <div class="stat-label">任务总数</div>
            <div class="stat-value">{{ formatSummary(overview.producerTaskCount) }}</div>
          </div>
          <div class="stat-card card">
            <div class="stat-label">已完成</div>
            <div class="stat-value">{{ formatSummary(overview.producerCompletedCount) }}</div>
          </div>
          <div class="stat-card card">
            <div class="stat-label">失败</div>
            <div class="stat-value">{{ formatSummary(overview.producerFailedCount) }}</div>
          </div>
          <div class="stat-card card">
            <div class="stat-label">进行中</div>
            <div class="stat-value">{{ formatSummary(activeTaskCount) }}</div>
          </div>
        </section>

        <section class="toolbar-card">
          <div class="toolbar-left">
            <div class="toolbar-title">任务筛选</div>
          </div>
          <div class="toolbar-right">
            <div class="search-box">
              <input
                v-model.trim="queryForm.keyword"
                class="search-input"
                type="text"
                placeholder="搜索任务ID、主题、需求、用户名或邮箱"
                @keyup.enter="handleSearch"
              />
              <button class="search-btn" type="button" @click="handleSearch">搜索</button>
            </div>
            <select v-model="queryForm.status" class="status-select" @change="handleSearch">
              <option value="">全部状态</option>
              <option value="pending">等待中</option>
              <option value="running">生成中</option>
              <option value="completed">已完成</option>
              <option value="failed">失败</option>
            </select>
            <button class="reset-btn" type="button" @click="handleReset">重置</button>
          </div>
        </section>

        <div v-if="listError" class="error-banner card">
          <div class="error-text">{{ listError }}</div>
          <button type="button" class="retry-btn" @click="loadTaskList">重新加载</button>
        </div>

        <div v-if="listNotice && !listError" class="info-banner card">
          <div class="info-text">{{ listNotice }}</div>
        </div>

        <section class="table-card">
          <div class="table-head">
            <div class="section-title">任务列表</div>
            <div class="table-tip">共 {{ total }} 条任务</div>
          </div>

          <div v-if="listLoading" class="loading-box">任务列表加载中...</div>

          <template v-else>
            <div v-if="!taskList.length" class="empty-box">暂无符合条件的任务</div>

            <div v-else class="table-wrap desktop-table">
              <table class="task-table">
                <thead>
                  <tr>
                    <th class="col-task-id">任务ID</th>
                    <th>用户</th>
                    <th>主题</th>
                    <th class="col-status">状态</th>
                    <th class="col-progress">进度</th>
                    <th class="col-count">产物数</th>
                    <th class="col-created">创建时间</th>
                    <th class="col-action">操作</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="item in taskList" :key="item.taskId">
                    <td class="col-task-id" :title="item.taskId">{{ shortTaskId(item.taskId) }}</td>
                    <td class="user-cell">
                      <div class="user-name">{{ item.username || '未知用户' }}</div>
                      <div v-if="item.email" class="user-email col-email">{{ item.email }}</div>
                    </td>
                    <td class="topic-cell" :title="item.topic">{{ item.topic || '-' }}</td>
                    <td class="col-status">
                      <span class="status-badge" :class="statusClass(item.status)">
                        {{ producerStatusText(item.status) }}
                      </span>
                      <button
                        v-if="item.status === 'failed'"
                        type="button"
                        class="reason-link"
                        @click="openDetail(item.taskId)"
                      >
                        查看原因
                      </button>
                    </td>
                    <td class="col-progress">
                      <div class="progress-text">{{ item.progress }}%</div>
                      <div class="progress-bar">
                        <div class="progress-fill" :style="{ width: `${item.progress}%` }"></div>
                      </div>
                    </td>
                    <td class="col-count">{{ item.artifactCount }}</td>
                    <td class="col-created">{{ formatDate(item.createdAt) }}</td>
                    <td class="col-action">
                      <button type="button" class="action-btn" @click="openDetail(item.taskId)">详情</button>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>

            <div v-if="taskList.length" class="mobile-list">
              <article v-for="item in taskList" :key="`mobile-${item.taskId}`" class="mobile-card card">
                <div class="mobile-row">
                  <span class="mobile-label">任务ID</span>
                  <span :title="item.taskId">{{ shortTaskId(item.taskId) }}</span>
                </div>
                <div class="mobile-row">
                  <span class="mobile-label">用户</span>
                  <span>{{ item.username || '未知用户' }}</span>
                </div>
                <div class="mobile-row">
                  <span class="mobile-label">主题</span>
                  <span class="mobile-topic">{{ item.topic || '-' }}</span>
                </div>
                <div class="mobile-row">
                  <span class="mobile-label">状态</span>
                  <span class="status-badge" :class="statusClass(item.status)">
                    {{ producerStatusText(item.status) }}
                  </span>
                </div>
                <div class="mobile-row">
                  <span class="mobile-label">进度</span>
                  <span>{{ item.progress }}%</span>
                </div>
                <div class="mobile-actions">
                  <button type="button" class="action-btn" @click="openDetail(item.taskId)">详情</button>
                </div>
              </article>
            </div>

            <div v-if="taskList.length" class="pagination">
              <button class="page-btn" type="button" :disabled="queryForm.page === 1" @click="handlePrevPage">
                上一页
              </button>
              <span class="page-text">第 {{ queryForm.page }} / {{ totalPages }} 页</span>
              <button
                class="page-btn"
                type="button"
                :disabled="queryForm.page >= totalPages"
                @click="handleNextPage"
              >
                下一页
              </button>
            </div>
          </template>
        </section>
      </main>
    </div>

    <div v-if="detailVisible" class="dialog-mask" @click="closeDetail">
      <div class="dialog-card" @click.stop>
        <div class="dialog-head">
          <div>
            <div class="dialog-title">任务详情</div>
            <div class="dialog-subtitle">查看任务状态、用户、产物与结果概要</div>
          </div>
          <button type="button" class="close-btn" @click="closeDetail">×</button>
        </div>

        <div v-if="detailLoading" class="dialog-loading">正在加载任务详情...</div>
        <div v-else-if="detailError" class="dialog-error">{{ detailError }}</div>
        <div v-else-if="detailData" class="dialog-content">
          <section class="detail-section">
            <div class="detail-section-title">基本信息</div>
            <div class="detail-grid">
              <div class="detail-item"><span class="detail-label">任务ID</span><span class="detail-value">{{ detailData.taskId }}</span></div>
              <div class="detail-item"><span class="detail-label">主题</span><span class="detail-value">{{ detailData.topic || '-' }}</span></div>
              <div class="detail-item full"><span class="detail-label">需求</span><span class="detail-value">{{ detailData.requirement || '无额外要求' }}</span></div>
              <div class="detail-item"><span class="detail-label">任务类型</span><span class="detail-value">{{ detailData.taskType || '-' }}</span></div>
              <div class="detail-item">
                <span class="detail-label">状态</span>
                <span class="status-badge" :class="statusClass(detailData.status)">{{ producerStatusText(detailData.status) }}</span>
              </div>
              <div class="detail-item"><span class="detail-label">进度</span><span class="detail-value">{{ detailData.progress }}%</span></div>
              <div class="detail-item"><span class="detail-label">创建时间</span><span class="detail-value">{{ formatDate(detailData.createdAt) }}</span></div>
              <div class="detail-item"><span class="detail-label">最后更新时间</span><span class="detail-value">{{ formatDate(detailData.updatedAt) }}</span></div>
            </div>
          </section>

          <section class="detail-section">
            <div class="detail-section-title">所属用户</div>
            <div class="detail-grid">
              <div class="detail-item"><span class="detail-label">用户名</span><span class="detail-value">{{ detailData.user?.username || '未知用户' }}</span></div>
              <div class="detail-item"><span class="detail-label">邮箱</span><span class="detail-value">{{ detailData.user?.email || '-' }}</span></div>
              <div class="detail-item"><span class="detail-label">账号状态</span><span class="detail-value">{{ detailData.user?.status || '-' }}</span></div>
            </div>
          </section>

          <section v-if="detailData.status === 'failed' || detailData.errorMessage" class="detail-section">
            <div class="detail-section-title">失败信息</div>
            <div class="error-box">{{ detailData.errorMessage || '暂无错误信息' }}</div>
          </section>

          <section class="detail-section">
            <div class="detail-section-title">产物列表（{{ detailData.artifactCount || 0 }}）</div>
            <div v-if="!detailData.artifacts?.length" class="empty-inline">暂无产物</div>
            <div v-else class="artifact-list">
              <article v-for="(artifact, index) in detailData.artifacts" :key="`${artifact.artifactType}-${index}`" class="artifact-item">
                <div class="artifact-head">
                  <span class="artifact-type">{{ artifact.artifactType }}</span>
                  <span class="artifact-title">{{ artifact.title }}</span>
                </div>
                <p v-if="artifact.contentPreview" class="artifact-preview">{{ artifact.contentPreview }}</p>
                <a v-if="artifact.url" class="artifact-link" :href="artifact.url" target="_blank" rel="noopener noreferrer">{{ artifact.url }}</a>
                <div class="artifact-time">{{ formatDate(artifact.createdAt) }}</div>
              </article>
            </div>
          </section>

          <section class="detail-section">
            <div class="detail-section-title">结果概要</div>
            <div class="detail-grid">
              <div class="detail-item"><span class="detail-label">主题</span><span class="detail-value">{{ detailData.resultSummary?.topic || '-' }}</span></div>
              <div class="detail-item"><span class="detail-label">Agent 轨迹数</span><span class="detail-value">{{ detailData.resultSummary?.agentTraceCount ?? 0 }}</span></div>
              <div class="detail-item full">
                <span class="detail-label">请求类型</span>
                <span class="detail-value">{{ formatList(detailData.resultSummary?.requestedTypes) }}</span>
              </div>
              <div class="detail-item full">
                <span class="detail-label">产物类型</span>
                <span class="detail-value">{{ formatList(detailData.resultSummary?.artifactTypes) }}</span>
              </div>
            </div>
          </section>
        </div>

        <div class="dialog-actions">
          <button type="button" class="secondary-btn" @click="closeDetail">关闭</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import Header from '../components/AppHeader.vue'
import AdminSidebar from '../components/admin/AdminSidebar.vue'
import '../styles/admin-layout.css'
import {
  getAdminProducerTaskDetail,
  getAdminProducerTasks,
  getAdminStatistics,
} from '../api/admin'
import { formatDate, producerStatusText } from '../utils/dashboard'

const router = useRouter()

const overview = reactive({
  producerTaskCount: 0,
  producerCompletedCount: 0,
  producerFailedCount: 0,
  producerRunningCount: 0,
  producerPendingCount: 0,
})
const statsLoaded = ref(false)

const taskList = ref([])
const total = ref(0)
const listLoading = ref(false)
const listError = ref('')
const listNotice = ref('')

const queryForm = reactive({
  page: 1,
  pageSize: 10,
  keyword: '',
  status: '',
})

const detailVisible = ref(false)
const detailLoading = ref(false)
const detailError = ref('')
const detailData = ref(null)

const activeTaskCount = computed(() => (
  Number(overview.producerRunningCount || 0) + Number(overview.producerPendingCount || 0)
))

const totalPages = computed(() => Math.max(1, Math.ceil(total.value / queryForm.pageSize)))

const goHome = () => {
  router.push('/')
}

const formatSummary = (value) => {
  if (!statsLoaded.value) return '—'
  const num = Number(value ?? 0)
  return Number.isFinite(num) ? String(num) : '0'
}

const shortTaskId = (taskId) => {
  const value = String(taskId || '')
  if (value.length <= 12) return value
  return `${value.slice(0, 12)}...`
}

const statusClass = (status) => {
  const normalized = String(status || '').toLowerCase()
  if (normalized === 'completed') return 'completed'
  if (normalized === 'failed') return 'failed'
  if (normalized === 'running') return 'running'
  if (normalized === 'pending') return 'pending'
  return 'unknown'
}

const formatList = (items) => {
  if (!Array.isArray(items) || !items.length) return '-'
  return items.join('、')
}

const buildListParams = () => {
  const params = {
    page: queryForm.page,
    pageSize: queryForm.pageSize,
  }
  if (queryForm.keyword) params.keyword = queryForm.keyword
  if (queryForm.status) params.status = queryForm.status
  return params
}

const loadStatistics = async () => {
  try {
    const data = await getAdminStatistics()
    const source = data.overview || data
    overview.producerTaskCount = source.producerTaskCount ?? 0
    overview.producerCompletedCount = source.producerCompletedCount ?? 0
    overview.producerFailedCount = source.producerFailedCount ?? 0
    overview.producerRunningCount = source.producerRunningCount ?? 0
    overview.producerPendingCount = source.producerPendingCount ?? 0
    statsLoaded.value = true
  } catch (error) {
    console.error('加载任务摘要失败：', error)
    statsLoaded.value = false
  }
}

const loadTaskList = async () => {
  listLoading.value = true
  listError.value = ''
  listNotice.value = ''
  try {
    const data = await getAdminProducerTasks(buildListParams())
    taskList.value = Array.isArray(data.items) ? data.items : []
    total.value = Number(data.total ?? 0)
    listNotice.value = data.message || ''
    if (data.page) queryForm.page = Number(data.page)
    if (data.pageSize) queryForm.pageSize = Number(data.pageSize)
  } catch (error) {
    console.error('加载任务列表失败：', error)
    listError.value = error?.message || '加载任务列表失败，请稍后重试'
    taskList.value = []
    total.value = 0
  } finally {
    listLoading.value = false
  }
}

const handleSearch = () => {
  queryForm.page = 1
  loadTaskList()
}

const handleReset = () => {
  queryForm.page = 1
  queryForm.keyword = ''
  queryForm.status = ''
  loadTaskList()
}

const handlePrevPage = () => {
  if (queryForm.page > 1) {
    queryForm.page -= 1
    loadTaskList()
  }
}

const handleNextPage = () => {
  if (queryForm.page < totalPages.value) {
    queryForm.page += 1
    loadTaskList()
  }
}

const openDetail = async (taskId) => {
  detailVisible.value = true
  detailLoading.value = true
  detailError.value = ''
  detailData.value = null
  try {
    detailData.value = await getAdminProducerTaskDetail(taskId)
  } catch (error) {
    console.error('加载任务详情失败：', error)
    detailError.value = error?.message || '加载任务详情失败'
  } finally {
    detailLoading.value = false
  }
}

const closeDetail = () => {
  detailVisible.value = false
  detailData.value = null
  detailError.value = ''
}

onMounted(() => {
  loadStatistics()
  loadTaskList()
})
</script>

<style scoped>
.card,
.toolbar-card,
.table-card {
  background: #ffffff;
  border: 1px solid #e5e7eb;
  border-radius: 18px;
  padding: 28px;
  box-shadow: var(--shadow-md);
  box-sizing: border-box;
}

.page-header,
.toolbar-card {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  flex-wrap: wrap;
}

.header-left,
.toolbar-left {
  flex: 1;
  min-width: 0;
}

.search-btn,
.reset-btn,
.page-btn,
.action-btn,
.retry-btn,
.secondary-btn,
.close-btn {
  font-family: inherit;
}

.section-title {
  font-size: 22px;
  line-height: 1.35;
  font-weight: 800;
  color: #111827;
}

.section-subtitle,
.toolbar-title {
  margin-top: 8px;
  font-size: 14px;
  color: #4b5563;
  line-height: 1.7;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 20px;
}

.stat-card {
  padding: 24px;
}

.stat-label {
  font-size: 14px;
  color: #4b5563;
  font-weight: 700;
  margin-bottom: 12px;
}

.stat-value {
  font-size: 32px;
  font-weight: 800;
  color: #111827;
}

.toolbar-right {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.search-box {
  display: flex;
  align-items: center;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  overflow: hidden;
  background: #ffffff;
}

.search-input {
  width: min(320px, 100%);
  height: 44px;
  border: none;
  outline: none;
  padding: 0 14px;
  font-size: 14px;
}

.search-btn {
  height: 44px;
  padding: 0 18px;
  border: none;
  background: #111827;
  color: #ffffff;
  font-size: 14px;
  font-weight: 700;
  cursor: pointer;
}

.status-select,
.reset-btn,
.page-btn,
.action-btn,
.retry-btn,
.secondary-btn {
  height: 44px;
  padding: 0 14px;
  border-radius: 12px;
  border: 1px solid #e5e7eb;
  background: #ffffff;
  font-size: 14px;
  font-weight: 600;
  color: #111827;
  cursor: pointer;
}

.error-banner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  flex-wrap: wrap;
  border-color: #fecaca;
  background: #fef2f2;
}

.info-banner {
  border-color: #bfdbfe;
  background: #eff6ff;
}

.info-text {
  color: #1d4ed8;
  font-size: 14px;
  font-weight: 600;
}

.error-text {
  color: #991b1b;
  font-size: 14px;
  font-weight: 600;
}

.table-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 18px;
  flex-wrap: wrap;
}

.table-tip {
  font-size: 14px;
  color: #4b5563;
  font-weight: 600;
}

.loading-box,
.empty-box,
.empty-inline {
  text-align: center;
  padding: 36px 0;
  color: #6b7280;
  font-size: 15px;
  font-weight: 600;
}

.table-wrap {
  width: 100%;
  overflow-x: visible;
}

.task-table {
  width: 100%;
  border-collapse: collapse;
  table-layout: fixed;
}

.task-table th,
.task-table td {
  padding: 14px 12px;
  border-bottom: 1px solid #f3f4f6;
  text-align: left;
  vertical-align: middle;
  font-size: 14px;
  color: #111827;
}

.task-table thead th {
  background: #f9fafb;
  font-size: 13px;
  font-weight: 700;
}

.task-table th:nth-child(1),
.task-table td:nth-child(1) { width: 11%; }
.task-table th:nth-child(2),
.task-table td:nth-child(2) { width: 16%; }
.task-table th:nth-child(3),
.task-table td:nth-child(3) { width: 20%; }
.task-table th:nth-child(4),
.task-table td:nth-child(4) { width: 14%; }
.task-table th:nth-child(5),
.task-table td:nth-child(5) { width: 12%; }
.task-table th:nth-child(6),
.task-table td:nth-child(6) { width: 8%; }
.task-table th:nth-child(7),
.task-table td:nth-child(7) { width: 14%; }
.task-table th:nth-child(8),
.task-table td:nth-child(8) { width: 9%; }

.col-task-id,
.topic-cell,
.user-cell {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.topic-cell {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  white-space: normal;
}

.user-name {
  font-weight: 600;
}

.user-email {
  margin-top: 4px;
  font-size: 12px;
  color: #6b7280;
}

.status-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-height: 28px;
  padding: 0 10px;
  border-radius: 999px;
  border: 1px solid #e5e7eb;
  font-size: 12px;
  font-weight: 700;
  white-space: nowrap;
}

.status-badge.completed {
  background: #111827;
  color: #ffffff;
  border-color: #111827;
}

.status-badge.failed {
  background: #fef2f2;
  color: #991b1b;
  border-color: #fecaca;
}

.status-badge.running {
  background: #f3f4f6;
  color: #111827;
}

.status-badge.pending,
.status-badge.unknown {
  background: #ffffff;
  color: #374151;
}

.reason-link {
  display: block;
  margin-top: 6px;
  padding: 0;
  border: none;
  background: transparent;
  color: #991b1b;
  font-size: 12px;
  cursor: pointer;
  text-decoration: underline;
}

.progress-text {
  font-size: 12px;
  font-weight: 700;
  margin-bottom: 6px;
}

.progress-bar {
  height: 6px;
  background: #f3f4f6;
  border-radius: 999px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: #111827;
  border-radius: 999px;
}

.action-btn {
  height: 32px;
  padding: 0 12px;
  font-size: 13px;
}

.pagination {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 18px;
  flex-wrap: wrap;
}

.page-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.page-text {
  font-size: 14px;
  color: #4b5563;
  font-weight: 600;
}

.mobile-list {
  display: none;
}

.mobile-card {
  padding: 20px;
  margin-bottom: 12px;
}

.mobile-row {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 10px;
  font-size: 14px;
}

.mobile-label {
  color: #6b7280;
  font-weight: 600;
}

.mobile-topic {
  text-align: right;
  max-width: 60%;
}

.mobile-actions {
  margin-top: 12px;
}

.dialog-mask {
  position: fixed;
  inset: 0;
  background: rgba(15, 23, 42, 0.45);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
  z-index: 1000;
}

.dialog-card {
  width: min(920px, 100%);
  max-height: calc(100vh - 48px);
  overflow: auto;
  background: #ffffff;
  border-radius: 18px;
  border: 1px solid #e5e7eb;
  padding: 28px;
}

.dialog-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 20px;
}

.dialog-title {
  font-size: 22px;
  font-weight: 800;
  color: #111827;
}

.dialog-subtitle {
  margin-top: 6px;
  font-size: 14px;
  color: #6b7280;
}

.close-btn {
  width: 36px;
  height: 36px;
  border: 1px solid #e5e7eb;
  border-radius: 10px;
  background: #ffffff;
  font-size: 22px;
  cursor: pointer;
}

.dialog-loading,
.dialog-error {
  padding: 24px 0;
  text-align: center;
  color: #6b7280;
  font-weight: 600;
}

.dialog-error {
  color: #991b1b;
}

.detail-section {
  margin-bottom: 22px;
}

.detail-section-title {
  font-size: 16px;
  font-weight: 800;
  color: #111827;
  margin-bottom: 12px;
}

.detail-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.detail-item {
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding: 12px;
  border: 1px solid #f3f4f6;
  border-radius: 12px;
  background: #fafafa;
}

.detail-item.full {
  grid-column: 1 / -1;
}

.detail-label {
  font-size: 12px;
  color: #6b7280;
  font-weight: 700;
}

.detail-value {
  font-size: 14px;
  color: #111827;
  word-break: break-word;
}

.error-box {
  max-height: 180px;
  overflow: auto;
  padding: 14px;
  border-radius: 12px;
  border: 1px solid #fecaca;
  background: #fef2f2;
  color: #991b1b;
  font-size: 14px;
  line-height: 1.7;
  white-space: pre-wrap;
  word-break: break-word;
}

.artifact-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.artifact-item {
  padding: 14px;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  background: #ffffff;
}

.artifact-head {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.artifact-type {
  display: inline-flex;
  padding: 4px 8px;
  border-radius: 999px;
  background: #f3f4f6;
  font-size: 12px;
  font-weight: 700;
}

.artifact-title {
  font-size: 14px;
  font-weight: 700;
  color: #111827;
}

.artifact-preview {
  margin: 10px 0 0;
  font-size: 13px;
  line-height: 1.7;
  color: #4b5563;
  white-space: pre-wrap;
  word-break: break-word;
}

.artifact-link {
  display: inline-block;
  margin-top: 8px;
  color: #111827;
  font-size: 13px;
  word-break: break-all;
}

.artifact-time {
  margin-top: 8px;
  font-size: 12px;
  color: #6b7280;
}

.dialog-actions {
  display: flex;
  justify-content: flex-end;
  margin-top: 20px;
}

.secondary-btn {
  min-width: 96px;
}

@media (max-width: 1200px) {
  .stats-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 1024px) {
  .col-email,
  .task-table .col-task-id {
    display: none;
  }

  .task-table th:nth-child(1),
  .task-table td:nth-child(1),
  .task-table th:nth-child(2),
  .task-table td:nth-child(2) {
    width: 18%;
  }
}

@media (max-width: 768px) {
  .stats-grid {
    grid-template-columns: 1fr;
  }

  .toolbar-right,
  .search-box,
  .search-input {
    width: 100%;
  }

  .desktop-table {
    display: none;
  }

  .mobile-list {
    display: block;
  }

  .detail-grid {
    grid-template-columns: 1fr;
  }
}
</style>
