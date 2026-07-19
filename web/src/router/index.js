import { createRouter, createWebHistory } from 'vue-router'
import { getStoredUserInfo, isAdminUser } from '../utils/user'

import HomeView from '../views/HomeView.vue'

const AuthView = () => import('../views/AuthView.vue')
const ProfileBuilder = () => import('../views/ProfileBuilder.vue')
const MultiAgentResourceGenerator = () => import('../views/MultiAgentResourceGenerator.vue')
const PersonalizedLearningPath = () => import('../views/PersonalizedLearningPath.vue')
const ProfileView = () => import('../views/ProfileView.vue')
const GuideView = () => import('../views/GuideView.vue')
const ResourceLibraryView = () => import('../views/ResourceLibraryView.vue')
const FeedbackView = () => import('../views/FeedbackView.vue')
const AdminView = () => import('../views/AdminView.vue')
const AdminFeedback = () => import('../views/AdminFeedback.vue')
const AdminDashboard = () => import('../views/AdminDashboard.vue')
const AdminSettings = () => import('../views/AdminSettings.vue')
const AdminTasks = () => import('../views/AdminTasks.vue')
const AiTutor = () => import('../views/AiTutor.vue')
const EvaluationView = () => import('../views/EvaluationView.vue')
const NotFoundView = () => import('../views/NotFoundView.vue')

const routeTitles = {
  home: '首页',
  resources: '资源中心',
  profileBuilder: '学习画像',
  multiAgentResource: '智能资源生成',
  learningPath: '学习路径',
  evaluation: '学习评估',
  aiTutor: '智能导师',
  profile: '个人中心',
  guide: '使用指南',
  feedback: '问题反馈',
  admin: '管理后台',
  adminFeedback: '反馈管理',
  adminDashboard: '数据总览',
  adminTasks: '任务监控',
  adminSettings: '系统设置',
  login: '登录',
  register: '注册',
  notFound: '页面未找到',
}

const router = createRouter({
  history: createWebHistory(),

  routes: [
    {
      path: '/',
      name: 'home',
      component: HomeView,
    },
    {
      path: '/resources',
      name: 'resources',
      component: ResourceLibraryView,
    },
    {
      path: '/profile-builder',
      name: 'profileBuilder',
      component: ProfileBuilder,
    },
    {
      path: '/multi-agent-resource',
      name: 'multiAgentResource',
      component: MultiAgentResourceGenerator,
      meta: { requiresAuth: true },
    },
    {
      path: '/learning-path',
      name: 'learningPath',
      component: PersonalizedLearningPath,
      meta: { requiresAuth: true },
    },
    {
      path: '/evaluation',
      name: 'evaluation',
      component: EvaluationView,
      meta: { requiresAuth: true },
    },
    {
      path: '/ai-tutor',
      name: 'aiTutor',
      component: AiTutor,
      meta: { requiresAuth: true },
    },
    {
      path: '/profile',
      name: 'profile',
      component: ProfileView,
      meta: { requiresAuth: true },
    },
    {
      path: '/guide',
      name: 'guide',
      component: GuideView,
    },
    {
      path: '/feedback',
      name: 'feedback',
      component: FeedbackView,
    },
    {
      path: '/admin',
      name: 'admin',
      component: AdminView,
      meta: { requiresAdmin: true },
    },
    {
      path: '/admin/feedback',
      name: 'adminFeedback',
      component: AdminFeedback,
      meta: { requiresAdmin: true },
    },
    {
      path: '/admin/dashboard',
      name: 'adminDashboard',
      component: AdminDashboard,
      meta: { requiresAdmin: true },
    },
    {
      path: '/admin/tasks',
      name: 'adminTasks',
      component: AdminTasks,
      meta: { requiresAdmin: true },
    },
    {
      path: '/admin/settings',
      name: 'adminSettings',
      component: AdminSettings,
      meta: { requiresAdmin: true },
    },
    {
      path: '/login',
      name: 'login',
      component: AuthView,
      props: {
        mode: 'login',
      },
    },
    {
      path: '/register',
      name: 'register',
      component: AuthView,
      props: {
        mode: 'register',
      },
    },
    {
      path: '/:pathMatch(.*)*',
      name: 'notFound',
      component: NotFoundView,
    },
  ],
})

router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('token')
  const userInfo = getStoredUserInfo()
  const isAdmin = isAdminUser(userInfo)

  if (to.meta.requiresAuth && !token) {
    next({ name: 'login', query: { redirect: to.fullPath } })
    return
  }

  if (to.meta.requiresAdmin) {
    if (!token) {
      next({ name: 'login', query: { redirect: to.fullPath } })
      return
    }
    if (!isAdmin) {
      next({ name: 'home' })
      return
    }
  }

  next()
})

router.afterEach((to) => {
  const title = routeTitles[to.name] || '个性化学习平台'
  document.title = `${title} · 汇知灵创`
})

export default router
