<template>
  <div class="app-root">
    <AppHeader v-if="showAppHeader" />
    <RouterView />
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { RouterView, useRoute } from 'vue-router'
import AppHeader from './components/AppHeader.vue'

const route = useRoute()
const showAppHeader = computed(() => !['login', 'register'].includes(String(route.name || '')))
</script>

<style scoped>
.app-root { min-height: 100vh; }
</style>
