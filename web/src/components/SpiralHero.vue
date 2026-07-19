<template>
  <section class="hero">
    <div class="hero-glow hero-glow-one"></div>
    <div class="hero-glow hero-glow-two"></div>
    <div class="hero-inner">
      <div class="hero-copy">
        <div class="eyebrow"><Sparkles :size="14" /> 高校个性化学习智能体</div>
        <h1>让每位学生，都有一套真正适合自己的学习系统</h1>
        <p class="description">
          从对话式画像、多智能体资源生成，到动态学习路径与效果评估，
          汇知灵创把“因材施教”变成可持续迭代的学习体验。
        </p>
        <div class="hero-actions">
          <RouterLink class="primary-action" :to="primaryPath">
            {{ isLoggedIn ? '完善我的学习画像' : '免费开始学习' }}
            <ArrowRight :size="17" />
          </RouterLink>
          <RouterLink class="secondary-action" to="/multi-agent-resource">
            <PlayCircle :size="17" /> 体验资源生成
          </RouterLink>
        </div>
        <div class="trust-row" aria-label="产品能力">
          <span><ShieldCheck :size="15" /> 引用约束与内容安全</span>
          <span><Workflow :size="15" /> 多智能体协同</span>
          <span><Activity :size="15" /> 全程进度可追踪</span>
        </div>
      </div>

      <div class="product-preview" aria-label="智能学习工作台预览">
        <div class="preview-toolbar">
          <div>
            <span class="preview-logo">汇</span>
            <strong>学习任务中心</strong>
          </div>
          <span class="online-badge"><i></i> 5 个智能体在线</span>
        </div>

        <div class="preview-body">
          <aside class="preview-side">
            <span class="side-item active"><UserRound :size="16" /> 学习画像</span>
            <span class="side-item"><LibraryBig :size="16" /> 资源生成</span>
            <span class="side-item"><Route :size="16" /> 学习路径</span>
            <span class="side-item"><ChartNoAxesCombined :size="16" /> 效果评估</span>
          </aside>

          <div class="preview-main">
            <div class="preview-heading">
              <div>
                <small>今日学习建议</small>
                <h2>机器学习 · 模型评估</h2>
              </div>
              <span class="score-ring">82<small>%</small></span>
            </div>

            <div class="insight-card">
              <span class="insight-icon"><BrainCircuit :size="18" /></span>
              <div>
                <strong>已识别 2 个关键薄弱点</strong>
                <p>建议优先复习交叉验证与过拟合，再完成代码实践。</p>
              </div>
            </div>

            <div class="agent-flow">
              <div v-for="(agent, index) in agents" :key="agent.name" class="agent-step">
                <span>{{ index + 1 }}</span>
                <div><strong>{{ agent.name }}</strong><small>{{ agent.status }}</small></div>
                <Check :size="15" />
              </div>
            </div>

            <div class="progress-block">
              <div><span>本周学习进度</span><strong>68%</strong></div>
              <div class="progress-track"><i></i></div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup>
import { computed } from 'vue'
import { RouterLink } from 'vue-router'
import {
  Activity,
  ArrowRight,
  BrainCircuit,
  ChartNoAxesCombined,
  Check,
  LibraryBig,
  PlayCircle,
  Route,
  ShieldCheck,
  Sparkles,
  UserRound,
  Workflow,
} from 'lucide-vue-next'
import { userStore } from '../stores/userStore'

const isLoggedIn = computed(() => userStore.state.isLoggedIn)
const primaryPath = computed(() => (isLoggedIn.value ? '/profile-builder' : '/register'))
const agents = [
  { name: '画像分析 Agent', status: '学习特征已更新' },
  { name: '路径规划 Agent', status: '学习顺序已优化' },
  { name: '资源生成 Agent', status: '7 类内容已就绪' },
]
</script>

<style scoped>
.hero {
  position: relative;
  overflow: hidden;
  padding: 86px 24px 72px;
  color: #fff;
  background:
    linear-gradient(120deg, rgba(17, 20, 42, .98), rgba(32, 30, 78, .96) 55%, rgba(62, 50, 160, .94)),
    #171a36;
}
.hero::before {
  position: absolute;
  inset: 0;
  content: '';
  opacity: .14;
  background-image: linear-gradient(rgba(255,255,255,.14) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,.14) 1px, transparent 1px);
  background-size: 54px 54px;
  mask-image: linear-gradient(to bottom, black, transparent 88%);
}
.hero-glow { position: absolute; border-radius: 50%; filter: blur(20px); pointer-events: none; }
.hero-glow-one { width: 460px; height: 460px; right: 3%; top: -210px; background: rgba(110, 99, 255, .28); }
.hero-glow-two { width: 320px; height: 320px; left: 8%; bottom: -260px; background: rgba(47, 128, 237, .23); }
.hero-inner { position: relative; z-index: 1; display: grid; grid-template-columns: minmax(0, .92fr) minmax(520px, 1.08fr); align-items: center; gap: 72px; width: min(100%, 1180px); margin: 0 auto; }
.eyebrow { display: inline-flex; align-items: center; gap: 7px; margin-bottom: 20px; color: #c8c4ff; font-size: 13px; font-weight: 750; letter-spacing: .06em; }
h1 { max-width: 650px; margin: 0; font-size: clamp(42px, 4.6vw, 66px); line-height: 1.08; letter-spacing: -.05em; }
.description { max-width: 620px; margin: 24px 0 0; color: rgba(235, 238, 255, .72); font-size: 17px; line-height: 1.85; }
.hero-actions { display: flex; flex-wrap: wrap; gap: 12px; margin-top: 34px; }
.primary-action, .secondary-action { display: inline-flex; align-items: center; justify-content: center; gap: 8px; min-height: 50px; padding: 0 22px; border-radius: 13px; font-size: 14px; font-weight: 750; text-decoration: none; transition: transform .2s ease, background .2s ease; }
.primary-action { color: #29235e; background: #fff; box-shadow: 0 16px 36px rgba(9, 11, 27, .24); }
.secondary-action { border: 1px solid rgba(255,255,255,.18); color: #fff; background: rgba(255,255,255,.07); }
.primary-action:hover, .secondary-action:hover { transform: translateY(-2px); }
.secondary-action:hover { background: rgba(255,255,255,.12); }
.trust-row { display: flex; flex-wrap: wrap; gap: 18px; margin-top: 28px; color: rgba(229, 232, 255, .62); font-size: 11px; font-weight: 650; }
.trust-row span { display: inline-flex; align-items: center; gap: 6px; }

.product-preview { overflow: hidden; border: 1px solid rgba(255,255,255,.14); border-radius: 22px; color: #24304a; background: rgba(255,255,255,.97); box-shadow: 0 34px 90px rgba(5, 7, 24, .34); transform: perspective(1200px) rotateY(-2deg) rotateX(1deg); }
.preview-toolbar { display: flex; align-items: center; justify-content: space-between; min-height: 58px; padding: 0 18px; border-bottom: 1px solid #e8eaf1; }
.preview-toolbar > div { display: flex; align-items: center; gap: 9px; }
.preview-logo { display: grid; width: 28px; height: 28px; place-items: center; border-radius: 9px; color: #fff; font-size: 12px; font-weight: 800; background: #635bff; }
.preview-toolbar strong { font-size: 13px; }
.online-badge { display: inline-flex; align-items: center; gap: 6px; padding: 5px 9px; border-radius: 999px; color: #087a54; font-size: 10px; font-weight: 700; background: #eafaf4; }
.online-badge i { width: 6px; height: 6px; border-radius: 50%; background: #12a36d; box-shadow: 0 0 0 3px rgba(18,163,109,.12); }
.preview-body { display: grid; grid-template-columns: 138px 1fr; min-height: 410px; }
.preview-side { padding: 15px 10px; border-right: 1px solid #eceef4; background: #fafbfe; }
.side-item { display: flex; align-items: center; gap: 8px; margin-bottom: 6px; padding: 10px 9px; border-radius: 9px; color: #768096; font-size: 10px; font-weight: 680; }
.side-item.active { color: #5148d9; background: #eeecff; }
.preview-main { padding: 22px; }
.preview-heading { display: flex; align-items: center; justify-content: space-between; gap: 18px; }
.preview-heading small { color: #98a2b3; font-size: 9px; font-weight: 700; }
.preview-heading h2 { margin: 4px 0 0; color: #182033; font-size: 19px; letter-spacing: -.02em; }
.score-ring { display: grid; width: 58px; height: 58px; place-items: center; border: 6px solid #e8e5ff; border-top-color: #635bff; border-right-color: #635bff; border-radius: 50%; color: #4f46d8; font-size: 16px; font-weight: 850; transform: rotate(12deg); }
.score-ring small { color: inherit; font-size: 8px; }
.insight-card { display: flex; gap: 11px; margin-top: 18px; padding: 13px; border: 1px solid #e1dfff; border-radius: 13px; background: linear-gradient(135deg, #f8f7ff, #f1f5ff); }
.insight-icon { display: grid; width: 34px; height: 34px; place-items: center; flex: 0 0 auto; border-radius: 10px; color: #5b52e8; background: #fff; box-shadow: 0 5px 14px rgba(91,82,232,.12); }
.insight-card strong { display: block; font-size: 11px; }
.insight-card p { margin: 4px 0 0; color: #667085; font-size: 9px; line-height: 1.55; }
.agent-flow { display: grid; gap: 8px; margin-top: 16px; }
.agent-step { display: grid; grid-template-columns: 26px 1fr auto; align-items: center; gap: 9px; padding: 9px 11px; border: 1px solid #edf0f5; border-radius: 11px; }
.agent-step > span { display: grid; width: 24px; height: 24px; place-items: center; border-radius: 8px; color: #635bff; font-size: 9px; font-weight: 800; background: #efedff; }
.agent-step strong, .agent-step small { display: block; }
.agent-step strong { font-size: 10px; }
.agent-step small { margin-top: 1px; color: #98a2b3; font-size: 8px; }
.agent-step > svg { color: #12a36d; }
.progress-block { margin-top: 17px; }
.progress-block > div:first-child { display: flex; justify-content: space-between; color: #667085; font-size: 9px; }
.progress-block strong { color: #344054; }
.progress-track { overflow: hidden; height: 7px; margin-top: 7px; border-radius: 999px; background: #eceef4; }
.progress-track i { display: block; width: 68%; height: 100%; border-radius: inherit; background: linear-gradient(90deg, #635bff, #2f80ed); }

@media (max-width: 980px) {
  .hero { padding-top: 64px; }
  .hero-inner { grid-template-columns: 1fr; gap: 46px; }
  .hero-copy { text-align: center; }
  h1, .description { margin-left: auto; margin-right: auto; }
  .hero-actions, .trust-row { justify-content: center; }
  .product-preview { width: min(100%, 620px); margin: 0 auto; transform: none; }
}
@media (max-width: 560px) {
  .hero { padding: 54px 16px 48px; }
  h1 { font-size: 38px; }
  .description { font-size: 15px; }
  .hero-actions { display: grid; }
  .primary-action, .secondary-action { width: 100%; }
  .trust-row { display: grid; justify-content: start; text-align: left; }
  .preview-body { grid-template-columns: 1fr; }
  .preview-side { display: none; }
  .product-preview { border-radius: 17px; }
}
</style>
