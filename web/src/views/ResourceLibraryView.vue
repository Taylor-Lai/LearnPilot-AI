<template>
  <div class="resource-page">
    <!-- Sidebar -->
    <aside class="resource-sidebar">
      <div class="sidebar-title">资源库</div>

      <button
        v-for="item in typeList"
        :key="item.value"
        class="sidebar-link"
        :class="{ active: activeType === item.value }"
        @click="activeType = item.value"
      >
        {{ item.label }}
      </button>

      <div class="sidebar-footer">
        <RouterLink to="/" class="ui-back-link ui-back-link--block sidebar-home-link">
          ← 返回首页
        </RouterLink>
      </div>
    </aside>

    <!-- Content -->
    <main class="resource-content">

      <!-- Hero -->
      <section class="hero-card">
        <p class="eyebrow">AI Resource Center</p>
        <h1>人工智能学习资源库</h1>
        <p>
          高质量课程资源、学习资料与实践案例统一管理与展示
        </p>
      </section>

      <!-- Filter -->
      <section class="filter-card">
        <input
          v-model.trim="keyword"
          class="search-box"
          placeholder="搜索资源名称 / 关键词 / 描述"
        />

        <div class="filter-row">
          <button
            v-for="category in categoryList"
            :key="category"
            class="filter-tag"
            :class="{ active: activeCategory === category }"
            @click="activeCategory = category"
          >
            {{ category }}
          </button>
        </div>
      </section>

      <!-- Header -->
      <section class="section-header">
        <div>
          <h2>{{ currentTypeLabel }}</h2>
          <p v-if="!loading">共 {{ totalResources }} 个资源</p>
          <p v-else>加载中...</p>
        </div>

        <select v-model="sortType" class="sort-select">
          <option value="default">默认排序</option>
          <option value="latest">最新优先</option>
          <option value="hot">热门优先</option>
        </select>
      </section>

      <!-- Loading -->
      <div v-if="loading" class="state-box">加载中...</div>
      <div v-else-if="error" class="state-box error">{{ error }}</div>

      <!-- Grid -->
      <section v-else-if="paginatedResources.length" class="resource-grid">
        <article
          v-for="item in paginatedResources"
          :key="item.id"
          class="resource-card"
        >
          <div class="card-content">
            <div class="top">
              <span class="type">{{ item.typeLabel || item.type }}</span>
              <span class="level">{{ item.level || '基础' }}</span>
            </div>

            <h3>{{ item.title }}</h3>
            <p class="desc">{{ item.desc }}</p>

            <div class="tags">
              <span v-for="tag in (item.tags || [])" :key="tag">
                {{ tag }}
              </span>
            </div>

            <div class="meta">
              <span>{{ item.date }}</span>
              <span>{{ item.views }} 次学习</span>
            </div>
          </div>

          <button class="btn" @click="openResource(item)">
            查看资源
          </button>
        </article>
      </section>

      <div v-else class="state-box">暂无资源</div>

      <!-- 分页组件 -->
      <div v-if="!loading && totalPages > 1" class="pagination">
        <button
          class="page-btn"
          :disabled="currentPage === 1"
          @click="currentPage--"
        >
          ← 上一页
        </button>

        <div class="page-numbers">
          <button
            v-for="page in visiblePages"
            :key="page"
            class="page-num"
            :class="{ active: currentPage === page }"
            @click="currentPage = page"
          >
            {{ page }}
          </button>
        </div>

        <button
          class="page-btn"
          :disabled="currentPage === totalPages"
          @click="currentPage++"
        >
          下一页 →
        </button>
      </div>
    </main>

    <!-- 文档内容模态框 -->
    <Teleport to="body">
      <div v-if="showModal" class="modal-overlay" @click.self="closeModal">
        <div class="modal-container">
          <div class="modal-header">
            <h3>{{ modalTitle }}</h3>
            <button class="modal-close" @click="closeModal">✕</button>
          </div>
          <div class="modal-body">
            <div class="markdown-content" v-html="renderedContent"></div>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { RouterLink, useRoute, useRouter } from 'vue-router'
import { getResourceList, getResourceDetail, viewResource } from '../api/resource'
import { marked } from 'marked'

const route = useRoute()
const router = useRouter()

// 配置 marked 选项
marked.setOptions({
  breaks: true,
  gfm: true,
  headerIds: false,
  mangle: false
})

const activeType = ref('all')
const activeCategory = ref('全部')
const keyword = ref('')
const sortType = ref('default')

const resources = ref([])
const loading = ref(false)
const error = ref('')

// 分页相关
const currentPage = ref(1)
const pageSize = 6 // 每页6个资源（2行 × 3列）

// 模态框相关
const showModal = ref(false)
const modalTitle = ref('')
const modalRawContent = ref('')

// 计算渲染后的 HTML 内容
const renderedContent = computed(() => {
  if (!modalRawContent.value) return ''
  try {
    return marked(modalRawContent.value)
  } catch (e) {
    console.error('Markdown 渲染失败：', e)
    return `<pre>${modalRawContent.value}</pre>`
  }
})

// 分页后的资源
const paginatedResources = computed(() => {
  const start = (currentPage.value - 1) * pageSize
  const end = start + pageSize
  return resources.value.slice(start, end)
})

// 总资源数
const totalResources = computed(() => resources.value.length)

// 总页数
const totalPages = computed(() => Math.ceil(totalResources.value / pageSize))

// 可见的页码（最多显示5个）
const visiblePages = computed(() => {
  const maxVisible = 5
  const half = Math.floor(maxVisible / 2)
  let start = Math.max(1, currentPage.value - half)
  let end = Math.min(totalPages.value, start + maxVisible - 1)

  if (end - start + 1 < maxVisible) {
    start = Math.max(1, end - maxVisible + 1)
  }

  const pages = []
  for (let i = start; i <= end; i++) {
    pages.push(i)
  }
  return pages
})

const typeList = [
  { label: '全部资源', value: 'all' },
  { label: '文档', value: 'document' },
  { label: 'PPT', value: 'ppt' },
  { label: '视频', value: 'video' },
]

const categoryList = [
  '全部',
  '人工智能基础',
  '机器学习',
  '深度学习',
  '自然语言处理',
  '计算机视觉',
  '大模型应用',
]

const currentTypeLabel = computed(() =>
  typeList.find(i => i.value === activeType.value)?.label || '全部资源'
)

const formatResource = (item = {}) => ({
  ...item,
  title: item.title || '未命名资源',
  desc: item.description || item.desc || '暂无描述',
  date: item.created_at ? String(item.created_at).slice(0, 10) : '',
  views: item.views ?? 0,
  likes: item.likes ?? 0,
  open_type: item.open_type,
  detail_url: item.detail_url,
  url: item.url || item.detail_url || '',
  typeLabel:
    item.type === 'document' ? '文档' :
    item.type === 'ppt' ? 'PPT' :
    item.type === 'video' ? '视频' :
    item.type || '资源',
  tags: item.category ? [item.category] : []
})

const fetchResources = async () => {
  loading.value = true
  error.value = ''

  try {
    const typeParam = activeType.value === 'all' ? 'all' : activeType.value
    const categoryParam = activeCategory.value === '全部' ? '' : activeCategory.value

    const res = await getResourceList({
      type: typeParam,
      category: categoryParam,
      keyword: keyword.value,
      sort: sortType.value,
    })

    const list = Array.isArray(res?.items)
      ? res.items
      : Array.isArray(res?.data?.items)
        ? res.data.items
        : Array.isArray(res?.data?.list)
          ? res.data.list
          : Array.isArray(res)
            ? res
            : []

    resources.value = list.map(formatResource)
    // 重置到第一页
    currentPage.value = 1
  } catch (e) {
    console.error('获取资源列表失败：', e)
    error.value = e.message || '加载失败'
    resources.value = []
  } finally {
    loading.value = false
  }
}

// 关闭模态框
const closeModal = () => {
  showModal.value = false
  modalRawContent.value = ''
  modalTitle.value = ''
}

// 展示文档内容
const showDocumentContent = async (item) => {
  try {
    const detailRes = await getResourceDetail(item.id)
    const content = detailRes?.data?.content || detailRes?.content

    if (content) {
      modalTitle.value = item.title || '文档内容'
      modalRawContent.value = content
      showModal.value = true
    } else {
      error.value = '无法获取文档内容'
      setTimeout(() => {
        error.value = ''
      }, 3000)
    }
  } catch (e) {
    console.error('获取文档详情失败：', e)
    error.value = e.message || '加载文档内容失败'
    setTimeout(() => {
      error.value = ''
    }, 3000)
  }
}

const openResource = async (item) => {
  try {
    if (item.id) {
      await viewResource(item.id)
      item.views = (item.views || 0) + 1
    }
  } catch (e) {
    console.warn('增加浏览量失败：', e)
  }

  const targetUrl = String(item.url || item.detail_url || '')
  const isInternalDetail = /^\/resources\/\d+\/view(?:[?#].*)?$/.test(targetUrl)

  if (item.open_type === 'content' || isInternalDetail) {
    await showDocumentContent(item)
  } else if (targetUrl) {
    window.open(targetUrl, '_blank', 'noopener,noreferrer')
  } else {
    error.value = '该资源暂无可打开的链接'
    setTimeout(() => {
      error.value = ''
    }, 3000)
  }
}

const openRequestedResource = async () => {
  const resourceId = Number(route.query.open)
  if (!Number.isInteger(resourceId) || resourceId <= 0) return
  const matched = resources.value.find(item => Number(item.id) === resourceId)
  await showDocumentContent(matched || { id: resourceId, title: '学习资源' })
  const query = { ...route.query }
  delete query.open
  await router.replace({ path: '/resources', query })
}

onMounted(async () => {
  await fetchResources()
  await openRequestedResource()
})

watch([activeType, activeCategory, keyword, sortType], () => {
  fetchResources()
})
</script>

<style scoped>
.resource-page {
  display: flex;
  min-height: 100vh;
  background: #f7f8fa;
  gap: 28px;
  padding: 32px;
}

/* Sidebar */
.resource-sidebar {
  width: 260px;
  flex-shrink: 0;
  position: sticky;
  top: 28px;
  height: fit-content;
  background: #ffffff;
  border: 1px solid #e5e7eb;
  border-radius: 18px;
  padding: 18px;
  box-shadow: var(--shadow-md);
}

.sidebar-title {
  font-size: 20px;
  font-weight: 800;
  margin-bottom: 14px;
}

.sidebar-link {
  width: 100%;
  padding: 12px 14px;
  margin: 6px 0;
  border-radius: 14px;
  border: none;
  background: transparent;
  text-align: left;
  cursor: pointer;
  font-weight: 600;
  transition: 0.2s;
}

.sidebar-link:hover {
  background: #f1f5f9;
  transform: translateX(4px);
}

.sidebar-link.active {
  background: #111827;
  color: #fff;
}

.sidebar-footer {
  margin-top: 12px;
}

.sidebar-home-link.ui-back-link--block {
  color: #ffffff;
  background: #111827;
}

.sidebar-home-link.ui-back-link--block:hover {
  color: #ffffff;
  background: #1f2937;
}

/* Content */
.resource-content {
  flex: 1;
  min-width: 0;
  max-width: 1050px;
}

/* Hero */
.hero-card {
  background: #fff;
  border: 1px solid #e5e7eb;
  border-radius: 18px;
  padding: 34px;
  margin-bottom: 20px;
  box-shadow: var(--shadow-md);
}

.eyebrow {
  font-size: 13px;
  font-weight: 700;
  letter-spacing: .08em;
}

.hero-card h1 {
  font-size: 32px;
  margin: 10px 0;
}

/* Filter */
.filter-card {
  background: #fff;
  border-radius: 18px;
  padding: 18px;
  margin-bottom: 20px;
  border: 1px solid #e5e7eb;
}

.search-box {
  width: 100%;
  padding: 12px;
  border-radius: 12px;
  border: 1px solid #e5e7eb;
  margin-bottom: 12px;
}

.filter-row {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.filter-tag {
  padding: 6px 12px;
  border-radius: 999px;
  border: 1px solid #e5e7eb;
  background: #fff;
  cursor: pointer;
  font-weight: 600;
}

.filter-tag.active {
  background: #111827;
  color: #fff;
}

/* Header */
.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin: 18px 0;
}

.sort-select {
  padding: 8px 12px;
  border-radius: 10px;
  border: 1px solid #e5e7eb;
  background: #fff;
  cursor: pointer;
}

/* Grid */
.resource-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 20px;
}

.resource-card {
  background: #fff;
  border: 1px solid #e5e7eb;
  border-radius: 18px;
  padding: 20px;
  box-shadow: 0 10px 24px rgba(0,0,0,0.04);
  transition: .2s;
  display: flex;
  flex-direction: column;
  min-height: 280px;
}

.resource-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 16px 32px rgba(0,0,0,0.08);
}

.card-content {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.top {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  margin-bottom: 12px;
}

.type {
  color: #000;
  font-weight: 700;
}

.level {
  color: #888;
}

.resource-card h3 {
  font-size: 18px;
  margin: 0 0 8px 0;
  font-weight: 600;
  line-height: 1.4;
}

.desc {
  font-size: 13px;
  color: #666;
  line-height: 1.5;
  display: -webkit-box;
  -webkit-box-orient: vertical;
  overflow: hidden;
  margin: 0 0 12px 0;
}

.tags {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
  margin: 0 0 12px 0;
}

.tags span {
  font-size: 11px;
  padding: 3px 10px;
  border-radius: 999px;
  background: #f3f4f6;
  color: #374151;
}

.meta {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  color: #888;
  margin: 0 0 16px 0;
}

.btn {
  width: 100%;
  padding: 10px;
  border-radius: 10px;
  border: none;
  background: #111827;
  color: #fff;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  margin-top: auto;
}

.btn:hover {
  opacity: 0.85;
  transform: translateY(-1px);
}

/* 分页样式 */
.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 16px;
  margin-top: 32px;
  padding: 20px 0;
}

.page-btn {
  padding: 8px 16px;
  border-radius: 10px;
  border: 1px solid #e5e7eb;
  background: #fff;
  cursor: pointer;
  font-weight: 500;
  transition: all 0.2s;
}

.page-btn:hover:not(:disabled) {
  background: #111827;
  color: #fff;
  border-color: #111827;
}

.page-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.page-numbers {
  display: flex;
  gap: 8px;
}

.page-num {
  width: 40px;
  height: 40px;
  border-radius: 10px;
  border: 1px solid #e5e7eb;
  background: #fff;
  cursor: pointer;
  font-weight: 500;
  transition: all 0.2s;
}

.page-num:hover {
  border-color: #111827;
  background: #f9fafb;
}

.page-num.active {
  background: #111827;
  color: #fff;
  border-color: #111827;
}

.state-box {
  text-align: center;
  padding: 60px;
  color: #888;
}

.state-box.error {
  color: #dc2626;
}

/* 模态框样式 */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-container {
  background: white;
  border-radius: 18px;
  width: 90%;
  max-width: 900px;
  max-height: 85vh;
  display: flex;
  flex-direction: column;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.2);
  animation: modalFadeIn 0.2s ease;
}

@keyframes modalFadeIn {
  from {
    opacity: 0;
    transform: scale(0.95);
  }
  to {
    opacity: 1;
    transform: scale(1);
  }
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid #e5e7eb;
}

.modal-header h3 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
}

.modal-close {
  background: none;
  border: none;
  font-size: 24px;
  cursor: pointer;
  padding: 0;
  width: 32px;
  height: 32px;
  border-radius: 8px;
  transition: background 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
}

.modal-close:hover {
  background: #f3f4f6;
}

.modal-body {
  padding: 24px;
  overflow-y: auto;
  flex: 1;
}

/* Markdown 内容样式 */
.markdown-content {
  line-height: 1.6;
  color: #1f2937;
}

.markdown-content h1 {
  font-size: 28px;
  margin: 24px 0 16px;
  padding-bottom: 8px;
  border-bottom: 1px solid #e5e7eb;
}

.markdown-content h2 {
  font-size: 24px;
  margin: 20px 0 12px;
  padding-bottom: 6px;
  border-bottom: 1px solid #e5e7eb;
}

.markdown-content h3 {
  font-size: 20px;
  margin: 16px 0 10px;
}

.markdown-content h4 {
  font-size: 18px;
  margin: 14px 0 8px;
}

.markdown-content p {
  margin: 12px 0;
}

.markdown-content ul,
.markdown-content ol {
  margin: 12px 0;
  padding-left: 28px;
}

.markdown-content li {
  margin: 6px 0;
}

.markdown-content code {
  background: #f3f4f6;
  padding: 2px 6px;
  border-radius: 4px;
  font-family: 'Courier New', monospace;
  font-size: 0.9em;
}

.markdown-content pre {
  background: #1f2937;
  color: #f3f4f6;
  padding: 16px;
  border-radius: 8px;
  overflow-x: auto;
  margin: 16px 0;
}

.markdown-content pre code {
  background: transparent;
  padding: 0;
  color: inherit;
}

.markdown-content blockquote {
  border-left: 4px solid #000;
  margin: 16px 0;
  padding: 8px 0 8px 20px;
  color: #6b7280;
  font-style: italic;
}

.markdown-content a {
  color: #2563eb;
  text-decoration: none;
}

.markdown-content a:hover {
  text-decoration: underline;
}

.markdown-content table {
  border-collapse: collapse;
  width: 100%;
  margin: 16px 0;
}

.markdown-content th,
.markdown-content td {
  border: 1px solid #e5e7eb;
  padding: 10px 12px;
  text-align: left;
}

.markdown-content th {
  background: #f9fafb;
  font-weight: 600;
}

.markdown-content img {
  max-width: 100%;
  height: auto;
  border-radius: 8px;
}

.markdown-content hr {
  border: none;
  border-top: 1px solid #e5e7eb;
  margin: 20px 0;
}

@media (max-width: 900px) {
  .resource-page {
    display: block;
    padding: 20px;
  }

  .resource-sidebar {
    position: static;
    width: 100%;
    margin-bottom: 20px;
  }

  .resource-sidebar nav {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
  }

  .sidebar-link {
    width: auto;
    margin: 0;
  }

  .sidebar-footer {
    max-width: 220px;
  }

  .resource-content {
    width: 100%;
    max-width: none;
  }

  .resource-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 640px) {
  .resource-page {
    padding: 14px;
  }

  .resource-sidebar,
  .hero-card,
  .filter-card {
    border-radius: 14px;
  }

  .resource-sidebar {
    padding: 14px;
  }

  .sidebar-title {
    margin-bottom: 10px;
    font-size: 18px;
  }

  .sidebar-link {
    flex: 1 1 96px;
    padding: 10px 12px;
    text-align: center;
  }

  .sidebar-footer {
    max-width: none;
  }

  .hero-card {
    padding: 24px 18px;
  }

  .hero-card h1 {
    font-size: 26px;
  }

  .section-header {
    align-items: flex-start;
    gap: 12px;
  }

  .resource-grid {
    grid-template-columns: 1fr;
  }

  .state-box {
    padding: 40px 16px;
  }

  .modal-container {
    width: calc(100% - 24px);
    max-height: 90vh;
  }

  .modal-body {
    padding: 18px;
  }
}

/* Unified product visual language */
.resource-page { justify-content: center; background: transparent; }
.resource-sidebar { border-radius: 24px; border-color: var(--border-default); }
.sidebar-link.active { background: linear-gradient(135deg, var(--accent-primary), #5046dc); box-shadow: 0 8px 18px rgba(99,91,255,.2); }
.resource-content { max-width: 1120px; }
.hero-card { position: relative; overflow: hidden; padding: 40px; border: 0; border-radius: 24px; background: linear-gradient(135deg, #171b2e, #292654 58%, #4338ca); }
.hero-card::after { position: absolute; right: -70px; top: -90px; width: 260px; height: 260px; border: 55px solid rgba(255,255,255,.07); border-radius: 50%; content: ""; }
.hero-card .eyebrow { color: #b9b5ff; }
.hero-card h1 { position: relative; z-index: 1; color: #fff; }
.hero-card p { position: relative; z-index: 1; color: rgba(255,255,255,.72); }
.filter-card, .resource-card { border-radius: 20px; border-color: var(--border-default); }
.filter-tag.active { border-color: var(--accent-primary); background: var(--accent-soft); color: var(--accent-primary); }
.resource-card:hover { border-color: #d9d6ff; box-shadow: 0 18px 38px rgba(65,57,140,.12); }

</style>
