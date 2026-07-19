<template>
  <header class="app-header">
    <div class="header-inner">
      <RouterLink class="brand" to="/" aria-label="汇知灵创首页">
        <span class="brand-mark">汇</span>
        <span class="brand-copy">
          <strong>汇知灵创</strong>
          <small>个性化学习智能体</small>
        </span>
      </RouterLink>

      <nav class="main-nav" aria-label="主导航">
        <RouterLink v-for="item in navItems" :key="item.path" :to="item.path" class="nav-link">
          <component :is="item.icon" :size="16" :stroke-width="2" />
          <span>{{ item.label }}</span>
        </RouterLink>
      </nav>

      <div class="header-actions">
        <template v-if="isLoggedIn">
          <RouterLink class="user-chip" to="/profile" aria-label="进入个人中心">
            <span class="user-avatar">{{ avatarText }}</span>
            <span class="user-copy">
              <small>欢迎回来</small>
              <strong>{{ displayName }}</strong>
            </span>
          </RouterLink>
          <RouterLink v-if="isAdmin" class="admin-link" to="/admin">管理后台</RouterLink>
          <button class="logout-button" type="button" @click="handleLogout">退出</button>
        </template>
        <template v-else>
          <RouterLink class="text-action" to="/login">登录</RouterLink>
          <RouterLink class="primary-action" to="/register">免费开始</RouterLink>
        </template>
      </div>
    </div>
  </header>
</template>

<script setup>
import { computed, onMounted } from 'vue'
import { RouterLink, useRouter } from 'vue-router'
import { Bot, House, LibraryBig, Route } from 'lucide-vue-next'
import { getUserInfo } from '../api/auth'
import { userStore } from '../stores/userStore'
import { clearAuthSession } from '../utils/user'

const router = useRouter()
const navItems = [
  { label: '学习工作台', path: '/', icon: House },
  { label: '资源中心', path: '/resources', icon: LibraryBig },
  { label: '学习路径', path: '/learning-path', icon: Route },
  { label: 'AI 辅导', path: '/ai-tutor', icon: Bot },
]

const isLoggedIn = computed(() => userStore.state.isLoggedIn)
const displayName = computed(() => userStore.state.nickname || userStore.state.username || '学习者')
const avatarText = computed(() => displayName.value.trim().slice(0, 1).toUpperCase() || '学')
const isAdmin = computed(() => userStore.state.isAdmin)

function handleLogout() {
  clearAuthSession()
  router.push('/')
}

onMounted(() => {
  userStore.syncFromLocalStorage()
  if (localStorage.getItem('token')) getUserInfo().catch(() => {})
})
</script>

<style scoped>
.app-header {
  position: sticky;
  top: 0;
  z-index: 1000;
  width: 100%;
  border-bottom: 1px solid rgba(218, 224, 236, 0.82);
  background: rgba(255, 255, 255, 0.9);
  backdrop-filter: blur(18px) saturate(1.35);
}

.header-inner {
  display: grid;
  grid-template-columns: minmax(210px, 1fr) auto minmax(210px, 1fr);
  align-items: center;
  width: min(100% - 40px, 1240px);
  min-height: 68px;
  margin: 0 auto;
  gap: 22px;
}

.brand, .user-chip { text-decoration: none; }
.brand { display: inline-flex; align-items: center; gap: 11px; justify-self: start; }
.brand-mark {
  display: grid;
  width: 38px;
  height: 38px;
  place-items: center;
  border-radius: 12px;
  color: #fff;
  font-size: 17px;
  font-weight: 850;
  background: linear-gradient(145deg, #675cff, #4f46d8);
  box-shadow: 0 9px 22px rgba(82, 70, 220, 0.24);
}
.brand-copy strong, .brand-copy small { display: block; }
.brand-copy strong { color: #182033; font-size: 15px; letter-spacing: .01em; }
.brand-copy small { margin-top: 1px; color: #8a94a6; font-size: 10px; font-weight: 650; }

.main-nav { display: flex; align-items: center; gap: 4px; }
.nav-link {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  padding: 9px 13px;
  border-radius: 10px;
  color: #667085;
  font-size: 13px;
  font-weight: 680;
  text-decoration: none;
  transition: background .2s ease, color .2s ease;
}
.nav-link:hover { color: #342d88; background: #f3f1ff; }
.nav-link.router-link-exact-active { color: #4f46d8; background: #efedff; }

.header-actions { display: flex; align-items: center; justify-self: end; gap: 8px; min-width: 0; }
.user-chip { display: flex; align-items: center; gap: 8px; min-width: 0; padding: 4px 8px 4px 4px; border-radius: 12px; }
.user-chip:hover { background: #f6f7fa; }
.user-avatar { display: grid; width: 32px; height: 32px; place-items: center; flex: 0 0 auto; border-radius: 10px; color: #fff; font-weight: 800; background: linear-gradient(145deg, #2f80ed, #635bff); }
.user-copy { min-width: 0; }
.user-copy small, .user-copy strong { display: block; max-width: 105px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.user-copy small { color: #98a2b3; font-size: 9px; }
.user-copy strong { color: #344054; font-size: 12px; }

.text-action, .admin-link, .logout-button, .primary-action {
  min-height: 36px;
  padding: 0 13px;
  border-radius: 10px;
  font-size: 12px;
  font-weight: 720;
  text-decoration: none;
}
.text-action, .admin-link, .primary-action { display: inline-flex; align-items: center; }
.text-action { color: #475467; }
.admin-link { border: 1px solid #d9d6ff; color: #4f46d8; background: #f7f6ff; }
.logout-button { border: 1px solid #e4e7ec; color: #667085; background: #fff; cursor: pointer; }
.primary-action { color: #fff; background: #5b52e8; box-shadow: 0 7px 18px rgba(91, 82, 232, .2); }
.logout-button:hover, .text-action:hover { background: #f2f4f7; }
.primary-action:hover { background: #4c43d3; }

@media (max-width: 980px) {
  .header-inner { grid-template-columns: auto 1fr auto; width: min(100% - 24px, 1240px); gap: 10px; }
  .brand-copy { display: none; }
  .main-nav { justify-content: center; }
  .nav-link { padding: 9px 10px; }
  .nav-link span { display: none; }
  .user-copy { display: none; }
}

@media (max-width: 560px) {
  .header-inner { min-height: 60px; }
  .brand-mark { width: 34px; height: 34px; }
  .main-nav { gap: 0; }
  .nav-link { padding: 8px; }
  .admin-link, .logout-button, .text-action { display: none; }
  .primary-action { min-height: 34px; padding: 0 11px; }
}
</style>
