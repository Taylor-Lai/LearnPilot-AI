<template>
  <section class="feature-section">
    <div class="feature-wrapper">
      <div class="feature-grid">
        <RouterLink
          v-for="item in cards"
          :key="item.title"
          class="feature-card"
          :to="getTargetPath(item)"
          :style="{ background: item.background }"
          @click.prevent="handleCardClick(item)"
        >
          <div class="card-main">
            <div class="card-icon">
              <component
                :is="item.icon"
                :size="30"
                :stroke-width="2"
              />
            </div>

            <div class="card-content">
              <h3>{{ item.title }}</h3>
            </div>
          </div>

          <div class="card-hover">
            <div class="hover-content">
              <h4>{{ item.title }}</h4>

              <p>
                {{ item.description }}
              </p>

              <span class="experience-btn">
                立即体验 →
              </span>
            </div>
          </div>
        </RouterLink>
      </div>
    </div>
  </section>
</template>

<script setup>
import { RouterLink, useRouter } from 'vue-router'
import { ref, onMounted, onUnmounted } from 'vue'

import {
  UserRound,
  BookOpen,
  Route,
  GraduationCap,
  ChartColumn,
} from 'lucide-vue-next'

const router = useRouter()
const isLoggedIn = ref(false)

// 检查登录状态
function checkLoginStatus() {
  try {
    const token = localStorage.getItem('token')
    const userInfo = localStorage.getItem('userInfo')
    isLoggedIn.value = !!(token && userInfo)
  } catch {
    isLoggedIn.value = false
  }
}

// 监听登录状态变化
onMounted(() => {
  checkLoginStatus()
  window.addEventListener('storage', checkLoginStatus)
  window.addEventListener('userInfoUpdated', checkLoginStatus)
})

onUnmounted(() => {
  window.removeEventListener('storage', checkLoginStatus)
  window.removeEventListener('userInfoUpdated', checkLoginStatus)
})

// 获取目标路径
function getTargetPath(item) {
  if (isLoggedIn.value) {
    return item.path || '#'
  }
  return '/login'
}

// 处理卡片点击
function handleCardClick(item) {
  if (!isLoggedIn.value) {
    // 未登录，跳转到登录页
    router.push('/login')
  } else if (item.path && item.path !== '#') {
    // 已登录且有有效路径，跳转到对应页面
    router.push(item.path)
  }
}

const cards = [
  {
    icon: UserRound,
    title: '对话式学习画像自主构建',
    path: '/profile-builder',
    description: '通过学习行为与实时交互动态形成个性化学习画像。',
    background: '#EAF4FF',
  },
  {
    icon: BookOpen,
    title: '多元学习资源构建',
    path: '/multi-agent-resource',
    description: '整合多种学习资源，形成结构化知识内容与学习材料。',
    background: '#FDEEF4',
  },
  {
    icon: Route,
    title: '个性化学习路径规划',
    path: '/learning-path',
    description: '根据学习目标智能规划学习路线并精准推送资源。',
    background: '#FFF8E5',
  },
  {
    icon: GraduationCap,
    title: '智能辅导',
    path: '/ai-tutor',
    description: '提供实时答疑、知识讲解与学习过程辅助。',
    background: '#EDF9F0',
  },
  {
    icon: ChartColumn,
    title: '学习效果评估',
    path: '/evaluation',
    description: '结合学习行为数据动态评估学习效果与成长轨迹。',
    background: '#F3EEFF',
  },
]
</script>

<style scoped>
.feature-section {
  width: 100%;
  padding: 48px 24px 64px;
  background: #ffffff;
  box-sizing: border-box;
}

.feature-wrapper {
  position: relative;
  overflow: hidden;
  width: min(100%, 1200px);
  margin: 0 auto;
  padding: 32px;
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border: 1px solid #e5e7eb;
  box-shadow: var(--shadow-md);
}

.feature-wrapper::before {
  content: '';
  position: absolute;
  left: -50%;
  top: -50%;
  width: 200%;
  height: 200%;
  z-index: 0;
  pointer-events: none;
  background:
    radial-gradient(circle at 20% 30%, rgba(59,130,246,.18), transparent 25%),
    radial-gradient(circle at 80% 20%, rgba(168,85,247,.18), transparent 25%),
    radial-gradient(circle at 70% 80%, rgba(236,72,153,.15), transparent 25%),
    radial-gradient(circle at 30% 75%, rgba(34,197,94,.15), transparent 25%),
    radial-gradient(circle at 50% 50%, rgba(251,191,36,.12), transparent 30%);
  animation: sandFlow 22s linear infinite;
}

.feature-wrapper::after {
  content: '';
  position: absolute;
  inset: 0;
  z-index: 1;
  pointer-events: none;
  background: rgba(255,255,255,.45);
  backdrop-filter: blur(28px);
}

.feature-grid {
  position: relative;
  z-index: 2;
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: 20px;
  width: 100%;
}

.feature-card {
  position: relative;
  min-height: 220px;
  height: 100%;
  overflow: hidden;
  border-radius: 18px;
  text-decoration: none;
  border: 1px solid rgba(255,255,255,.75);
  transition: transform .35s ease, box-shadow .35s ease;
  cursor: pointer;
}

.feature-card:hover {
  transform: translateY(-8px);
  box-shadow:
    0 16px 30px rgba(0,0,0,.08),
    0 6px 12px rgba(0,0,0,.04);
}

.card-main {
  position: relative;
  z-index: 2;
  padding: 24px;
}

.card-icon {
  width: 68px;
  height: 68px;
  border-radius: 18px;
  background: rgba(255,255,255,.75);
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 20px;
  color: #2563eb;
  backdrop-filter: blur(10px);
  box-shadow:
    0 4px 12px rgba(0,0,0,.06),
    inset 0 1px 0 rgba(255,255,255,.6);
}

.card-content h3 {
  color: #1e293b;
  font-size: 18px;
  font-weight: 700;
  line-height: 1.6;
}

.card-hover {
  position: absolute;
  top: 0;
  right: 0;
  width: 100%;
  height: 100%;
  z-index: 10;
  background: rgba(255,255,255,.4);
  backdrop-filter: blur(18px);
  transform: translateX(100%);
  transition: transform .45s cubic-bezier(.4,0,.2,1);
}

.feature-card:hover .card-hover {
  transform: translateX(0);
}

.hover-content {
  height: 100%;
  padding: 24px;
  display: flex;
  flex-direction: column;
}

.hover-content h4 {
  color: #0f172a;
  font-size: 18px;
  font-weight: 700;
  margin-bottom: 14px;
}

.hover-content p {
  flex: 1;
  color: #334155;
  font-size: 14px;
  line-height: 1.8;
}

.experience-btn {
  align-self: flex-end;
  padding: 10px 16px;
  border-radius: 999px;
  background: rgba(255,255,255,.8);
  color: #2563eb;
  font-size: 13px;
  font-weight: 700;
  transition: all .3s ease;
}

.feature-card:hover .experience-btn {
  transform: translateX(4px);
}

@keyframes sandFlow {
  0% {
    transform: rotate(0deg) scale(1);
  }
  25% {
    transform: rotate(90deg) scale(1.08);
  }
  50% {
    transform: rotate(180deg) scale(1);
  }
  75% {
    transform: rotate(270deg) scale(1.08);
  }
  100% {
    transform: rotate(360deg) scale(1);
  }
}

/* ==============================
   响应式布局
=============================== */
@media (max-width: 1199px) {
  .feature-section {
    padding: 40px 24px 56px;
  }

  .feature-grid {
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 16px;
  }
}

@media (max-width: 767px) {
  .feature-section {
    padding: 32px 16px 48px;
  }

  .feature-wrapper {
    padding: 20px;
    border-radius: 18px;
  }

  .feature-grid {
    grid-template-columns: 1fr;
    gap: 14px;
  }

  .feature-card {
    min-height: 200px;
  }
}
</style>
