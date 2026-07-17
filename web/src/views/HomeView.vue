<template>
  <div class="page">
    <AppHeader />
    <SpiralHero />
    <HomeFeatureGrid />
  </div>
</template>

<script setup>
import AppHeader from '../components/AppHeader.vue'
import HomeFeatureGrid from '../components/HomeFeatureGrid.vue'
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
