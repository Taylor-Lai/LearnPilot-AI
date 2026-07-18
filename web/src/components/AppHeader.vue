<template>
  <header class="header">
    <div class="header-inner">
      <RouterLink class="brand" to="/">汇知灵创</RouterLink>

      <nav class="nav-menu">
        <span class="nav-item" @click="handleNavClick('/resources')">资源库</span>
        <span class="nav-item" @click="handleNavClick('/profile')">个人中心</span>
        <span class="nav-item" @click="handleNavClick('/guide')">使用指南</span>
        <span class="nav-item" @click="handleNavClick('/feedback')">问题反馈</span>
      </nav>

      <nav class="actions">
        <template v-if="isLoggedIn">
          <span class="user-greeting">你好，{{ displayName }}</span>

          <button class="logout-button" @click="handleLogout">
            退出登录
          </button>

          <button
            v-if="isAdmin"
            class="admin-button"
            @click="handleAdminClick"
          >
            管理员后台
          </button>
        </template>

        <template v-else>
          <RouterLink class="action-button" to="/login">
            登录 / 注册
          </RouterLink>
        </template>
      </nav>
    </div>
  </header>
</template>

<script setup>
import { RouterLink, useRouter } from 'vue-router'
import { computed, onMounted } from 'vue'
import { userStore } from '../stores/userStore'
import { getUserInfo } from '../api/auth'

const router = useRouter()

// 使用 computed 保持响应式
const isLoggedIn = computed(() => userStore.state.isLoggedIn)
const displayName = computed(() => userStore.state.nickname || userStore.state.username || '用户')
const isAdmin = computed(() => userStore.state.isAdmin)

function handleNavClick(path) {
  if (!isLoggedIn.value) {
    router.push('/login')
    return
  }
  router.push(path)
}

function handleAdminClick() {
  router.push('/admin')
}

function handleLogout() {
  const ok = window.confirm('确定要退出登录吗？')
  if (!ok) return

  localStorage.removeItem('token')
  localStorage.removeItem('userInfo')

  userStore.updateUserInfo(null)

  router.push('/')
}

onMounted(() => {
  if (localStorage.getItem('token')) {
    getUserInfo().catch(() => {})
  }
})
</script>

<style scoped>
.header {
  position: relative;
  z-index: 99999;
  width: 100%;
  background: #ffffff;
  overflow: visible;
}

.header-inner {
  position: relative;
  display: flex;
  align-items: center;
  width: 100%;
  min-height: 62px;
  padding: 0 28px;
  border: 1px solid #d6dbe6;
  border-radius: 18px 18px 0 0;
  background: #ffffff;
  overflow: visible;
}

.brand {
  color: #6a52ff;
  font-size: 17px;
  font-weight: 800;
  letter-spacing: 0.05em;
  text-decoration: none;
}

.nav-menu {
  position: absolute;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  align-items: center;
  gap: 46px;
  z-index: 100000;
}

.nav-item {
  color: #000;
  font-size: 16px;
  font-weight: 700;
  cursor: pointer;
  white-space: nowrap;
  transition: color 0.25s ease;
}

.nav-item:hover {
  color: #6a52ff;
}

.actions {
  margin-left: auto;
  display: flex;
  align-items: center;
  gap: 10px;
}

.action-button,
.logout-button,
.admin-button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 112px;
  min-height: 34px;
  padding: 0 14px;
  border: 1px solid #111827;
  border-radius: 8px;
  background: #111827;
  color: #ffffff;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.08em;
  cursor: pointer;
  transition: background-color 0.2s ease;
  text-decoration: none;
}

.admin-button {
  min-width: 104px;
  border-color: #4f46e5;
  background: #4f46e5;
}

.action-button:hover,
.logout-button:hover {
  background: #1f2937;
}

.admin-button:hover {
  background: #4338ca;
}

.user-greeting {
  color: #6a52ff;
  font-weight: 700;
  font-size: 14px;
}

@media (max-width: 1024px) {
  .nav-menu { gap: 24px; }
  .nav-item { font-size: 15px; }
}
@media (max-width: 768px) {
  .header-inner {
    display: grid;
    grid-template-columns: auto minmax(0, 1fr);
    gap: 10px 12px;
    min-height: auto;
    padding: 10px 14px 8px;
  }

  .brand {
    align-self: center;
    white-space: nowrap;
  }

  .actions {
    min-width: 0;
    margin-left: 0;
    justify-self: end;
    gap: 6px;
  }

  .user-greeting {
    display: none;
  }

  .action-button,
  .logout-button,
  .admin-button {
    min-width: auto;
    min-height: 32px;
    padding: 0 10px;
    font-size: 11px;
    letter-spacing: 0;
  }

  .nav-menu {
    position: static;
    grid-column: 1 / -1;
    transform: none;
    width: 100%;
    justify-content: space-between;
    gap: 12px;
    padding-top: 8px;
    border-top: 1px solid #eef0f5;
    overflow-x: auto;
    scrollbar-width: none;
  }

  .nav-menu::-webkit-scrollbar {
    display: none;
  }

  .nav-item { font-size: 13px; }
}
@media (max-width: 640px) {
  .header-inner { padding: 10px 12px 8px; }
  .nav-menu { gap: 10px; }
  .nav-item { font-size: 12px; }
}
</style>
