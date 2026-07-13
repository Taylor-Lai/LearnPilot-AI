<template>
  <div class="admin-page">
    <Header />

    <div class="admin-layout admin-container">
      <AdminSidebar />

      <!-- 右侧内容区域 -->
      <main class="main-content">
        <!-- 返回首页按钮和标题区域 -->
        <section class="page-head card">
          <div class="page-head-left">
            <button class="ui-back-link" @click="goHome">
              ← 返回首页
            </button>
            <div>
              <div class="section-title">系统设置</div>
              <div class="section-subtitle">
                基于大模型的个性化资源生成与学习多智能体系统，通过智能交互实现知识共创与个性化学习
              </div>
            </div>
          </div>
        </section>

        <!-- 基础信息设置 -->
        <section class="card">
          <div class="card-title">平台基础信息</div>

          <div class="form-grid">
            <div class="form-item">
              <label class="form-label">平台名称</label>
              <input
                v-model.trim="form.siteName"
                type="text"
                class="form-input"
                placeholder="请输入平台名称"
              />
            </div>

            <div class="form-item">
              <label class="form-label">平台副标题</label>
              <input
                v-model.trim="form.siteSubtitle"
                type="text"
                class="form-input"
                placeholder="请输入平台副标题"
              />
            </div>

            <div class="form-item">
              <label class="form-label">联系邮箱</label>
              <input
                v-model.trim="form.contactEmail"
                type="text"
                class="form-input"
                placeholder="请输入联系邮箱"
              />
            </div>

            <div class="form-item">
              <label class="form-label">联系电话</label>
              <input
                v-model.trim="form.contactPhone"
                type="text"
                class="form-input"
                placeholder="请输入联系电话"
              />
            </div>

            <div class="form-item full">
              <label class="form-label">大模型服务商</label>
              <input
                v-model.trim="form.llmProvider"
                type="text"
                class="form-input"
                placeholder="例如：OpenAI、DeepSeek、通义千问"
              />
            </div>
          </div>
        </section>

        <!-- 智能体与资源生成设置 -->
        <section class="card">
          <div class="card-title">智能体与资源生成设置</div>

          <div class="form-grid">
            <div class="form-item">
              <label class="form-label">默认分页大小</label>
              <input
                v-model.number="form.pageSize"
                type="number"
                class="form-input"
                placeholder="请输入默认分页大小"
              />
            </div>

            <div class="form-item">
              <label class="form-label">单次最大资源生成数</label>
              <input
                v-model.number="form.maxGenerateCount"
                type="number"
                class="form-input"
                placeholder="请输入单次最大生成数量"
              />
            </div>

            <div class="form-item">
              <label class="form-label">大模型温度参数</label>
              <input
                v-model.number="form.temperature"
                type="number"
                step="0.1"
                min="0"
                max="2"
                class="form-input"
                placeholder="0-2之间，控制生成多样性"
              />
            </div>

            <div class="form-item">
              <label class="form-label">最大输出Token数</label>
              <input
                v-model.number="form.maxTokens"
                type="number"
                class="form-input"
                placeholder="单次请求最大输出Token数"
              />
            </div>

            <div class="form-item full">
              <label class="form-label">默认系统提示词</label>
              <textarea
                v-model.trim="form.systemPrompt"
                class="form-textarea"
                placeholder="请输入多智能体协作时的默认系统提示词"
                rows="3"
              ></textarea>
            </div>
          </div>

          <div class="switch-grid">
            <div class="switch-item">
              <div class="switch-info">
                <div class="switch-title">多智能体协作模式</div>
                <div class="switch-desc">启用后，多个智能体协同完成资源生成与路径规划</div>
              </div>
              <label class="switch">
                <input v-model="form.multiAgentEnabled" type="checkbox" />
                <span class="slider"></span>
              </label>
            </div>

            <div class="switch-item">
              <div class="switch-info">
                <div class="switch-title">个性化学习路径规划</div>
                <div class="switch-desc">根据用户画像智能规划个性化学习路线</div>
              </div>
              <label class="switch">
                <input v-model="form.learningPathEnabled" type="checkbox" />
                <span class="slider"></span>
              </label>
            </div>

            <div class="switch-item">
              <div class="switch-info">
                <div class="switch-title">用户画像自动构建</div>
                <div class="switch-desc">通过学习行为自动构建用户学习画像</div>
              </div>
              <label class="switch">
                <input v-model="form.profileBuilderEnabled" type="checkbox" />
                <span class="slider"></span>
              </label>
            </div>

            <div class="switch-item">
              <div class="switch-info">
                <div class="switch-title">资源智能推荐</div>
                <div class="switch-desc">基于用户画像和兴趣点智能推荐学习资源</div>
              </div>
              <label class="switch">
                <input v-model="form.resourceRecommendEnabled" type="checkbox" />
                <span class="slider"></span>
              </label>
            </div>
          </div>
        </section>

        <!-- 首页展示设置 -->
        <section class="card">
          <div class="card-title">首页展示设置</div>

          <div class="form-grid">
            <div class="form-item full">
              <label class="form-label">首页公告</label>
              <textarea
                v-model.trim="form.notice"
                class="form-textarea"
                placeholder="请输入首页公告内容"
                rows="3"
              ></textarea>
            </div>

            <div class="form-item full">
              <label class="form-label">平台简介</label>
              <textarea
                v-model.trim="form.introduction"
                class="form-textarea"
                placeholder="请输入平台简介"
                rows="4"
              ></textarea>
            </div>

            <div class="form-item full">
              <label class="form-label">系统特色说明</label>
              <textarea
                v-model.trim="form.features"
                class="form-textarea"
                placeholder="请介绍系统的核心功能和特色"
                rows="3"
              ></textarea>
            </div>
          </div>
        </section>

        <!-- 系统访问控制 -->
        <section class="card">
          <div class="card-title">系统访问控制</div>

          <div class="switch-grid">
            <div class="switch-item">
              <div class="switch-info">
                <div class="switch-title">允许新用户注册</div>
                <div class="switch-desc">关闭后，平台将停止普通用户自主注册</div>
              </div>
              <label class="switch">
                <input v-model="form.allowRegister" type="checkbox" />
                <span class="slider"></span>
              </label>
            </div>

            <div class="switch-item">
              <div class="switch-info">
                <div class="switch-title">反馈自动提醒</div>
                <div class="switch-desc">收到新的用户反馈后，自动提醒管理员处理</div>
              </div>
              <label class="switch">
                <input v-model="form.feedbackNotice" type="checkbox" />
                <span class="slider"></span>
              </label>
            </div>

            <div class="switch-item">
              <div class="switch-info">
                <div class="switch-title">智能辅导功能</div>
                <div class="switch-desc">启用后，用户可获得实时答疑与学习辅助</div>
              </div>
              <label class="switch">
                <input v-model="form.aiTutorEnabled" type="checkbox" />
                <span class="slider"></span>
              </label>
            </div>
          </div>
        </section>

        <!-- Logo 设置 -->
        <section class="card">
          <div class="card-title">品牌形象设置</div>

          <div class="form-grid">
            <div class="form-item">
              <label class="form-label">平台 Logo 地址</label>
              <input
                v-model.trim="form.logoUrl"
                type="text"
                class="form-input"
                placeholder="请输入 Logo 图片地址"
              />
            </div>

            <div class="form-item">
              <label class="form-label">网站图标地址</label>
              <input
                v-model.trim="form.faviconUrl"
                type="text"
                class="form-input"
                placeholder="请输入 favicon 图片地址"
              />
            </div>
          </div>

          <div class="preview-grid">
            <div class="preview-card">
              <div class="preview-label">Logo 预览</div>
              <div class="preview-box">
                <img
                  v-if="form.logoUrl"
                  :src="form.logoUrl"
                  alt="logo"
                  class="preview-image"
                />
                <span v-else>暂无图片</span>
              </div>
            </div>

            <div class="preview-card">
              <div class="preview-label">图标预览</div>
              <div class="preview-box small">
                <img
                  v-if="form.faviconUrl"
                  :src="form.faviconUrl"
                  alt="favicon"
                  class="preview-image small"
                />
                <span v-else>暂无图片</span>
              </div>
            </div>
          </div>
        </section>

        <!-- 操作区域 -->
        <section class="action-bar card">
          <button
            class="primary-btn"
            :disabled="saving"
            @click="handleSave"
          >
            {{ saving ? '保存中...' : '保存设置' }}
          </button>
          <button class="secondary-btn" @click="handleReset">重置内容</button>
        </section>
      </main>
    </div>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { getAdminSettings, updateAdminSettings } from '../api/admin'
import Header from '../components/AppHeader.vue'
import AdminSidebar from '../components/admin/AdminSidebar.vue'
import '../styles/admin-layout.css'

const router = useRouter()

const goHome = () => {
  router.push('/')
}

const saving = ref(false)

const createDefaultForm = () => ({
  // 平台基础信息
  siteName: '汇知灵创',
  siteSubtitle: '基于大模型的个性化资源生成与学习多智能体系统',
  contactEmail: 'support@huizhilingchuang.com',
  contactPhone: '400-800-1234',
  llmProvider: 'DeepSeek / 通义千问',

  // 智能体与资源生成设置
  pageSize: 12,
  maxGenerateCount: 10,
  temperature: 0.7,
  maxTokens: 4096,
  systemPrompt: '你是一个专业的学习辅助智能体，请根据用户的学习需求和兴趣点，生成高质量、结构化的学习资源。',

  // 功能开关
  multiAgentEnabled: true,
  learningPathEnabled: true,
  profileBuilderEnabled: true,
  resourceRecommendEnabled: true,
  allowRegister: true,
  feedbackNotice: true,
  aiTutorEnabled: true,

  // 首页展示
  notice: '欢迎使用汇知灵创！基于大模型的多智能体系统将为你提供个性化学习资源生成与路径规划服务。',
  introduction: '汇知灵创是一个基于大模型的个性化资源生成与学习多智能体系统。通过智能交互、多智能体协作与个性化学习路径规划，帮助用户高效获取知识、构建学习画像并实现持续成长。',
  features: '1. 对话式学习画像构建\n2. 多智能体资源生成\n3. 个性化学习路径规划\n4. 智能辅导与学习评估',

  // 品牌形象
  logoUrl: '',
  faviconUrl: ''
})

const form = reactive(createDefaultForm())

const loadSettings = async () => {
  try {
    const saved = await getAdminSettings()
    Object.assign(form, createDefaultForm(), saved || {})
  } catch (error) {
    console.error('读取系统设置失败：', error)
    alert(`读取系统设置失败：${error.message}`)
  }
}

const validateForm = () => {
  if (!form.siteName) {
    alert('请输入平台名称')
    return false
  }

  if (!form.contactEmail) {
    alert('请输入联系邮箱')
    return false
  }

  if (!form.pageSize || form.pageSize <= 0) {
    alert('默认分页大小必须大于0')
    return false
  }

  if (!form.maxGenerateCount || form.maxGenerateCount <= 0) {
    alert('单次最大资源生成数必须大于0')
    return false
  }

  if (form.temperature < 0 || form.temperature > 2) {
    alert('温度参数必须在0-2之间')
    return false
  }

  return true
}

const handleSave = async () => {
  if (saving.value) return
  if (!validateForm()) return

  saving.value = true

  try {
    await updateAdminSettings({ ...form })
    alert('系统设置保存成功')
  } catch (error) {
    console.error('保存系统设置失败：', error)
    alert('保存失败，请稍后重试')
  } finally {
    saving.value = false
  }
}

const handleReset = () => {
  const confirmed = window.confirm('确定要重置当前填写内容吗？')
  if (!confirmed) return

  Object.assign(form, createDefaultForm())
}

onMounted(() => {
  loadSettings()
})
</script>

<style scoped>
.card {
  position: relative;
  overflow: hidden;
  background: #ffffff;
  border: 1px solid #e5e7eb;
  border-radius: 18px;
  padding: 34px;
  box-shadow: var(--shadow-md);
}

.page-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  flex-wrap: wrap;
}

.page-head-left {
  flex: 1;
}

.section-title {
  font-size: 25px;
  line-height: 1.35;
  font-weight: 800;
  color: #111827;
}

.section-subtitle {
  margin-top: 10px;
  max-width: 760px;
  line-height: 1.8;
  font-size: 15px;
  color: #111827;
}

.card-title {
  font-size: 18px;
  font-weight: 800;
  color: #111827;
  margin-bottom: 22px;
}

/* 表单 */
.form-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 20px;
}

.form-item {
  display: flex;
  flex-direction: column;
  gap: 10px;
  min-width: 0;
}

.form-item.full {
  grid-column: 1 / -1;
}

.form-label {
  font-size: 14px;
  font-weight: 700;
  color: #111827;
}

.form-input,
.form-textarea {
  width: 100%;
  border: 1px solid #e5e7eb;
  border-radius: 16px;
  background: #ffffff;
  font-size: 15px;
  color: #111827;
  outline: none;
  transition: all 0.2s ease;
  box-sizing: border-box;
  font-family: inherit;
}

.form-input {
  height: 54px;
  padding: 0 16px;
}

.form-textarea {
  min-height: 100px;
  padding: 16px;
  resize: vertical;
  line-height: 1.8;
}

.form-input::placeholder,
.form-textarea::placeholder {
  color: #9ca3af;
}

.form-input:focus,
.form-textarea:focus {
  border-color: #111827;
  box-shadow: 0 0 0 3px rgba(0, 0, 0, 0.08);
}

/* 开关区域 */
.switch-grid {
  margin-top: 24px;
  display: grid;
  gap: 16px;
}

.switch-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 20px;
  background: #f9fafb;
  border: 1px solid #e5e7eb;
  border-radius: 16px;
  padding: 18px 20px;
}

.switch-info {
  flex: 1;
  min-width: 0;
}

.switch-title {
  font-size: 15px;
  font-weight: 800;
  color: #111827;
}

.switch-desc {
  margin-top: 6px;
  font-size: 13px;
  color: #4b5563;
  line-height: 1.6;
}

.switch {
  position: relative;
  width: 52px;
  height: 30px;
  display: inline-block;
  flex-shrink: 0;
}

.switch input {
  opacity: 0;
  width: 0;
  height: 0;
}

.slider {
  position: absolute;
  inset: 0;
  cursor: pointer;
  background: #d1d5db;
  border-radius: 999px;
  transition: 0.25s;
}

.slider::before {
  content: '';
  position: absolute;
  width: 22px;
  height: 22px;
  left: 4px;
  top: 4px;
  border-radius: 50%;
  background: #ffffff;
  transition: 0.25s;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.18);
}

.switch input:checked + .slider {
  background: #111827;
}

.switch input:checked + .slider::before {
  transform: translateX(22px);
}

/* 图片预览 */
.preview-grid {
  margin-top: 24px;
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 20px;
}

.preview-card {
  background: #f9fafb;
  border: 1px solid #e5e7eb;
  border-radius: 16px;
  padding: 18px;
  min-width: 0;
}

.preview-label {
  font-size: 14px;
  font-weight: 800;
  color: #111827;
  margin-bottom: 14px;
}

.preview-box {
  height: 140px;
  border: 1px dashed #d1d5db;
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #6b7280;
  background: #ffffff;
  overflow: hidden;
  text-align: center;
  padding: 10px;
  font-size: 14px;
  font-weight: 600;
}

.preview-box.small {
  height: 100px;
}

.preview-image {
  max-width: 100%;
  max-height: 100%;
  object-fit: contain;
}

.preview-image.small {
  width: 48px;
  height: 48px;
  object-fit: contain;
}

/* 底部操作 */
.action-bar {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  flex-wrap: wrap;
}

.primary-btn,
.secondary-btn {
  height: 44px;
  padding: 0 22px;
  border-radius: 14px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 800;
  transition: all 0.2s ease;
}

.primary-btn {
  border: 1px solid #111827;
  background: #111827;
  color: #ffffff;
}

.secondary-btn {
  border: 1px solid #e5e7eb;
  background: #ffffff;
  color: #111827;
}

.primary-btn:hover {
  background: #1f2937;
  transform: translateY(-2px);
  box-shadow: 0 12px 24px rgba(0, 0, 0, 0.14);
}

.secondary-btn:hover {
  background: #f1f5f9;
  transform: translateY(-2px);
}

.primary-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none;
  box-shadow: none;
}

/* 响应式 */
@media (max-width: 992px) {
  .form-grid,
  .preview-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .section-title {
    font-size: 22px;
  }

  .switch-item {
    flex-direction: column;
    align-items: flex-start;
  }

  .action-bar {
    flex-direction: column;
  }

  .primary-btn,
  .secondary-btn {
    width: 100%;
  }

  .ui-back-link {
    margin-bottom: 16px;
  }
}
</style>
