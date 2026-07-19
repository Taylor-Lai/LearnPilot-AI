<template>
  <main class="not-found-page">
    <section class="not-found-card">
      <div class="error-code">404</div>
      <span class="eyebrow">页面走丢了</span>
      <h1>这里暂时没有学习内容</h1>
      <p>地址可能已经变更。你可以返回首页，或前往资源中心继续学习。</p>
      <div class="actions">
        <RouterLink class="primary-action" to="/">返回首页</RouterLink>
        <RouterLink class="secondary-action" to="/resources">浏览资源</RouterLink>
      </div>
    </section>
  </main>
</template>

<script setup>
import { RouterLink } from 'vue-router'
</script>

<style scoped>
.not-found-page {
  display: grid;
  min-height: calc(100vh - 72px);
  padding: 72px 24px;
  place-items: center;
}

.not-found-card {
  width: min(620px, 100%);
  padding: 64px;
  text-align: center;
  background: rgba(255, 255, 255, 0.94);
  border: 1px solid #e5e7eb;
  border-radius: 28px;
  box-shadow: 0 28px 72px rgba(17, 24, 39, 0.1);
}

.error-code {
  margin-bottom: -18px;
  color: rgba(99, 91, 255, 0.1);
  font-size: clamp(92px, 16vw, 150px);
  font-weight: 800;
  line-height: 0.9;
  letter-spacing: -0.08em;
}

.eyebrow {
  color: #635bff;
  font-weight: 700;
}

h1 {
  margin: 12px 0;
  font-size: clamp(28px, 5vw, 42px);
  line-height: 1.18;
}

p {
  max-width: 460px;
  margin: 0 auto;
  color: #667085;
  font-size: 16px;
}

.actions {
  display: flex;
  gap: 12px;
  justify-content: center;
  margin-top: 30px;
}

.actions a {
  padding: 11px 20px;
  font-weight: 700;
  text-decoration: none;
  border-radius: 12px;
}

.primary-action {
  color: #fff;
  background: #111827;
}

.secondary-action {
  color: #344054;
  background: #f3f4f6;
}

@media (max-width: 560px) {
  .not-found-card {
    padding: 44px 24px;
  }
}
</style>
