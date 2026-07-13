<template>
  <div class="admin-page">
    <Header />

    <div class="admin-layout admin-container">
      <AdminSidebar />

      <main ref="mainContentRef" class="main-content">
        <section class="overview-header card">
          <div class="overview-left">
            <button class="ui-back-link admin-back-link" @click="goHome">
              ← 返回首页
            </button>
            <p class="eyebrow">AI Learning Dashboard</p>
            <div class="section-title">学习多智能体系统数据总览</div>
            <div class="section-subtitle">
              展示平台用户、学习路径、评测、资源生成与学习资源的真实统计数据
            </div>
          </div>

          <div class="date-tip">
            统计周期：近 7 天（UTC）
            <span v-if="trendRangeText"> · {{ trendRangeText }}</span>
          </div>
        </section>

        <div v-if="loadError" class="error-banner card">
          <div class="error-text">{{ loadError }}</div>
          <button type="button" class="retry-btn" @click="loadDashboard">重新加载</button>
        </div>

        <section class="stats-grid">
          <div class="stat-card card">
            <div class="stat-label">用户总数</div>
            <div class="stat-value">{{ formatKpi(overview.userCount) }}</div>
            <div class="stat-meta">已构建画像 {{ formatKpi(overview.profileUserCount) }} 人</div>
          </div>

          <div class="stat-card card">
            <div class="stat-label">今日新增用户</div>
            <div class="stat-value">{{ formatKpi(overview.todayUserCount) }}</div>
            <div class="stat-meta">近 7 天新增 {{ formatKpi(overview.last7DaysUserCount) }} 人</div>
          </div>

          <div class="stat-card card">
            <div class="stat-label">评测总次数</div>
            <div class="stat-value">{{ formatKpi(overview.evaluationCount) }}</div>
            <div class="stat-meta">平均评测分 {{ formatScore(overview.averageEvaluationScore) }}</div>
          </div>

          <div class="stat-card card">
            <div class="stat-label">Producer 任务总数</div>
            <div class="stat-value">{{ formatKpi(overview.producerTaskCount) }}</div>
            <div class="stat-meta">成功率 {{ formatRate(overview.producerSuccessRate) }}</div>
          </div>
        </section>

        <div v-if="loading" class="loading-banner card">数据加载中...</div>

        <section v-show="!loading" class="chart-grid">
          <div class="chart-card card large">
            <div class="card-title">最近 7 天用户与路径新增趋势</div>
            <div v-if="hasTrendData" ref="trendChartRef" class="chart-box trend-chart-box"></div>
            <div v-else class="chart-empty">暂无数据</div>
          </div>

          <div class="chart-card card">
            <div class="card-title">Producer 任务状态分布</div>
            <div v-if="hasProducerData" ref="pieChartRef" class="chart-box pie-chart-box"></div>
            <div v-else class="chart-empty">暂无数据</div>
          </div>

          <div class="chart-card card">
            <div class="card-title">评测分数分布</div>
            <div v-if="hasEvaluationData" ref="barChartRef" class="chart-box"></div>
            <div v-else class="chart-empty">暂无数据</div>
          </div>

          <div class="chart-card card">
            <div class="card-title">资源类型分布</div>
            <div v-if="hasResourceTypeData" ref="resourceChartRef" class="chart-box pie-chart-box"></div>
            <div v-else class="chart-empty">暂无数据</div>
          </div>
        </section>

        <section class="table-card card">
          <div class="table-head">
            <div>
              <p class="eyebrow">Business Summary</p>
              <div class="section-title">核心业务数据汇总</div>
            </div>
            <div class="table-tip">基于 overview 真实统计</div>
          </div>

          <div class="table-wrap">
            <table class="data-table">
              <thead>
                <tr>
                  <th>业务模块</th>
                  <th>总量</th>
                  <th>关键指标</th>
                  <th>最近 7 天新增</th>
                  <th>当前状态</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="item in summaryRows" :key="item.name">
                  <td>{{ item.name }}</td>
                  <td>{{ item.total }}</td>
                  <td>{{ item.metric }}</td>
                  <td>{{ item.last7Days }}</td>
                  <td>
                    <span
                      class="status-badge"
                      :class="item.hasData ? 'active' : 'stable'"
                    >
                      {{ item.hasData ? '运行正常' : '暂无数据' }}
                    </span>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </section>
      </main>
    </div>
  </div>
</template>

<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { BarChart, LineChart, PieChart } from 'echarts/charts'
import { GridComponent, LegendComponent, TooltipComponent } from 'echarts/components'
import { init, use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import Header from '../components/AppHeader.vue'
import AdminSidebar from '../components/admin/AdminSidebar.vue'
import '../styles/admin-layout.css'
import { getAdminStatistics } from '../api/admin'

use([BarChart, LineChart, PieChart, GridComponent, LegendComponent, TooltipComponent, CanvasRenderer])

const router = useRouter()

const mainContentRef = ref(null)
const trendChartRef = ref(null)
const pieChartRef = ref(null)
const barChartRef = ref(null)
const resourceChartRef = ref(null)

const loading = ref(false)
const loadError = ref('')
const dataLoaded = ref(false)

const overview = reactive({
  userCount: 0,
  todayUserCount: 0,
  last7DaysUserCount: 0,
  profileUserCount: 0,
  profileCoverageRate: 0,
  pathCount: 0,
  activePathCount: 0,
  completedPathCount: 0,
  averagePathProgress: 0,
  last7DaysPathCount: 0,
  evaluationCount: 0,
  averageEvaluationScore: 0,
  last7DaysEvaluationCount: 0,
  producerTaskCount: 0,
  producerSuccessRate: 0,
  last7DaysProducerTaskCount: 0,
  resourceCount: 0,
  publishedResourceCount: 0,
  last7DaysResourceCount: 0,
})

const trends = reactive({
  dates: [],
  newUsers: [],
  newPaths: [],
  newEvaluations: [],
  newProducerTasks: [],
})

const distributions = reactive({
  producerStatus: [],
  evaluationScoreBuckets: [],
  resourceType: [],
})

let trendChart = null
let pieChart = null
let barChart = null
let resourceChart = null
let mainResizeObserver = null
let animationFrameId = null

const chartColors = ['#111827', '#4b5563', '#6b7280', '#9ca3af', '#d1d5db']

const trendRangeText = computed(() => {
  if (!trends.dates.length) return ''
  return `${trends.dates[0]} - ${trends.dates[trends.dates.length - 1]}`
})

const hasTrendData = computed(() => dataLoaded.value && trends.dates.length === 7)

const hasProducerData = computed(() => (
  dataLoaded.value && distributions.producerStatus.length === 4
))

const hasEvaluationData = computed(() => (
  dataLoaded.value && distributions.evaluationScoreBuckets.length === 4
))

const hasResourceTypeData = computed(() => {
  if (!dataLoaded.value) return false
  return distributions.resourceType.length > 0
})

const summaryRows = computed(() => {
  const rows = [
    {
      name: '学习画像',
      total: overview.profileUserCount,
      metric: `覆盖率 ${formatRate(overview.profileCoverageRate)}`,
      last7Days: '—',
      hasData: overview.profileUserCount > 0,
    },
    {
      name: '学习路径',
      total: overview.pathCount,
      metric: `已完成 ${overview.completedPathCount} / 进行中 ${overview.activePathCount}`,
      last7Days: overview.last7DaysPathCount,
      hasData: overview.pathCount > 0,
    },
    {
      name: '学习评测',
      total: overview.evaluationCount,
      metric: `平均分 ${formatScore(overview.averageEvaluationScore)}`,
      last7Days: overview.last7DaysEvaluationCount,
      hasData: overview.evaluationCount > 0,
    },
    {
      name: '资源生成',
      total: overview.producerTaskCount,
      metric: `成功率 ${formatRate(overview.producerSuccessRate)}`,
      last7Days: overview.last7DaysProducerTaskCount,
      hasData: overview.producerTaskCount > 0,
    },
    {
      name: '学习资源',
      total: overview.resourceCount,
      metric: `已发布 ${overview.publishedResourceCount}`,
      last7Days: overview.last7DaysResourceCount,
      hasData: overview.resourceCount > 0,
    },
  ]
  if (!dataLoaded.value && loading.value) {
    return rows.map((row) => ({
      ...row,
      total: '—',
      metric: '—',
      last7Days: '—',
      hasData: false,
    }))
  }
  return rows.map((row) => ({
    ...row,
    total: formatKpi(row.total),
    last7Days: row.last7Days === '—' ? '—' : formatKpi(row.last7Days),
  }))
})

const goHome = () => {
  router.push('/')
}

const formatKpi = (value) => {
  if (!dataLoaded.value && loading.value) return '—'
  const num = Number(value ?? 0)
  return Number.isFinite(num) ? String(num) : '0'
}

const formatScore = (value) => {
  if (!dataLoaded.value && loading.value) return '—'
  const num = Number(value ?? 0)
  return Number.isFinite(num) ? num.toFixed(1) : '0.0'
}

const formatRate = (value) => {
  if (!dataLoaded.value && loading.value) return '—'
  const num = Number(value ?? 0)
  return Number.isFinite(num) ? `${num.toFixed(1)}%` : '0.0%'
}

const applyOverview = (source = {}) => {
  Object.assign(overview, {
    userCount: source.userCount ?? 0,
    todayUserCount: source.todayUserCount ?? 0,
    last7DaysUserCount: source.last7DaysUserCount ?? 0,
    profileUserCount: source.profileUserCount ?? 0,
    profileCoverageRate: source.profileCoverageRate ?? 0,
    pathCount: source.pathCount ?? 0,
    activePathCount: source.activePathCount ?? 0,
    completedPathCount: source.completedPathCount ?? 0,
    averagePathProgress: source.averagePathProgress ?? 0,
    last7DaysPathCount: source.last7DaysPathCount ?? 0,
    evaluationCount: source.evaluationCount ?? 0,
    averageEvaluationScore: source.averageEvaluationScore ?? 0,
    last7DaysEvaluationCount: source.last7DaysEvaluationCount ?? 0,
    producerTaskCount: source.producerTaskCount ?? 0,
    producerSuccessRate: source.producerSuccessRate ?? 0,
    last7DaysProducerTaskCount: source.last7DaysProducerTaskCount ?? 0,
    resourceCount: source.resourceCount ?? 0,
    publishedResourceCount: source.publishedResourceCount ?? 0,
    last7DaysResourceCount: source.last7DaysResourceCount ?? 0,
  })
}

const applyTrends = (source = {}) => {
  trends.dates = Array.isArray(source.dates) ? [...source.dates] : []
  trends.newUsers = Array.isArray(source.newUsers) ? [...source.newUsers] : []
  trends.newPaths = Array.isArray(source.newPaths) ? [...source.newPaths] : []
  trends.newEvaluations = Array.isArray(source.newEvaluations) ? [...source.newEvaluations] : []
  trends.newProducerTasks = Array.isArray(source.newProducerTasks) ? [...source.newProducerTasks] : []
}

const applyDistributions = (source = {}) => {
  distributions.producerStatus = Array.isArray(source.producerStatus) ? [...source.producerStatus] : []
  distributions.evaluationScoreBuckets = Array.isArray(source.evaluationScoreBuckets)
    ? [...source.evaluationScoreBuckets]
    : []
  distributions.resourceType = Array.isArray(source.resourceType) ? [...source.resourceType] : []
}

const disposeCharts = () => {
  trendChart?.dispose()
  pieChart?.dispose()
  barChart?.dispose()
  resourceChart?.dispose()
  trendChart = null
  pieChart = null
  barChart = null
  resourceChart = null
}

const safeResizeCharts = () => {
  if (animationFrameId) cancelAnimationFrame(animationFrameId)
  animationFrameId = requestAnimationFrame(() => {
    trendChart?.resize()
    pieChart?.resize()
    barChart?.resize()
    resourceChart?.resize()
  })
}

const initTrendChart = () => {
  if (!trendChartRef.value) return
  trendChart?.dispose()
  trendChart = init(trendChartRef.value)
  trendChart.setOption({
    color: ['#111827', '#6b7280'],
    tooltip: { trigger: 'axis', confine: true },
    legend: { top: 12, left: 'center', textStyle: { color: '#111827' } },
    grid: { left: '4%', right: '6%', bottom: '6%', top: 76, containLabel: true },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: trends.dates,
      axisLine: { lineStyle: { color: '#e5e7eb' } },
      axisLabel: { color: '#4b5563' },
    },
    yAxis: {
      type: 'value',
      minInterval: 1,
      splitLine: { lineStyle: { color: '#e5e7eb' } },
      axisLabel: { color: '#4b5563' },
    },
    series: [
      {
        name: '新增用户',
        type: 'line',
        smooth: 0.35,
        data: trends.newUsers,
        lineStyle: { width: 3 },
        areaStyle: { opacity: 0.08 },
      },
      {
        name: '新增路径',
        type: 'line',
        smooth: 0.35,
        data: trends.newPaths,
        lineStyle: { width: 3 },
        areaStyle: { opacity: 0.06 },
      },
    ],
  })
}

const initProducerChart = () => {
  if (!pieChartRef.value) return
  pieChart?.dispose()
  pieChart = init(pieChartRef.value)
  pieChart.setOption({
    color: chartColors,
    tooltip: { trigger: 'item', confine: true },
    legend: {
      orient: 'vertical',
      right: 4,
      top: 'center',
      textStyle: { color: '#111827', fontSize: 12 },
    },
    series: [
      {
        name: '任务状态',
        type: 'pie',
        radius: ['40%', '62%'],
        center: ['36%', '50%'],
        data: distributions.producerStatus.map((item) => ({
          name: item.name,
          value: item.value,
        })),
        label: { formatter: '{b}: {c}', color: '#4b5563' },
      },
    ],
  })
}

const initEvaluationChart = () => {
  if (!barChartRef.value) return
  barChart?.dispose()
  barChart = init(barChartRef.value)
  barChart.setOption({
    color: ['#111827'],
    tooltip: { trigger: 'axis', confine: true },
    grid: { left: '6%', right: '6%', bottom: '10%', top: 40, containLabel: true },
    xAxis: {
      type: 'category',
      data: distributions.evaluationScoreBuckets.map((item) => item.name),
      axisLabel: { color: '#4b5563' },
      axisLine: { lineStyle: { color: '#e5e7eb' } },
    },
    yAxis: {
      type: 'value',
      minInterval: 1,
      splitLine: { lineStyle: { color: '#e5e7eb' } },
      axisLabel: { color: '#4b5563' },
    },
    series: [
      {
        name: '评测次数',
        type: 'bar',
        barWidth: 36,
        data: distributions.evaluationScoreBuckets.map((item) => item.value),
        itemStyle: { borderRadius: [8, 8, 0, 0] },
      },
    ],
  })
}

const initResourceChart = () => {
  if (!resourceChartRef.value) return
  resourceChart?.dispose()
  resourceChart = init(resourceChartRef.value)
  resourceChart.setOption({
    color: chartColors,
    tooltip: { trigger: 'item', confine: true },
    legend: {
      orient: 'vertical',
      right: 4,
      top: 'center',
      textStyle: { color: '#111827', fontSize: 12 },
    },
    series: [
      {
        name: '资源类型',
        type: 'pie',
        radius: ['40%', '62%'],
        center: ['36%', '50%'],
        data: distributions.resourceType.map((item) => ({
          name: item.name,
          value: item.value,
        })),
        label: { formatter: '{b}: {c}', color: '#4b5563' },
      },
    ],
  })
}

const renderCharts = async () => {
  await nextTick()
  if (hasTrendData.value) initTrendChart()
  if (hasProducerData.value) initProducerChart()
  if (hasEvaluationData.value) initEvaluationChart()
  if (hasResourceTypeData.value) initResourceChart()
  safeResizeCharts()
}

const loadDashboard = async () => {
  loading.value = true
  loadError.value = ''
  dataLoaded.value = false
  disposeCharts()
  try {
    const data = await getAdminStatistics()
    applyOverview(data.overview || data)
    applyTrends(data.trends || {})
    applyDistributions(data.distributions || {})
    dataLoaded.value = true
    loading.value = false
    await renderCharts()
  } catch (error) {
    console.error('加载数据总览失败：', error)
    loadError.value = error?.message || '加载数据总览失败，请稍后重试'
    loading.value = false
    dataLoaded.value = false
  }
}

const initResizeObserver = () => {
  const resizeHandler = () => safeResizeCharts()
  if (window.ResizeObserver && mainContentRef.value) {
    mainResizeObserver = new ResizeObserver(resizeHandler)
    mainResizeObserver.observe(mainContentRef.value)
  } else {
    window.addEventListener('resize', resizeHandler)
  }
}

onMounted(async () => {
  initResizeObserver()
  await loadDashboard()
})

onBeforeUnmount(() => {
  mainResizeObserver?.disconnect()
  mainResizeObserver = null
  window.removeEventListener('resize', safeResizeCharts)
  if (animationFrameId) {
    cancelAnimationFrame(animationFrameId)
    animationFrameId = null
  }
  disposeCharts()
})
</script>

<style scoped>
.card {
  position: relative;
  overflow: hidden;
  background: #ffffff;
  border: 1px solid #e5e7eb;
  border-radius: 18px;
  padding: 28px;
  box-shadow: var(--shadow-md);
}

.overview-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  flex-wrap: wrap;
}

.overview-left {
  flex: 1;
  min-width: 0;
}

.eyebrow {
  margin: 0 0 10px;
  font-size: 13px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: #111827;
}

.section-title {
  font-size: 22px;
  line-height: 1.35;
  font-weight: 800;
  color: #111827;
}

.section-subtitle {
  margin-top: 10px;
  max-width: 760px;
  line-height: 1.8;
  font-size: 14px;
  color: #4b5563;
}

.date-tip {
  font-size: 13px;
  color: #374151;
  background: #f3f4f6;
  border: 1px solid #e5e7eb;
  padding: 10px 14px;
  border-radius: 999px;
  font-weight: 600;
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

.error-text {
  color: #991b1b;
  font-size: 14px;
  font-weight: 600;
}

.retry-btn {
  transition: background 0.2s ease, border-color 0.2s ease;
}

.retry-btn {
  height: 36px;
  padding: 0 14px;
  border: 1px solid #e5e7eb;
  border-radius: 10px;
  background: #ffffff;
  color: #111827;
  font-size: 13px;
  font-weight: 700;
  cursor: pointer;
  font-family: inherit;
}

.retry-btn:hover {
  background: #f9fafb;
}

.loading-banner {
  text-align: center;
  color: #4b5563;
  font-size: 14px;
  font-weight: 600;
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
  margin-bottom: 12px;
  font-weight: 700;
}

.stat-value {
  font-size: 32px;
  line-height: 1;
  font-weight: 800;
  color: #111827;
}

.stat-meta {
  margin-top: 14px;
  font-size: 13px;
  color: #6b7280;
  font-weight: 600;
}

.chart-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 24px;
}

.chart-card.large {
  grid-column: span 2;
}

.card-title {
  font-size: 18px;
  font-weight: 800;
  color: #111827;
  margin-bottom: 18px;
}

.chart-box {
  width: 100%;
  height: 360px;
  overflow: hidden;
}

.pie-chart-box {
  height: 360px;
}

.chart-empty {
  height: 360px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #6b7280;
  font-size: 14px;
  font-weight: 600;
  background: #f9fafb;
  border: 1px dashed #e5e7eb;
  border-radius: 14px;
}

.table-card {
  padding-top: 24px;
}

.table-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  margin-bottom: 18px;
  gap: 12px;
  flex-wrap: wrap;
}

.table-tip {
  font-size: 13px;
  color: #374151;
  background: #f3f4f6;
  border: 1px solid #e5e7eb;
  padding: 8px 12px;
  border-radius: 999px;
  font-weight: 600;
}

.table-wrap {
  width: 100%;
  overflow-x: auto;
}

.data-table {
  width: 100%;
  table-layout: fixed;
  border-collapse: collapse;
  background: #ffffff;
  border: 1px solid #e5e7eb;
  border-radius: 14px;
  overflow: hidden;
}

.data-table thead th {
  text-align: left;
  padding: 14px 16px;
  background: #f9fafb;
  color: #111827;
  font-size: 13px;
  font-weight: 700;
  border-bottom: 1px solid #e5e7eb;
}

.data-table tbody td {
  padding: 14px 16px;
  font-size: 14px;
  color: #111827;
  border-bottom: 1px solid #f3f4f6;
  vertical-align: middle;
  word-break: break-word;
}

.data-table tbody tr:last-child td {
  border-bottom: none;
}

.status-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 72px;
  height: 28px;
  padding: 0 10px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 700;
  white-space: nowrap;
  border: 1px solid #e5e7eb;
}

.status-badge.active {
  background: #111827;
  color: #ffffff;
  border-color: #111827;
}

.status-badge.stable {
  background: #f3f4f6;
  color: #374151;
}

@media (max-width: 1200px) {
  .stats-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 992px) {
  .chart-grid {
    grid-template-columns: 1fr;
  }

  .chart-card.large {
    grid-column: span 1;
  }
}

@media (max-width: 768px) {
  .stats-grid {
    grid-template-columns: 1fr;
  }

  .chart-box,
  .pie-chart-box,
  .chart-empty {
    height: 300px;
  }

  .admin-back-link {
    width: 100%;
    justify-content: center;
  }
}
</style>
