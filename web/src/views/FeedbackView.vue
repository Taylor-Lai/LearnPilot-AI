<template>
  <div class="feedback-page">
    <RouterLink class="ui-back-link page-back-link" to="/">
      ← 返回首页
    </RouterLink>

    <main class="feedback-content">
      <section class="feedback-card">
        <p class="eyebrow">Feedback</p>
        <h1>问题反馈</h1>
        <p class="description">
          如果你在使用过程中遇到问题，或者有功能优化建议，可以在这里提交反馈。
          请尽量描述清楚问题场景，并留下邮箱或手机号，方便我们后续联系你。
        </p>

        <form class="feedback-form" @submit.prevent="handleSubmit">
          <div class="form-group">
            <label for="content">反馈内容</label>
            <textarea
              id="content"
              v-model.trim="form.content"
              placeholder="请输入你遇到的问题或建议..."
            ></textarea>
          </div>

          <div class="form-group">
            <label for="contact">联系方式</label>
            <input
              id="contact"
              v-model.trim="form.contact"
              type="text"
              placeholder="请输入邮箱或手机号"
            />
          </div>

          <p v-if="errorMessage" class="feedback-text error-text">
            {{ errorMessage }}
          </p>

          <p v-if="successMessage" class="feedback-text success-text">
            {{ successMessage }}
          </p>

          <button class="submit-button" type="submit" :disabled="submitting">
            {{ submitting ? '提交中...' : '提交反馈' }}
          </button>
        </form>
      </section>
    </main>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { RouterLink } from 'vue-router'
import { submitFeedback } from '../api/feedback'

const form = reactive({
  content: '',
  contact: '',
})

const errorMessage = ref('')
const successMessage = ref('')
const submitting = ref(false)

function validateContact(value) {
  const emailReg = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
  const phoneReg = /^1[3-9]\d{9}$/

  return emailReg.test(value) || phoneReg.test(value)
}

async function handleSubmit() {
  errorMessage.value = ''
  successMessage.value = ''

  if (!form.content) {
    errorMessage.value = '请输入反馈内容'
    return
  }

  if (form.content.length < 5) {
    errorMessage.value = '反馈内容至少需要5个字'
    return
  }

  if (!form.contact) {
    errorMessage.value = '请输入联系方式'
    return
  }

  if (!validateContact(form.contact)) {
    errorMessage.value = '请输入正确的邮箱或手机号'
    return
  }

  submitting.value = true
  try {
    await submitFeedback({ content: form.content, contact: form.contact, type: '其他', allowContact: true })
    successMessage.value = '反馈提交成功，感谢你的建议！'
    form.content = ''
    form.contact = ''
  } catch (error) {
    errorMessage.value = `反馈提交失败：${error.message}`
  } finally {
    submitting.value = false
  }
}
</script>

<style scoped>
.feedback-page {
  position: relative;
  min-height: 100vh;
  padding: 32px;
  background: #f7f8fa;
  color: #111827;
  box-sizing: border-box;
}

.page-back-link {
  position: absolute;
  left: 32px;
  top: 28px;
}

.feedback-content {
  max-width: 960px;
  margin: 0 auto;
  padding-top: 52px;
}

.feedback-card {
  position: relative;
  overflow: hidden;
  background: #ffffff;
  border: 1px solid #e5e7eb;
  border-radius: 18px;
  padding: 42px;
  box-shadow: var(--shadow-md);
}

.eyebrow {
  margin: 0 0 10px;
  font-size: 13px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: #111827;
}

.feedback-card h1 {
  margin: 0 0 14px;
  font-size: 34px;
  line-height: 1.25;
  color: #111827;
}

.description {
  max-width: 760px;
  margin: 0 0 30px;
  line-height: 1.9;
  font-size: 15px;
  color: #111827;
}

.feedback-form {
  display: grid;
  gap: 22px;
}

.form-group {
  display: grid;
  gap: 10px;
}

.form-group label {
  font-size: 15px;
  font-weight: 700;
  color: #111827;
}

.form-group textarea,
.form-group input {
  width: 100%;
  border: 1px solid #e5e7eb;
  outline: none;
  background: #f9fafb;
  color: #111827;
  font-size: 15px;
  border-radius: 14px;
  box-sizing: border-box;
  transition:
    background-color 0.2s ease,
    box-shadow 0.2s ease,
    border-color 0.2s ease;
}

.form-group textarea {
  min-height: 260px;
  padding: 18px;
  line-height: 1.8;
  resize: vertical;
}

.form-group input {
  height: 54px;
  padding: 0 18px;
}

.form-group textarea:focus,
.form-group input:focus {
  background: #ffffff;
  border-color: #d6dbe6;
  box-shadow: 0 0 0 3px rgba(0, 114, 255, 0.12);
}

.feedback-text {
  margin: -4px 0 0;
  font-size: 14px;
  font-weight: 600;
}

.error-text {
  color: #d14343;
}

.success-text {
  color: #12805c;
}

.submit-button {
  justify-self: start;
  min-width: 180px;
  height: 46px;
  border: none;
  border-radius: 999px;
  background: #111827;
  color: #ffffff;
  font-size: 14px;
  font-weight: 700;
  cursor: pointer;
  transition:
    transform 0.2s ease,
    box-shadow 0.2s ease,
    background-color 0.2s ease;
}

.submit-button:hover {
  transform: translateY(-2px);
  background: #1f2937;
  box-shadow: 0 12px 24px rgba(0, 0, 0, 0.18);
}

@media (max-width: 900px) {
  .feedback-page {
    padding: 18px;
  }

  .page-back-link {
    left: 18px;
    top: 18px;
  }

  .feedback-content {
    padding-top: 48px;
  }

  .feedback-card {
    padding: 24px;
    border-radius: 18px;
  }

  .feedback-card h1 {
    font-size: 28px;
  }

  .form-group textarea {
    min-height: 220px;
  }

  .submit-button {
    width: 100%;
  }
}
</style>
