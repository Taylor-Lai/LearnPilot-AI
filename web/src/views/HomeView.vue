<template>
  <div class="page">
    <AppHeader />
    <SpiralHero />
    <AppFooter />
  </div>
</template>

<script setup>
import AppFooter from '../components/AppFooter.vue'
import AppHeader from '../components/AppHeader.vue'
import SpiralHero from '../components/SpiralHero.vue'
</script>

<style scoped>
.page {
  min-height: 100vh;
  background: var(--bg-page);
  display: flex;
  flex-direction: column;
  overflow-x: hidden;
}
</style>
