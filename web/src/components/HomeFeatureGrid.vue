<template>
  <section class="capability-section">
    <div class="section-heading">
      <div>
        <span class="section-kicker">完整学习闭环</span>
        <h2>不是工具堆叠，而是一套持续进化的学习系统</h2>
      </div>
      <p>画像、资源、路径、辅导和评估共享同一份学习状态，每次互动都会让下一次推荐更准确。</p>
    </div>

    <div class="capability-grid">
      <RouterLink
        v-for="(item, index) in cards"
        :key="item.title"
        class="capability-card"
        :class="`card-${index + 1}`"
        :to="item.path"
      >
        <div class="card-top">
          <span class="icon-wrap" :style="{ color: item.color, background: item.soft }">
            <component :is="item.icon" :size="22" :stroke-width="2" />
          </span>
          <span class="step-label">0{{ index + 1 }}</span>
        </div>
        <h3>{{ item.title }}</h3>
        <p>{{ item.description }}</p>
        <div class="feature-tags">
          <span v-for="tag in item.tags" :key="tag">{{ tag }}</span>
        </div>
        <strong class="card-link">进入模块 <ArrowUpRight :size="16" /></strong>
      </RouterLink>
    </div>

    <div class="system-proof">
      <div class="proof-copy">
        <span>LEARNPILOT INTELLIGENCE LAYER</span>
        <h3>每一次生成都有依据，每一个建议都能追踪</h3>
        <p>课程知识库检索、引用完整性审核、内容安全过滤和智能体执行轨迹共同构成可信生成链路。</p>
      </div>
      <div class="proof-metrics">
        <article><strong>8+</strong><span>动态画像维度</span></article>
        <article><strong>7</strong><span>资源交付类型</span></article>
        <article><strong>5</strong><span>协同智能体角色</span></article>
        <article><strong>100%</strong><span>生成过程可追踪</span></article>
      </div>
    </div>
  </section>
</template>

<script setup>
import { RouterLink } from 'vue-router'
import {
  ArrowUpRight,
  Bot,
  ChartColumnIncreasing,
  LibraryBig,
  Route,
  UserRoundSearch,
} from 'lucide-vue-next'

const cards = [
  {
    icon: UserRoundSearch,
    title: '对话式学习画像',
    path: '/profile-builder',
    description: '用自然对话理解专业背景、知识基础、认知风格、薄弱点与学习偏好。',
    tags: ['8+ 维度', '动态更新', '行为融合'],
    color: '#4f46d8',
    soft: '#eeecff',
  },
  {
    icon: LibraryBig,
    title: '多智能体资源生成',
    path: '/multi-agent-resource',
    description: '多角色智能体协作生成讲义、导图、习题、视频、阅读材料与代码案例。',
    tags: ['7 类资源', '引用约束', '质量复审'],
    color: '#1778cf',
    soft: '#eaf4ff',
  },
  {
    icon: Route,
    title: '个性化学习路径',
    path: '/learning-path',
    description: '把学习目标拆解成可执行步骤，持续同步进度并精准推送所需资源。',
    tags: ['动态规划', '节点跟踪', '资源推荐'],
    color: '#b55b13',
    soft: '#fff3e7',
  },
  {
    icon: Bot,
    title: '智能辅导',
    path: '/ai-tutor',
    description: '结合课程证据即时答疑，用 Markdown、知识图解和语音提供多形态讲解。',
    tags: ['实时问答', '知识图解', '语音讲解'],
    color: '#07845b',
    soft: '#e8f8f1',
  },
  {
    icon: ChartColumnIncreasing,
    title: '学习效果评估',
    path: '/evaluation',
    description: '结合练习结果、学习行为和资源反馈，评估掌握度并驱动下一轮调整。',
    tags: ['多维评估', '即时反馈', '策略更新'],
    color: '#b23f68',
    soft: '#fff0f5',
  },
]
</script>

<style scoped>
.capability-section { width: min(100% - 40px, 1180px); margin: 0 auto; padding: 84px 0 96px; }
.section-heading { display: grid; grid-template-columns: minmax(0, 1.15fr) minmax(300px, .75fr); align-items: end; gap: 80px; margin-bottom: 36px; }
.section-kicker { color: #5b52e8; font-size: 12px; font-weight: 800; letter-spacing: .12em; }
.section-heading h2 { max-width: 720px; margin: 10px 0 0; color: #182033; font-size: clamp(30px, 3.4vw, 45px); line-height: 1.18; letter-spacing: -.045em; }
.section-heading p { margin: 0; color: #667085; font-size: 14px; line-height: 1.85; }
.capability-grid { display: grid; grid-template-columns: repeat(6, minmax(0, 1fr)); gap: 16px; }
.capability-card { position: relative; display: flex; min-height: 300px; flex-direction: column; grid-column: span 2; padding: 26px; overflow: hidden; border: 1px solid #e2e7f0; border-radius: 20px; color: inherit; background: rgba(255,255,255,.94); box-shadow: 0 8px 28px rgba(31,42,68,.055); text-decoration: none; transition: transform .24s ease, border-color .24s ease, box-shadow .24s ease; }
.capability-card::after { position: absolute; right: -48px; bottom: -56px; width: 150px; height: 150px; border-radius: 50%; content: ''; background: radial-gradient(circle, rgba(99,91,255,.08), transparent 68%); }
.capability-card:hover { transform: translateY(-5px); border-color: #cfcaff; box-shadow: 0 20px 45px rgba(31,42,68,.1); }
.card-4 { grid-column: 2 / span 2; }
.card-5 { grid-column: 4 / span 2; }
.card-top { display: flex; align-items: center; justify-content: space-between; }
.icon-wrap { display: grid; width: 46px; height: 46px; place-items: center; border-radius: 14px; }
.step-label { color: #c1c7d2; font-size: 12px; font-weight: 800; letter-spacing: .08em; }
.capability-card h3 { margin: 28px 0 10px; color: #1d2638; font-size: 20px; }
.capability-card p { margin: 0; color: #667085; font-size: 13px; line-height: 1.75; }
.feature-tags { display: flex; flex-wrap: wrap; gap: 6px; margin-top: 20px; }
.feature-tags span { padding: 5px 8px; border: 1px solid #e7eaf0; border-radius: 8px; color: #667085; font-size: 9px; font-weight: 700; background: #fafbfc; }
.card-link { display: inline-flex; align-items: center; gap: 5px; margin-top: auto; padding-top: 22px; color: #4f46d8; font-size: 12px; }
.system-proof { display: grid; grid-template-columns: 1fr 1.15fr; align-items: center; gap: 64px; margin-top: 70px; padding: 42px 46px; overflow: hidden; border-radius: 24px; color: #fff; background: linear-gradient(125deg, #171b30, #262453 60%, #39328d); box-shadow: 0 28px 60px rgba(24,25,59,.18); }
.proof-copy > span { color: #aaa5ff; font-size: 9px; font-weight: 800; letter-spacing: .14em; }
.proof-copy h3 { margin: 11px 0 10px; font-size: 25px; line-height: 1.3; }
.proof-copy p { margin: 0; color: rgba(235,237,255,.66); font-size: 12px; line-height: 1.75; }
.proof-metrics { display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; }
.proof-metrics article { padding: 18px 10px; border: 1px solid rgba(255,255,255,.09); border-radius: 14px; text-align: center; background: rgba(255,255,255,.045); }
.proof-metrics strong, .proof-metrics span { display: block; }
.proof-metrics strong { font-size: 23px; }
.proof-metrics span { margin-top: 4px; color: rgba(236,238,255,.58); font-size: 9px; }
@media (max-width: 900px) {
  .section-heading { grid-template-columns: 1fr; gap: 18px; }
  .capability-card { grid-column: span 3; }
  .card-5 { grid-column: 2 / span 4; }
  .system-proof { grid-template-columns: 1fr; gap: 28px; }
}
@media (max-width: 600px) {
  .capability-section { width: min(100% - 28px, 1180px); padding: 58px 0 68px; }
  .capability-grid { grid-template-columns: 1fr; }
  .capability-card, .card-4, .card-5 { grid-column: auto; min-height: 270px; }
  .system-proof { margin-top: 42px; padding: 30px 22px; }
  .proof-metrics { grid-template-columns: repeat(2, 1fr); }
}
</style>
