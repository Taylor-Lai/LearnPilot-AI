<template>
  <div class="page">
    <SpiralHero />
    <HomeFeatureGrid />
  </div>
</template>

<script setup>
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
