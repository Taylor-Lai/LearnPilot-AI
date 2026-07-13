<template>
  <div class="auth-page">
    <RouterLink class="ui-back-link auth-back-link" to="/">← 返回首页</RouterLink>

    <section class="auth-card" :class="{ 'is-register': isRegister }">
      <div class="forms-layer">
        <div class="form-side form-left">
          <form class="form-box" @submit.prevent="handleLogin">
            <h1>登录</h1>

            <div class="input-group">
              <input
                v-model.trim="loginForm.email"
                type="email"
                placeholder="请输入邮箱"
              />
              <input
                v-model="loginForm.password"
                type="password"
                placeholder="请输入密码"
              />
            </div>

            <p v-if="loginError" class="feedback error-text">{{ loginError }}</p>
            <p v-if="loginSuccess" class="feedback success-text">{{ loginSuccess }}</p>

            <button class="submit-button" type="submit" :disabled="loginLoading">
              {{ loginLoading ? '登录中...' : '登录' }}
            </button>
          </form>
        </div>

        <div class="form-side form-right">
          <form class="form-box" @submit.prevent="handleRegister">
            <h1>注册</h1>

            <div class="input-group">
              <input
                v-model.trim="registerForm.username"
                type="text"
                placeholder="请输入用户名"
              />
              <input
                v-model.trim="registerForm.email"
                type="email"
                placeholder="请输入邮箱"
              />
              <input
                v-model="registerForm.password"
                type="password"
                placeholder="请输入密码"
              />
            </div>

            <p v-if="registerError" class="feedback error-text">{{ registerError }}</p>
            <p v-if="registerSuccess" class="feedback success-text">
              {{ registerSuccess }}
            </p>

            <button class="submit-button" type="submit" :disabled="registerLoading">
              {{ registerLoading ? '注册中...' : '注册' }}
            </button>
          </form>
        </div>
      </div>

      <div class="slide-panel">
        <div class="slide-bg"></div>

        <div class="slide-content register-hint">
          <h2>还没有账号？</h2>
          <p>创建账号，开启专属知识协作体验。</p>
          <button class="switch-button" type="button" @click="switchToRegister">
            去注册
          </button>
        </div>

        <div class="slide-content login-hint">
          <h2>已有账号？</h2>
          <p>登录账号，继续进入你的个人空间。</p>
          <button class="switch-button" type="button" @click="switchToLogin">
            去登录
          </button>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup>
import { reactive, ref, watch, nextTick } from 'vue'
import { RouterLink, useRoute, useRouter } from 'vue-router'
import { login, register } from '../api/auth'

const route = useRoute()
const router = useRouter()

const isRegister = ref(route.path.includes('register'))

const loginForm = reactive({
  email: '',
  password: '',
})

const registerForm = reactive({
  username: '',
  email: '',
  password: '',
})

const loginLoading = ref(false)
const registerLoading = ref(false)

const loginError = ref('')
const registerError = ref('')
const loginSuccess = ref('')
const registerSuccess = ref('')

watch(
  () => route.path,
  (path) => {
    isRegister.value = path.includes('register')
    clearMessage()
  },
)

function validateEmail(email) {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)
}

function clearMessage() {
  loginError.value = ''
  registerError.value = ''
  loginSuccess.value = ''
  registerSuccess.value = ''
}

function resetLoginForm() {
  loginForm.email = ''
  loginForm.password = ''
}

function resetRegisterForm() {
  registerForm.username = ''
  registerForm.email = ''
  registerForm.password = ''
}

function switchToRegister() {
  clearMessage()
  isRegister.value = true
  router.push('/register')
}

function switchToLogin() {
  clearMessage()
  isRegister.value = false
  router.push('/login')
}

function validateLoginForm() {
  if (!loginForm.email) return '请输入邮箱'
  if (!validateEmail(loginForm.email)) return '邮箱格式不正确'
  if (!loginForm.password) return '请输入密码'
  if (loginForm.password.length < 6) return '密码错误'
  return ''
}

function validateRegisterForm() {
  if (!registerForm.username) return '请输入用户名'
  if (registerForm.username.length < 2) return '用户名至少需要2位'
  if (!registerForm.email) return '请输入邮箱'
  if (!validateEmail(registerForm.email)) return '邮箱格式不正确'
  if (!registerForm.password) return '请输入密码'
  if (registerForm.password.length < 6) return '密码至少需要6位'
  return ''
}

async function handleLogin() {
  loginError.value = ''
  loginSuccess.value = ''

  const error = validateLoginForm()
  if (error) {
    loginError.value = error
    return
  }

  loginLoading.value = true

  try {
    await login({
      email: loginForm.email,
      password: loginForm.password,
    })

    await nextTick()

    loginSuccess.value = '登录成功'
    resetLoginForm()

    const redirect = route.query.redirect
    router.push(typeof redirect === 'string' && redirect ? redirect : '/')
  } catch (err) {
    console.error('Login error:', err)
    loginError.value = err?.message || '登录失败，请检查邮箱或密码'
  } finally {
    loginLoading.value = false
  }
}

async function handleRegister() {
  registerError.value = ''
  registerSuccess.value = ''

  const error = validateRegisterForm()
  if (error) {
    registerError.value = error
    return
  }

  registerLoading.value = true

  try {
    await register({
      username: registerForm.username,
      email: registerForm.email,
      password: registerForm.password,
    })

    registerSuccess.value = '注册成功，请登录'
    resetRegisterForm()

    setTimeout(() => {
      switchToLogin()
    }, 800)
  } catch (err) {
    registerError.value = err?.message || '注册失败，请稍后重试'
  } finally {
    registerLoading.value = false
  }
}
</script>

<style scoped>
.auth-page {
  min-height: 100vh;
  padding: 32px 24px;
  background: var(--bg-page);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}

.auth-back-link {
  width: min(100%, 960px);
  margin-bottom: 18px;
}

.auth-card {
  position: relative;
  width: min(100%, 960px);
  height: 560px;
  overflow: hidden;
  border-radius: 18px;
  background: #ffffff;
  box-shadow: 0 24px 60px rgba(15, 23, 42, 0.18);
}

.forms-layer {
  position: absolute;
  inset: 0;
  z-index: 1;
}

.form-side {
  position: absolute;
  top: 0;
  width: 50%;
  height: 100%;
  background: #f5f5f5;
}

.form-left {
  left: 0;
}

.form-right {
  right: 0;
}

.form-box {
  width: 100%;
  height: 100%;
  padding: 70px 64px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}

.form-box h1 {
  margin: 0 0 36px;
  color: #333333;
  font-size: 40px;
  font-weight: 400;
}

.input-group {
  width: 100%;
  display: grid;
  gap: 18px;
}

.input-group input {
  width: 100%;
  height: 54px;
  padding: 0 18px;
  border: none;
  outline: none;
  background: #ffffff;
  color: #333333;
  font-size: 15px;
  border-radius: 10px;
}

.input-group input::placeholder {
  color: #9ca3af;
}

.input-group input:focus {
  box-shadow: 0 0 0 3px rgba(0, 114, 255, 0.12);
}

.feedback {
  width: 100%;
  margin: 16px 0 0;
  font-size: 14px;
  text-align: left;
}

.error-text {
  color: #d14343;
}

.success-text {
  color: #12805c;
}

.submit-button,
.switch-button {
  min-width: 210px;
  height: 50px;
  margin-top: 34px;
  border: none;
  border-radius: 999px;
  background: linear-gradient(135deg, #0072ff, #0094b8);
  color: #ffffff;
  font-size: 15px;
  font-weight: 700;
  letter-spacing: 0.16em;
  cursor: pointer;
  transition:
    transform 0.25s ease,
    box-shadow 0.25s ease;
}

.submit-button:hover,
.switch-button:hover {
  transform: translateY(-2px);
  box-shadow: 0 14px 30px rgba(0, 114, 255, 0.26);
}

.submit-button:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

.slide-panel {
  position: absolute;
  top: 0;
  right: 0;
  z-index: 20;
  width: 50%;
  height: 100%;
  overflow: hidden;
  background: #00305c;
  transition: transform 0.75s cubic-bezier(0.22, 1, 0.36, 1);
}

.auth-card.is-register .slide-panel {
  transform: translateX(-100%);
}

.slide-bg {
  position: absolute;
  inset: 0;
  background: linear-gradient(135deg, #00305c 0%, #005c78 100%);
}

.slide-content {
  position: absolute;
  inset: 0;
  z-index: 2;
  padding: 48px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  color: #ffffff;
  transition:
    opacity 0.45s ease,
    transform 0.55s ease;
}

.slide-content h2 {
  margin: 0 0 18px;
  font-size: 36px;
  font-weight: 400;
}

.slide-content p {
  max-width: 280px;
  margin: 0;
  color: rgba(255, 255, 255, 0.92);
  font-size: 15px;
  line-height: 1.8;
}

.register-hint {
  opacity: 1;
  transform: translateX(0);
  pointer-events: auto;
}

.login-hint {
  opacity: 0;
  transform: translateX(-40px);
  pointer-events: none;
}

.auth-card.is-register .register-hint {
  opacity: 0;
  transform: translateX(40px);
  pointer-events: none;
}

.auth-card.is-register .login-hint {
  opacity: 1;
  transform: translateX(0);
  pointer-events: auto;
}

@media (max-width: 860px) {
  .auth-card {
    height: auto;
    min-height: 620px;
  }

  .forms-layer {
    position: relative;
  }

  .form-side {
    position: relative;
    width: 100%;
    height: auto;
  }

  .form-box {
    min-height: 430px;
    padding: 42px 24px;
  }

  .form-right {
    display: none;
  }

  .auth-card.is-register .form-left {
    display: none;
  }

  .auth-card.is-register .form-right {
    display: block;
  }

  .slide-panel {
    position: relative;
    right: auto;
    width: 100%;
    height: 240px;
    transform: none !important;
  }

  .slide-content h2 {
    font-size: 28px;
  }
}
</style>
