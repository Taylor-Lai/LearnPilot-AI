<template>
  <div class="page">
    <Header />
    <SpiralHero />
    <HomeDashboard />
    <Bottom />
  </div>
</template>

<script setup>
import Bottom from '../components/AppFooter.vue'
import Header from '../components/AppHeader.vue'
import HomeDashboard from '../components/HomeDashboard.vue'
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
