<template>
  <div class="admin-page">
    <Header />

    <div class="admin-layout admin-container">
      <AdminSidebar />

      <!-- 右侧内容区 -->
      <main class="main-content">
        <!-- 工具栏 -->
        <section class="toolbar-card">
          <div class="toolbar-left">
            <button class="ui-back-link" @click="goHome">
              ← 返回首页
            </button>
            <div class="section-title">问题反馈管理</div>
            <div class="toolbar-subtitle">
              面向个性化资源生成、学习路径规划与多智能体协同过程的问题反馈管理
            </div>
          </div>

          <div class="toolbar-right">
            <div class="search-box">
              <input
                v-model.trim="queryForm.keyword"
                class="search-input"
                type="text"
                placeholder="搜索反馈标题、描述、资源或联系方式..."
                @keyup.enter="handleSearch"
              />
              <button class="search-btn" @click="handleSearch">搜索</button>
            </div>

            <select
              v-model="queryForm.type"
              class="status-select"
              @change="handleSearch"
            >
              <option value="">全部类型</option>
              <option value="资源生成质量问题">资源生成质量问题</option>
              <option value="学习路径规划问题">学习路径规划问题</option>
              <option value="多智能体协同异常">多智能体协同异常</option>
              <option value="学习画像问题">学习画像问题</option>
              <option value="大模型回答偏差">大模型回答偏差</option>
              <option value="页面显示问题">页面显示问题</option>
              <option value="账号登录问题">账号登录问题</option>
              <option value="功能建议">功能建议</option>
              <option value="其他">其他</option>
            </select>

            <select
              v-model="queryForm.status"
              class="status-select"
              @change="handleSearch"
            >
              <option value="">全部状态</option>
              <option value="待处理">待处理</option>
              <option value="处理中">处理中</option>
              <option value="已解决">已解决</option>
            </select>

            <button class="reset-btn" @click="handleReset">重置</button>
          </div>
        </section>

        <!-- 列表区域 -->
        <section class="table-card">
          <div class="table-head">
            <div class="section-title">反馈列表</div>
            <div class="table-tip">共 {{ total }} 条数据</div>
          </div>

          <div class="table-wrap">
            <table class="feedback-table">
              <thead>
                <tr>
                  <th>问题类型</th>
                  <th>标题</th>
                  <th>联系方式</th>
                  <th>处理状态</th>
                  <th>提交时间</th>
                  <th class="action-column">操作</th>
                </tr>
              </thead>

              <tbody>
                <tr v-for="item in feedbackList" :key="item.id">
                  <td>
                    <span class="type-badge">{{ item.type || '-' }}</span>
                  </td>
                  <td>
                    <div class="title-cell">{{ item.title || '-' }}</div>
                  </td>
                  <td>{{ item.contact || '-' }}</td>
                  <td>
                    <span
                      class="status-badge"
                      :class="getStatusClass(item.status)"
                    >
                      {{ item.status || '-' }}
                    </span>
                  </td>
                  <td>{{ item.createTime || '-' }}</td>
                  <td class="action-cell">
                    <div class="action-group">
                      <button class="action-btn detail" @click="handleDetail(item)">
                        详情
                      </button>
                      <button
                        v-if="item.status !== '已解决'"
                        class="action-btn success"
                        @click="handleResolve(item.id)"
                      >
                        标记解决
                      </button>
                      <button
                        class="action-btn delete"
                        @click="handleDelete(item.id)"
                      >
                        删除
                      </button>
                    </div>
                  </td>
                </tr>

                <tr v-if="!loading && !feedbackList.length">
                  <td colspan="6">
                    <div class="empty-box">暂无符合条件的反馈数据</div>
                  </td>
                </tr>

                <tr v-if="loading">
                  <td colspan="6">
                    <div class="empty-box">加载中...</div>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>

          <!-- 分页 -->
          <div class="pagination">
            <button
              class="page-btn"
              :disabled="queryForm.pageNum === 1"
              @click="handlePrevPage"
            >
              上一页
            </button>

            <span class="page-text">
              第 {{ queryForm.pageNum }} / {{ totalPages }} 页
            </span>

            <button
              class="page-btn"
              :disabled="queryForm.pageNum >= totalPages"
              @click="handleNextPage"
            >
              下一页
            </button>
          </div>
        </section>
      </main>
    </div>

    <!-- 详情弹窗 -->
    <div v-if="detailVisible" class="dialog-mask" @click="closeDetail">
      <div class="dialog-card" @click.stop>
        <div class="dialog-head">
          <div>
            <div class="dialog-title">反馈详情</div>
            <div class="dialog-subtitle">查看学习资源生成与多智能体系统相关反馈</div>
          </div>
          <button class="close-btn" @click="closeDetail">×</button>
        </div>

        <div v-if="currentFeedback" class="dialog-content">
          <div class="detail-grid">
            <div class="detail-item">
              <span class="detail-label">问题类型</span>
              <span class="detail-value">{{ currentFeedback.type || '-' }}</span>
            </div>

            <div class="detail-item">
              <span class="detail-label">联系方式</span>
              <span class="detail-value">{{ currentFeedback.contact || '-' }}</span>
            </div>

            <div class="detail-item full">
              <span class="detail-label">问题标题</span>
              <span class="detail-value">{{ currentFeedback.title || '-' }}</span>
            </div>

            <div class="detail-item full">
              <span class="detail-label">问题描述</span>
              <span class="detail-value">{{ currentFeedback.content || '-' }}</span>
            </div>

            <div class="detail-item full">
              <span class="detail-label">补充说明</span>
              <span class="detail-value">{{ currentFeedback.remark || '暂无补充说明' }}</span>
            </div>

            <div class="detail-item">
              <span class="detail-label">允许联系</span>
              <span class="detail-value">{{ currentFeedback.allowContact ? '是' : '否' }}</span>
            </div>

            <div class="detail-item">
              <span class="detail-label">处理状态</span>
              <span class="detail-value">{{ currentFeedback.status || '-' }}</span>
            </div>

            <div class="detail-item">
              <span class="detail-label">提交时间</span>
              <span class="detail-value">{{ currentFeedback.createTime || '-' }}</span>
            </div>
          </div>
        </div>

        <div class="dialog-actions">
          <button
            v-if="currentFeedback && currentFeedback.status !== '已解决'"
            class="primary-btn"
            @click="handleResolve(currentFeedback.id)"
          >
            标记为已解决
          </button>
          <button class="secondary-btn" @click="closeDetail">关闭</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { deleteAdminFeedback, getAdminFeedback, resolveAdminFeedback } from '../api/admin'
import Header from '../components/AppHeader.vue'
import AdminSidebar from '../components/admin/AdminSidebar.vue'
import '../styles/admin-layout.css'

const router = useRouter()

const goHome = () => {
  router.push('/')
}

const loading = ref(false)
const detailVisible = ref(false)
const currentFeedback = ref(null)

const queryForm = reactive({
  pageNum: 1,
  pageSize: 8,
  keyword: '',
  type: '',
  status: ''
})

const feedbackList = ref([])
const total = ref(0)

const totalPages = computed(() => {
  return Math.max(1, Math.ceil(total.value / queryForm.pageSize))
})

const loadFeedback = async () => {
  loading.value = true
  try {
    const response = await getAdminFeedback({ ...queryForm })
    feedbackList.value = Array.isArray(response.items) ? response.items : []
    total.value = Number(response.total) || 0
  } catch (error) {
    alert(`反馈加载失败：${error.message}`)
  } finally {
    loading.value = false
  }
}

const handleSearch = async () => {
  queryForm.pageNum = 1
  await loadFeedback()
}

const handleReset = async () => {
  queryForm.pageNum = 1
  queryForm.keyword = ''
  queryForm.type = ''
  queryForm.status = ''
  await loadFeedback()
}

const handlePrevPage = async () => {
  if (queryForm.pageNum > 1) {
    queryForm.pageNum -= 1
    await loadFeedback()
  }
}

const handleNextPage = async () => {
  if (queryForm.pageNum < totalPages.value) {
    queryForm.pageNum += 1
    await loadFeedback()
  }
}

const handleDetail = (item) => {
  currentFeedback.value = { ...item }
  detailVisible.value = true
}

const closeDetail = () => {
  detailVisible.value = false
  currentFeedback.value = null
}

const handleResolve = async (id) => {
  const confirmed = window.confirm('确定将该反馈标记为已解决吗？')
  if (!confirmed) return
  try {
    const updated = await resolveAdminFeedback(id)
    if (currentFeedback.value?.id === id) currentFeedback.value = { ...updated }
    await loadFeedback()
    alert('已标记为已解决')
  } catch (error) {
    alert(`操作失败：${error.message}`)
  }
}

const handleDelete = async (id) => {
  const confirmed = window.confirm('确定删除该反馈吗？删除后不可恢复。')
  if (!confirmed) return

  try {
    await deleteAdminFeedback(id)
    if (currentFeedback.value?.id === id) closeDetail()
    if (feedbackList.value.length === 1 && queryForm.pageNum > 1) queryForm.pageNum -= 1
    await loadFeedback()
    alert('删除成功')
  } catch (error) {
    alert(`删除失败：${error.message}`)
  }
}

const getStatusClass = (status) => {
  if (status === '待处理') return 'pending'
  if (status === '处理中') return 'processing'
  if (status === '已解决') return 'resolved'
  return ''
}

onMounted(loadFeedback)
</script>

<style scoped>
.toolbar-card,
.table-card {
  position: relative;
  overflow: hidden;
  background: #ffffff;
  border: 1px solid #e5e7eb;
  border-radius: 18px;
  padding: 34px;
  box-shadow: var(--shadow-md);
}

.toolbar-card {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 22px;
  flex-wrap: wrap;
}

.toolbar-left {
  flex: 1;
}

.section-title {
  margin: 0;
  font-size: 25px;
  line-height: 1.35;
  font-weight: 800;
  color: #111827;
}

.toolbar-subtitle {
  margin-top: 10px;
  max-width: 560px;
  font-size: 15px;
  line-height: 1.8;
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
  overflow: hidden;
  background: #ffffff;
  border: 1px solid #e5e7eb;
  border-radius: 14px;
}

.search-input {
  width: 320px;
  height: 48px;
  border: none;
  outline: none;
  padding: 0 16px;
  background: transparent;
  color: #111827;
  font-size: 14px;
  box-sizing: border-box;
}

.search-input::placeholder {
  color: #9ca3af;
}

.search-btn {
  height: 48px;
  padding: 0 22px;
  border: none;
  background: #111827;
  color: #ffffff;
  cursor: pointer;
  font-size: 14px;
  font-weight: 700;
  transition: all 0.2s ease;
}

.search-btn:hover {
  background: #1f2937;
}

.status-select,
.reset-btn,
.page-btn,
.primary-btn,
.secondary-btn,
.action-btn,
.close-btn {
  outline: none;
  font-family: inherit;
}

.status-select {
  height: 48px;
  min-width: 150px;
  padding: 0 14px;
  border: 1px solid #e5e7eb;
  border-radius: 14px;
  background: #ffffff;
  color: #111827;
  cursor: pointer;
  font-size: 14px;
  font-weight: 600;
}

.reset-btn,
.page-btn,
.secondary-btn {
  border: 1px solid #e5e7eb;
  background: #ffffff;
  color: #111827;
}

.reset-btn {
  height: 48px;
  padding: 0 20px;
  border-radius: 14px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 700;
  transition: all 0.2s ease;
}

.reset-btn:hover,
.page-btn:hover:not(:disabled),
.secondary-btn:hover {
  background: #f1f5f9;
  transform: translateY(-1px);
}

.table-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 14px;
  flex-wrap: wrap;
  margin-bottom: 20px;
}

.table-tip {
  color: #111827;
  font-size: 14px;
  font-weight: 600;
}

.table-wrap {
  width: 100%;
  overflow-x: auto;
}

.feedback-table {
  width: 100%;
  min-width: 1080px;
  border-collapse: separate;
  border-spacing: 0;
  overflow: hidden;
  table-layout: fixed;
  background: #ffffff;
  border: 1px solid #e5e7eb;
  border-radius: 18px;
}

.feedback-table thead th {
  padding: 16px 18px;
  text-align: left;
  background: #f9fafb;
  color: #111827;
  font-size: 14px;
  font-weight: 800;
  border-bottom: 1px solid #e5e7eb;
  white-space: nowrap;
}

.feedback-table tbody td {
  padding: 17px 18px;
  color: #111827;
  font-size: 14px;
  line-height: 1.7;
  border-bottom: 1px solid #e5e7eb;
  vertical-align: middle;
  word-break: break-word;
}

.feedback-table tbody tr:last-child td {
  border-bottom: none;
}

.feedback-table th:nth-child(1),
.feedback-table td:nth-child(1) {
  width: 160px;
}

.feedback-table th:nth-child(2),
.feedback-table td:nth-child(2) {
  width: 240px;
}

.feedback-table th:nth-child(3),
.feedback-table td:nth-child(3) {
  width: 220px;
}

.feedback-table th:nth-child(4),
.feedback-table td:nth-child(4) {
  width: 120px;
}

.feedback-table th:nth-child(5),
.feedback-table td:nth-child(5) {
  width: 180px;
}

.action-column,
.action-cell {
  width: 300px;
}

.title-cell {
  overflow: hidden;
  color: #111827;
  font-weight: 700;
  white-space: nowrap;
  text-overflow: ellipsis;
}

.type-badge,
.status-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-height: 30px;
  padding: 0 12px;
  border-radius: 999px;
  font-size: 13px;
  font-weight: 700;
  white-space: nowrap;
  border: 1px solid #e5e7eb;
}

.type-badge {
  background: #f3f4f6;
  color: #111827;
}

.status-badge.pending {
  background: #fff7ed;
  color: #9a3412;
  border-color: #fed7aa;
}

.status-badge.processing {
  background: #eff6ff;
  color: #1d4ed8;
  border-color: #bfdbfe;
}

.status-badge.resolved {
  background: #f0fdf4;
  color: #15803d;
  border-color: #bbf7d0;
}

.action-cell {
  white-space: nowrap;
}

.action-group {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: nowrap;
}

.action-btn {
  height: 36px;
  min-width: 72px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  padding: 0 12px;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  cursor: pointer;
  background: #ffffff;
  color: #111827;
  font-size: 13px;
  font-weight: 700;
  white-space: nowrap;
  transition: all 0.2s ease;
  box-sizing: border-box;
}

.action-btn:hover {
  background: #f1f5f9;
  transform: translateY(-1px);
}

.action-btn.detail {
  background: #f9fafb;
}

.action-btn.success {
  min-width: 88px;
  background: #111827;
  color: #ffffff;
  border-color: #111827;
}

.action-btn.success:hover,
.primary-btn:hover {
  background: #1f2937;
}

.action-btn.delete {
  color: #b91c1c;
  background: #fff5f5;
  border-color: #fecaca;
}

.empty-box {
  padding: 44px 0;
  text-align: center;
  color: #6b7280;
  font-size: 15px;
  font-weight: 600;
}

.pagination {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 14px;
  flex-wrap: wrap;
  margin-top: 20px;
}

.page-btn {
  height: 42px;
  padding: 0 18px;
  border-radius: 14px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 700;
  transition: all 0.2s ease;
}

.page-btn:disabled,
.primary-btn:disabled {
  opacity: 0.55;
  cursor: not-allowed;
  transform: none;
}

.page-text {
  color: #111827;
  font-size: 14px;
  font-weight: 600;
}

.dialog-mask {
  position: fixed;
  inset: 0;
  z-index: 999;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
  background: rgba(0, 0, 0, 0.42);
}

.dialog-card {
  width: 760px;
  max-width: 100%;
  overflow: hidden;
  background: #ffffff;
  border: 1px solid #e5e7eb;
  border-radius: 18px;
  box-shadow: 0 18px 50px rgba(0, 0, 0, 0.18);
}

.dialog-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 28px 28px 12px;
}

.dialog-title {
  color: #111827;
  font-size: 25px;
  font-weight: 800;
}

.dialog-subtitle {
  margin-top: 8px;
  color: #111827;
  font-size: 14px;
  line-height: 1.7;
}

.close-btn {
  width: 42px;
  height: 42px;
  border: 1px solid #e5e7eb;
  border-radius: 50%;
  background: #ffffff;
  color: #111827;
  cursor: pointer;
  font-size: 22px;
  transition: all 0.2s ease;
}

.close-btn:hover {
  background: #f1f5f9;
  transform: rotate(90deg);
}

.dialog-content {
  padding: 12px 28px 24px;
}

.detail-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px;
  padding-top: 8px;
}

.detail-item {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 15px;
  background: #f9fafb;
  border: 1px solid #e5e7eb;
  border-radius: 14px;
}

.detail-item.full {
  grid-column: 1 / -1;
}

.detail-label {
  color: #6b7280;
  font-size: 13px;
  font-weight: 700;
}

.detail-value {
  color: #111827;
  font-size: 15px;
  line-height: 1.8;
  word-break: break-all;
}

.dialog-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 0 28px 28px;
}

.primary-btn,
.secondary-btn {
  height: 44px;
  padding: 0 20px;
  border-radius: 14px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 700;
  transition: all 0.2s ease;
}

.primary-btn {
  border: none;
  background: #111827;
  color: #ffffff;
}

@media (max-width: 992px) {
  .detail-grid {
    grid-template-columns: 1fr;
  }

  .search-input {
    width: 220px;
  }
}

@media (max-width: 768px) {
  .section-title,
  .dialog-title {
    font-size: 22px;
  }

  .toolbar-right,
  .search-box {
    width: 100%;
  }

  .search-input {
    width: 100%;
  }

  .status-select,
  .reset-btn {
    flex: 1;
    min-width: 0;
  }

  .dialog-actions {
    flex-direction: column;
  }

  .primary-btn,
  .secondary-btn {
    width: 100%;
  }

  .ui-back-link {
    margin-bottom: 12px;
    width: 100%;
    justify-content: center;
  }

  .toolbar-left {
    width: 100%;
  }
}
</style>
