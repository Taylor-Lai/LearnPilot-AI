<template>
  <div class="admin-sidebar-shell">
    <aside v-if="!sidebarHidden" class="admin-sidebar">
      <div class="sidebar-top">
        <div class="sidebar-title">后台管理</div>
        <button type="button" class="sidebar-hide-btn" @click="hideSidebar">
          收起菜单
        </button>
      </div>

      <nav class="sidebar-menu">
        <button
          v-for="item in menuItems"
          :key="item.path"
          type="button"
          class="menu-item"
          :class="{ active: route.path === item.path }"
          @click="goPage(item.path)"
        >
          {{ item.label }}
        </button>
      </nav>
    </aside>

    <button
      v-else
      type="button"
      class="sidebar-expand-btn"
      @click="showSidebar"
    >
      展开后台菜单
    </button>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

const route = useRoute()
const router = useRouter()

const STORAGE_KEY = 'admin_sidebar_hidden'

const sidebarHidden = ref(
  localStorage.getItem(STORAGE_KEY) === 'true'
  || localStorage.getItem('admin_sidebar_collapsed') === 'true'
)

const menuItems = [
  { path: '/admin', label: '用户管理' },
  { path: '/admin/feedback', label: '问题反馈管理' },
  { path: '/admin/dashboard', label: '数据总览' },
  { path: '/admin/tasks', label: '任务监控' },
  { path: '/admin/settings', label: '系统设置' },
]

const hideSidebar = () => {
  sidebarHidden.value = true
  localStorage.setItem(STORAGE_KEY, 'true')
}

const showSidebar = () => {
  sidebarHidden.value = false
  localStorage.setItem(STORAGE_KEY, 'false')
}

const goPage = (path) => {
  if (route.path === path) return
  router.push(path)
}
</script>
