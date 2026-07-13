<template>
  <div class="admin-page">
    <Header />

    <div class="admin-layout admin-container">
      <AdminSidebar />

      <!-- 右侧内容区域 -->
      <main class="main-content">
        <!-- 返回首页按钮和工具栏 -->
        <section class="toolbar-card">
          <div class="toolbar-left">
            <button class="ui-back-link" @click="goHome">
              ← 返回首页
            </button>
            <div class="section-title">用户管理</div>
            <div class="toolbar-subtitle">
              支持按用户名、邮箱、昵称、角色与账号状态筛选
            </div>
          </div>

          <div class="toolbar-right">
            <div class="search-box">
              <input
                v-model.trim="queryForm.keyword"
                class="search-input"
                type="text"
                placeholder="搜索用户名、邮箱或昵称..."
                @keyup.enter="handleSearch"
              />
              <button class="search-btn" @click="handleSearch">搜索</button>
            </div>

            <select
              v-model="queryForm.roleFilter"
              class="status-select"
              @change="handleSearch"
            >
              <option value="">全部角色</option>
              <option value="admin">管理员</option>
              <option value="student">普通用户</option>
            </select>

            <select
              v-model="queryForm.statusFilter"
              class="status-select"
              @change="handleSearch"
            >
              <option value="">全部状态</option>
              <option value="active">正常</option>
              <option value="deleted">已删除</option>
              <option value="all">全部含已删除</option>
            </select>

            <button class="reset-btn" @click="handleReset">重置</button>
          </div>
        </section>

        <!-- 用户列表表格 -->
        <section class="table-card">
          <div class="table-head">
            <div class="section-title">用户列表</div>
            <div class="table-tip">共 {{ total }} 条数据</div>
          </div>


          <div class="table-wrap">
            <table class="user-table">
              <thead>
                <tr>
                  <th>用户名</th>
                  <th class="col-nickname">昵称</th>
                  <th>邮箱</th>
                  <th class="col-role">角色</th>
                  <th class="col-status">账号状态</th>
                  <th class="col-created">注册时间</th>
                  <th class="action-column">操作</th>
                </tr>
              </thead>

              <tbody>
                <tr v-for="item in userList" :key="item.id">
                  <td class="cell-ellipsis" :title="item.username">{{ item.username || '-' }}</td>
                  <td class="cell-ellipsis col-nickname" :title="item.nickname">{{ item.nickname || '-' }}</td>
                  <td class="cell-email" :title="item.email">{{ item.email || '-' }}</td>
                  <td class="role-cell-td col-role">
                    <span v-if="item.isAdmin" class="admin-tag">管理员</span>
                    <span v-else class="role-text">普通用户</span>
                  </td>
                  <td class="col-status">
                    <span
                      class="status-badge"
                      :class="item.status === 'active' ? 'normal' : 'disabled'"
                    >
                      {{ item.statusLabel }}
                    </span>
                  </td>
                  <td class="col-created">{{ item.createdAt || '-' }}</td>
                  <td class="action-cell">
                    <div class="action-group">
                      <button class="action-btn detail" @click="handleDetail(item.id)">
                        详情
                      </button>
                      <button
                        v-if="!isSelfUser(item.id)"
                        class="action-btn delete"
                        @click="handleDelete(item.id)"
                      >
                        删除
                      </button>
                    </div>
                  </td>
                </tr>

                <tr v-if="!loading && !userList.length">
                  <td colspan="7">
                    <div class="empty-box">暂无符合条件的用户数据</div>
                  </td>
                </tr>

                <tr v-if="loading">
                  <td colspan="7">
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
              :disabled="queryForm.page === 1"
              @click="handlePrevPage"
            >
              上一页
            </button>

            <span class="page-text">
              第 {{ queryForm.page }} / {{ totalPages }} 页
            </span>

            <button
              class="page-btn"
              :disabled="queryForm.page >= totalPages"
              @click="handleNextPage"
            >
              下一页
            </button>
          </div>
        </section>
      </main>
    </div>

    <!-- 用户详情弹窗 -->
    <div v-if="detailVisible" class="dialog-mask" @click="closeDetail">
      <div class="dialog-card" @click.stop>
        <div class="dialog-head">
          <div>
            <div class="dialog-title">用户详情</div>
            <div class="dialog-subtitle">查看用户资料与登录信息</div>
          </div>
          <button class="close-btn" @click="closeDetail">×</button>
        </div>

        <div v-if="detailLoading" class="dialog-loading">
          正在加载用户详情...
        </div>

        <div v-else-if="currentUser" class="dialog-content">
          <div class="detail-top">
            <div class="detail-avatar">
              {{ (currentUser.username || 'U').slice(0, 1) }}
            </div>
            <div class="detail-main">
              <div class="detail-name">
                {{ currentUser.username || '-' }}
                <span v-if="currentUser.isAdmin" class="detail-admin-tag">管理员</span>
              </div>
              <div class="detail-role">{{ currentUser.isAdmin ? '管理员' : '普通用户' }}</div>
            </div>
          </div>

          <div class="detail-grid">
            <div class="detail-item">
              <span class="detail-label">昵称</span>
              <span class="detail-value">{{ currentUser.nickname || '-' }}</span>
            </div>
            <div class="detail-item">
              <span class="detail-label">邮箱</span>
              <span class="detail-value">{{ currentUser.email || '-' }}</span>
            </div>
            <div class="detail-item">
              <span class="detail-label">账号状态</span>
              <span class="detail-value">{{ currentUser.statusLabel || '-' }}</span>
            </div>
            <div class="detail-item">
              <span class="detail-label">注册时间</span>
              <span class="detail-value">{{ currentUser.createdAt || '-' }}</span>
            </div>
            <div class="detail-item">
              <span class="detail-label">更新时间</span>
              <span class="detail-value">{{ currentUser.updatedAt || '-' }}</span>
            </div>
          </div>
        </div>

        <div class="dialog-actions">
          <button
            v-if="currentUser && !isSelfUser(currentUser.id)"
            class="primary-btn"
            :disabled="adminRoleLoading"
            @click="handleToggleAdminRole"
          >
            {{ adminRoleLoading ? '提交中...' : (currentUser.isAdmin ? '取消管理员' : '设为管理员') }}
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
import Header from '../components/AppHeader.vue'
import AdminSidebar from '../components/admin/AdminSidebar.vue'
import '../styles/admin-layout.css'
import { userStore } from '../stores/userStore'
import {
  getAdminUsers,
  getAdminUserDetail,
  deleteAdminUser,
  getAdminStatistics,
  updateAdminUserRole,
} from '../api/admin'

const router = useRouter()

const goHome = () => {
  router.push('/')
}

const loading = ref(false)
const detailLoading = ref(false)
const detailVisible = ref(false)
const adminRoleLoading = ref(false)
const currentUser = ref(null)

const userList = ref([])
const total = ref(0)

const statistics = reactive({
  totalUsers: 0,
  resourceCount: 0,
  pathCount: 0,
  feedbackCount: 0,
  producerTaskCount: 0,
  todayUserCount: 0,
})

const queryForm = reactive({
  page: 1,
  pageSize: 8,
  keyword: '',
  roleFilter: '',
  statusFilter: '',
})

const currentUserId = computed(() => String(userStore.state.userId || ''))

const totalPages = computed(() => {
  return Math.max(1, Math.ceil(total.value / queryForm.pageSize))
})

const isSelfUser = (id) => String(id) === currentUserId.value

const formatDateTime = (value) => {
  if (!value) return '-'
  return value.replace('T', ' ').slice(0, 19)
}

const formatStatusLabel = (status) => {
  if (status === 'active') return '正常'
  if (status === 'deleted') return '已删除'
  return status || '-'
}

const normalizeIsAdmin = (item = {}) => {
  if (item.isAdmin === true || item.is_admin === true) return true
  const roleText = String(item.role ?? '').toLowerCase()
  return roleText === 'admin'
}

const normalizeUser = (item = {}) => {
  const isAdmin = normalizeIsAdmin(item)
  const status = item.status || 'active'
  return {
    id: item.id ?? '',
    username: item.username || '-',
    nickname: item.nickname || item.username || '-',
    email: item.email || '-',
    isAdmin,
    status,
    statusLabel: formatStatusLabel(status),
    createdAt: formatDateTime(item.created_at),
    updatedAt: formatDateTime(item.updated_at),
  }
}

const buildListParams = () => {
  const params = {
    page: queryForm.page,
    pageSize: queryForm.pageSize,
  }
  if (queryForm.keyword) params.keyword = queryForm.keyword
  if (queryForm.roleFilter) params.role = queryForm.roleFilter
  if (queryForm.statusFilter) params.status = queryForm.statusFilter
  return params
}

const getUserPage = async () => {
  loading.value = true
  try {
    const data = await getAdminUsers(buildListParams())
    userList.value = Array.isArray(data.items) ? data.items.map(normalizeUser) : []
    total.value = Number(data.total ?? 0)
    if (data.page) queryForm.page = Number(data.page)
    if (data.pageSize) queryForm.pageSize = Number(data.pageSize)
  } catch (error) {
    console.error('获取用户列表失败：', error)
    alert(error.message || '获取用户列表失败')
  } finally {
    loading.value = false
  }
}

const getStatistics = async () => {
  try {
    const data = await getAdminStatistics()
    statistics.totalUsers = data.userCount ?? 0
    statistics.resourceCount = data.resourceCount ?? 0
    statistics.pathCount = data.pathCount ?? 0
    statistics.feedbackCount = data.feedbackCount ?? 0
    statistics.producerTaskCount = data.producerTaskCount ?? 0
    statistics.todayUserCount = data.todayUserCount ?? 0
  } catch (error) {
    console.error(error)
  }
}

const handleSearch = () => {
  queryForm.page = 1
  getUserPage()
}

const handleReset = () => {
  queryForm.page = 1
  queryForm.keyword = ''
  queryForm.roleFilter = ''
  queryForm.statusFilter = ''
  getUserPage()
}

const handlePrevPage = () => {
  if (queryForm.page > 1) {
    queryForm.page -= 1
    getUserPage()
  }
}

const handleNextPage = () => {
  if (queryForm.page < totalPages.value) {
    queryForm.page += 1
    getUserPage()
  }
}

const handleDetail = async (id) => {
  detailVisible.value = true
  detailLoading.value = true
  currentUser.value = null
  try {
    const data = await getAdminUserDetail(id)
    currentUser.value = normalizeUser(data.user ?? data)
  } catch (error) {
    console.error('获取用户详情失败：', error)
    alert(error.message || '获取用户详情失败')
    detailVisible.value = false
  } finally {
    detailLoading.value = false
  }
}

const closeDetail = () => {
  detailVisible.value = false
  currentUser.value = null
}

const handleToggleAdminRole = async () => {
  if (!currentUser.value?.id || isSelfUser(currentUser.value.id)) return
  const targetIsAdmin = !currentUser.value.isAdmin
  const tipText = targetIsAdmin ? '设为管理员' : '取消管理员'
  const confirmed = window.confirm(`确定要${tipText}吗？`)
  if (!confirmed) return
  adminRoleLoading.value = true
  try {
    const res = await updateAdminUserRole(currentUser.value.id, targetIsAdmin)
    alert(`${tipText}成功`)
    currentUser.value = normalizeUser(res.user ?? currentUser.value)
    await Promise.all([getUserPage(), getStatistics()])
  } catch (error) {
    console.error('设置管理员失败：', error)
    alert(error.message || `${tipText}失败`)
  } finally {
    adminRoleLoading.value = false
  }
}

const handleDelete = async (id) => {
  if (isSelfUser(id)) return
  const confirmed = window.confirm('确定删除该用户吗？此操作不可恢复。')
  if (!confirmed) return
  try {
    await deleteAdminUser(id)
    alert('删除成功')
    if (userList.value.length === 1 && queryForm.page > 1) {
      queryForm.page -= 1
    }
    if (currentUser.value?.id === id) {
      closeDetail()
    }
    await Promise.all([getUserPage(), getStatistics()])
  } catch (error) {
    console.error('删除用户失败：', error)
    alert(error.message || '删除用户失败')
  }
}

onMounted(() => {
  getUserPage()
  getStatistics()
})
</script>

<style scoped>
.toolbar-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20px;
  flex-wrap: wrap;
}

.toolbar-left {
  flex: 1;
  min-width: 0;
}

.toolbar-subtitle {
  margin-top: 8px;
  font-size: 14px;
  line-height: 1.8;
  color: #4b5563;
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
  background: #ffffff;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  overflow: hidden;
}

.search-input {
  width: min(280px, 100%);
  height: 44px;
  border: none;
  outline: none;
  padding: 0 14px;
  background: transparent;
  font-size: 14px;
  color: #111827;
}

.search-btn,
.reset-btn,
.page-btn,
.status-select {
  font-family: inherit;
}

.search-btn {
  height: 44px;
  padding: 0 18px;
  border: none;
  cursor: pointer;
  background: #111827;
  color: #ffffff;
  font-size: 14px;
  font-weight: 700;
}

.status-select,
.reset-btn {
  height: 44px;
  min-width: 120px;
  padding: 0 12px;
  border-radius: 12px;
  border: 1px solid #e5e7eb;
  background: #ffffff;
  font-size: 14px;
  font-weight: 600;
  color: #111827;
  cursor: pointer;
}

.reset-btn {
  padding: 0 16px;
  cursor: pointer;
}

.table-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 18px;
  gap: 12px;
  flex-wrap: wrap;
}

.table-tip {
  font-size: 14px;
  color: #4b5563;
  font-weight: 600;
}

.table-wrap {
  width: 100%;
  overflow-x: visible;
}

.user-table {
  width: 100%;
  border-collapse: collapse;
  table-layout: fixed;
}

.user-table thead th {
  text-align: left;
  padding: 14px 12px;
  background: #f9fafb;
  color: #111827;
  font-size: 13px;
  font-weight: 700;
  border-bottom: 1px solid #e5e7eb;
}

.user-table tbody td {
  padding: 14px 12px;
  font-size: 14px;
  color: #111827;
  border-bottom: 1px solid #f3f4f6;
  vertical-align: middle;
}

.user-table tbody tr:last-child td {
  border-bottom: none;
}

.user-table th:nth-child(1),
.user-table td:nth-child(1) { width: 12%; }

.user-table th:nth-child(2),
.user-table td:nth-child(2) { width: 11%; }

.user-table th:nth-child(3),
.user-table td:nth-child(3) { width: 26%; }

.user-table th:nth-child(4),
.user-table td:nth-child(4) { width: 9%; }

.user-table th:nth-child(5),
.user-table td:nth-child(5) { width: 9%; }

.user-table th:nth-child(6),
.user-table td:nth-child(6) { width: 14%; }

.user-table th:nth-child(7),
.user-table td:nth-child(7) { width: 19%; }

.cell-ellipsis {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.cell-email {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  word-break: normal;
}

.role-cell-td {
  text-align: left;
}

.admin-tag,
.detail-admin-tag {
  display: inline-flex;
  align-items: center;
  height: 26px;
  padding: 0 10px;
  border-radius: 999px;
  background: #f3f4f6;
  border: 1px solid #e5e7eb;
  color: #111827;
  font-size: 12px;
  font-weight: 700;
}

.role-text {
  font-size: 14px;
  color: #374151;
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

.status-badge.normal {
  background: #f9fafb;
  color: #111827;
}

.status-badge.disabled {
  background: #fef2f2;
  color: #991b1b;
  border-color: #fecaca;
}

.action-cell {
  white-space: nowrap;
}

.action-group {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.action-btn,
.primary-btn,
.secondary-btn,
.close-btn {
  font-family: inherit;
}

.action-btn {
  height: 32px;
  padding: 0 12px;
  border-radius: 10px;
  cursor: pointer;
  font-size: 13px;
  font-weight: 700;
  border: 1px solid #e5e7eb;
  background: #ffffff;
  color: #111827;
}

.action-btn.detail {
  background: #f9fafb;
}

.action-btn.delete {
  background: #fef2f2;
  color: #991b1b;
  border-color: #fecaca;
}

.empty-box {
  text-align: center;
  padding: 36px 0;
  color: #6b7280;
  font-size: 15px;
  font-weight: 600;
}

.pagination {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 18px;
  flex-wrap: wrap;
}

.page-btn {
  height: 38px;
  padding: 0 14px;
  border-radius: 10px;
  background: #ffffff;
  border: 1px solid #e5e7eb;
  cursor: pointer;
  font-size: 14px;
  font-weight: 700;
  color: #111827;
}

.page-btn:disabled,
.primary-btn:disabled {
  opacity: 0.55;
  cursor: not-allowed;
}

.page-text {
  font-size: 14px;
  font-weight: 600;
  color: #374151;
}

.dialog-mask {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.42);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
  z-index: 999;
}

.dialog-card {
  width: min(720px, 100%);
  background: #ffffff;
  border: 1px solid #e5e7eb;
  border-radius: 18px;
  box-shadow: 0 18px 50px rgba(0, 0, 0, 0.16);
  overflow: hidden;
}

.dialog-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 24px 24px 10px;
  gap: 16px;
}

.dialog-title {
  font-size: 22px;
  font-weight: 800;
  color: #111827;
}

.dialog-subtitle {
  margin-top: 6px;
  color: #6b7280;
  font-size: 14px;
}

.close-btn {
  width: 36px;
  height: 36px;
  border: 1px solid #e5e7eb;
  border-radius: 50%;
  background: #f9fafb;
  cursor: pointer;
  font-size: 20px;
}

.dialog-loading {
  padding: 40px 24px;
  text-align: center;
  color: #6b7280;
  font-weight: 600;
}

.dialog-content {
  padding: 10px 24px 24px;
}

.detail-top {
  display: flex;
  align-items: center;
  gap: 14px;
  padding-bottom: 18px;
  border-bottom: 1px solid #e5e7eb;
}

.detail-avatar {
  width: 60px;
  height: 60px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #111827;
  color: #ffffff;
  font-size: 22px;
  font-weight: 800;
}

.detail-name {
  font-size: 22px;
  font-weight: 800;
  color: #111827;
}

.detail-role {
  font-size: 14px;
  color: #6b7280;
  font-weight: 600;
}

.detail-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px;
  padding-top: 18px;
}

.detail-item {
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding: 14px;
  border-radius: 12px;
  background: #f9fafb;
  border: 1px solid #e5e7eb;
}

.detail-label {
  font-size: 12px;
  color: #6b7280;
  font-weight: 700;
}

.detail-value {
  font-size: 14px;
  color: #111827;
  line-height: 1.6;
  word-break: break-word;
}

.dialog-actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  padding: 0 24px 24px;
}

.primary-btn,
.secondary-btn {
  height: 40px;
  padding: 0 18px;
  border-radius: 10px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 700;
}

.primary-btn {
  border: none;
  background: #111827;
  color: #ffffff;
}

.secondary-btn {
  background: #ffffff;
  color: #111827;
  border: 1px solid #e5e7eb;
}

@media (max-width: 1024px) {
  .user-table th:nth-child(2),
  .user-table td:nth-child(2) { width: 10%; }

  .user-table th:nth-child(3),
  .user-table td:nth-child(3) { width: 24%; }

  .search-input {
    width: 220px;
  }
}

@media (max-width: 768px) {
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

  .user-table .col-nickname,
  .user-table .col-created {
    display: none;
  }

  .user-table th:nth-child(1),
  .user-table td:nth-child(1) { width: 18%; }

  .user-table th:nth-child(3),
  .user-table td:nth-child(3) { width: 30%; }

  .user-table th:nth-child(4),
  .user-table td:nth-child(4) { width: 12%; }

  .user-table th:nth-child(5),
  .user-table td:nth-child(5) { width: 12%; }

  .user-table th:nth-child(7),
  .user-table td:nth-child(7) { width: 28%; }

  .detail-grid {
    grid-template-columns: 1fr;
  }

  .dialog-actions {
    flex-direction: column;
  }

  .primary-btn,
  .secondary-btn {
    width: 100%;
  }
}
</style>
