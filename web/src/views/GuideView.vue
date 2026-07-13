<template>
  <div class="guide-page">
    <aside class="guide-sidebar">
      <div class="sidebar-title">使用指南</div>

      <a
        v-for="item in navList"
        :key="item.id"
        href="javascript:void(0)"
        :class="{ active: activeSection === item.id }"
        @click="scrollToSection(item.id)"
      >
        {{ item.title }}
      </a>

      <div class="sidebar-footer">
        <RouterLink to="/" class="ui-back-link ui-back-link--block">
          ← 返回首页
        </RouterLink>
      </div>
    </aside>

    <main class="guide-content">
      <section class="hero-card">
        <p class="eyebrow">AI Learning Guide</p>
        <h1>智能学习系统使用指南</h1>
        <p>
          本系统围绕学生的专业背景、学习目标、知识基础和学习过程数据，
          提供个性化学习画像构建、资源生成、学习路径规划、智能辅导与学习效果评估能力。
        </p>
      </section>

      <section id="profile" class="guide-section">
        <div class="section-index">01</div>
        <h2>对话式学习画像自主构建</h2>
        <p>
          系统摒弃传统复杂表单填写方式，学生只需通过自然语言对话，
          即可完成学习画像的自主构建。
        </p>

        <div class="tag-list">
          <span>学生专业</span>
          <span>学习目标</span>
          <span>学习历史</span>
          <span>知识基础</span>
          <span>学习偏好</span>
        </div>

        <div class="grid-list">
          <div>知识基础水平</div>
          <div>认知风格</div>
          <div>学习目标</div>
          <div>学习兴趣</div>
          <div>易错点偏好</div>
          <div>学习节奏</div>
          <div>资源偏好</div>
          <div>知识短板</div>
        </div>

        <p>
          画像会随着学生学习过程持续更新，实现“随学随新”，
          让后续资源推荐和路径规划更加精准。
        </p>
      </section>

      <section id="agents" class="guide-section">
        <div class="section-index">02</div>
        <h2>多智能体协同的资源生成</h2>
        <p>
          系统采用多智能体协同架构，由不同角色的智能体共同完成个性化学习资源生成。
        </p>

        <div class="grid-list">
          <div>学情分析智能体</div>
          <div>知识讲解智能体</div>
          <div>题目生成智能体</div>
          <div>思维导图智能体</div>
          <div>拓展阅读智能体</div>
          <div>视频/动画脚本智能体</div>
          <div>代码实操智能体</div>
        </div>

        <ol class="step-list">
          <li>专业课程讲解文档</li>
          <li>知识点思维导图</li>
          <li>不同类型练习题目</li>
          <li>拓展阅读材料</li>
          <li>多模态教学视频或动画</li>
          <li>代码类实操案例</li>
        </ol>
      </section>

      <section id="path" class="guide-section">
        <div class="section-index">03</div>
        <h2>个性化学习路径规划和资源推送</h2>
        <p>
          系统整合个性化学习资源，并结合大模型对学生学习情况的深度分析，
          为学生规划科学、动态的学习路径。
        </p>

        <ol class="step-list">
          <li>基础概念理解</li>
          <li>核心知识点学习</li>
          <li>典型案例分析</li>
          <li>练习题巩固</li>
          <li>项目或代码实操</li>
          <li>阶段性测试与反馈</li>
        </ol>
      </section>

      <section id="tutor" class="guide-section">
        <div class="section-index">04</div>
        <h2>智能辅导</h2>
        <p>
          当学生在学习过程中遇到问题时，系统可提供即时、多模态的智能答疑服务。
        </p>

        <div class="grid-list">
          <div>详细文字解答</div>
          <div>图解说明</div>
          <div>知识点拆解</div>
          <div>解题步骤分析</div>
          <div>代码错误定位</div>
          <div>短视频讲解脚本</div>
          <div>动画化说明建议</div>
        </div>
      </section>

      <section id="evaluate" class="guide-section">
        <div class="section-index">05</div>
        <h2>学习效果评估</h2>
        <p>
          系统会实时跟踪学生学习行为、练习测试结果和资源使用反馈，
          对学习效果进行多维度评估。
        </p>

        <div class="grid-list">
          <div>知识掌握程度</div>
          <div>练习正确率</div>
          <div>学习活跃度</div>
          <div>资源使用情况</div>
          <div>易错知识点分布</div>
          <div>阶段性学习进步</div>
          <div>学习目标完成度</div>
        </div>

        <p>
          系统会根据评估结果动态调整学习资源推送策略和学习计划，
          实现学习方案的持续优化。
        </p>
      </section>
    </main>
  </div>
</template>

<script setup>
import { onMounted, onBeforeUnmount, ref } from 'vue'
import { RouterLink } from 'vue-router'

const activeSection = ref('profile')

const scrollToSection = id => {
  const target = document.getElementById(id)

  if (target) {
    target.scrollIntoView({
      behavior: 'smooth',
      block: 'start',
    })

    activeSection.value = id
  }
}

const navList = [
  { id: 'profile', title: '1. 学习画像构建' },
  { id: 'agents', title: '2. 多智能体资源生成' },
  { id: 'path', title: '3. 学习路径与资源推送' },
  { id: 'tutor', title: '4. 智能辅导' },
  { id: 'evaluate', title: '5. 学习效果评估' },
]

let observer = null

onMounted(() => {
  const sections = document.querySelectorAll('.guide-section')

  observer = new IntersectionObserver(
    entries => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          activeSection.value = entry.target.id
        }
      })
    },
    {
      rootMargin: '-30% 0px -60% 0px',
      threshold: 0.1,
    },
  )

  sections.forEach(section => observer.observe(section))
})

onBeforeUnmount(() => {
  if (observer) observer.disconnect()
})
</script>

<style scoped>
.guide-page {
  min-height: 100vh;
  display: flex;
  gap: 30px;
  padding: 32px;
  background: #f7f8fa;
  color: #111827;
  box-sizing: border-box;
  scroll-behavior: smooth;
}

.guide-sidebar {
  width: 260px;
  flex-shrink: 0;
  position: sticky;
  top: 28px;
  height: fit-content;
  background: #ffffff;
  border: 1px solid #e5e7eb;
  border-radius: 18px;
  padding: 18px;
  box-shadow: var(--shadow-md);
}

.sidebar-title {
  font-size: 20px;
  font-weight: 800;
  color: #111827;
  margin-bottom: 14px;
  padding: 8px 10px;
}

.guide-sidebar a:not(.ui-back-link--block) {
  display: block;
  padding: 12px 14px;
  margin: 8px 0;
  border-radius: 14px;
  color: #111827;
  text-decoration: none;
  font-size: 14px;
  font-weight: 600;
  transition: all 0.2s ease;
}

.guide-sidebar a:not(.ui-back-link--block):hover,
.guide-sidebar a:not(.ui-back-link--block).active {
  background: #f1f5f9;
  transform: translateX(4px);
}

.sidebar-footer {
  margin-top: 8px;
  padding-top: 12px;
  border-top: 1px solid #e5e7eb;
}

.guide-content {
  flex: 1;
  max-width: 1050px;
  padding-bottom: 240px;
}

.hero-card,
.guide-section {
  position: relative;
  overflow: hidden;
  background: #ffffff;
  border: 1px solid #e5e7eb;
  border-radius: 18px;
  padding: 34px;
  margin-bottom: 24px;
  box-shadow: var(--shadow-md);
  scroll-margin-top: 32px;
}

.eyebrow {
  margin: 0 0 10px;
  font-size: 13px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: #111827;
}

.hero-card h1 {
  margin: 0 0 14px;
  font-size: 34px;
  line-height: 1.25;
  color: #111827;
}

.hero-card p,
.guide-section p {
  line-height: 1.9;
  font-size: 15px;
  color: #111827;
}

.guide-section h2 {
  margin: 0 0 16px;
  padding-right: 80px;
  font-size: 25px;
  line-height: 1.35;
  color: #111827;
}

.section-index {
  position: absolute;
  right: 28px;
  top: 24px;
  font-size: 42px;
  font-weight: 900;
  color: #e5e7eb;
  line-height: 1;
}

.tag-list {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin: 18px 0;
}

.tag-list span {
  background: #f3f4f6;
  color: #111827;
  padding: 7px 13px;
  border-radius: 999px;
  font-size: 13px;
  font-weight: 600;
  border: 1px solid #e5e7eb;
}

.grid-list {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
  margin: 18px 0;
}

.grid-list div {
  background: #f9fafb;
  border: 1px solid #e5e7eb;
  border-radius: 14px;
  padding: 13px 15px;
  font-size: 14px;
  font-weight: 600;
  color: #111827;
}

.step-list {
  margin: 18px 0 0;
  padding-left: 22px;
}

.step-list li {
  margin-bottom: 10px;
  line-height: 1.8;
  font-size: 15px;
  color: #111827;
  font-weight: 500;
}

@media (max-width: 900px) {
  .guide-page {
    flex-direction: column;
    padding: 18px;
  }

  .guide-sidebar {
    position: static;
    width: 100%;
    box-sizing: border-box;
  }

  .guide-content {
    max-width: 100%;
  }

  .grid-list {
    grid-template-columns: 1fr;
  }

  .hero-card,
  .guide-section {
    padding: 24px;
    border-radius: 18px;
  }

  .hero-card h1 {
    font-size: 28px;
  }

  .guide-section h2 {
    font-size: 22px;
    padding-right: 56px;
  }

  .section-index {
    font-size: 34px;
    right: 22px;
  }
}
</style>