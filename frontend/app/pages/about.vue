<template>
  <div class="py-12 md:py-16">
    <div class="max-w-4xl mx-auto px-6">
      <!-- 头部 -->
      <div class="text-center mb-16">
        <div class="w-20 h-20 mx-auto rounded-2xl bg-gradient-text flex items-center justify-center text-white font-bold text-2xl mb-6 shadow-glow">
          AI
        </div>
        <h1 class="text-3xl md:text-4xl font-bold text-text-primary mb-4">
          关于 AI Knowledge Hub
        </h1>
        <p class="text-text-secondary text-lg max-w-2xl mx-auto">
          一站式探索人工智能的世界，从科普知识到前沿技术动态
        </p>
      </div>

      <!-- 统计卡片 -->
      <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-16">
        <div v-for="stat in statsList" :key="stat.label" class="card p-5 text-center gradient-border">
          <div class="text-2xl md:text-3xl font-bold gradient-text mb-1">{{ stat.value }}</div>
          <div class="text-text-muted text-sm">{{ stat.label }}</div>
        </div>
      </div>

      <!-- 项目介绍 -->
      <div class="card p-6 md:p-8 mb-8">
        <h2 class="text-xl font-semibold text-text-primary mb-4 flex items-center gap-2">
          <span class="text-2xl">🎯</span>
          项目目标
        </h2>
        <p class="text-text-secondary leading-relaxed mb-4">
          AI Knowledge Hub 致力于打造一个 AI 知识聚合平台，让每个人都能方便地了解人工智能的最新进展。
        </p>
        <p class="text-text-secondary leading-relaxed">
          我们相信，AI 不应该只是少数专家的领域。通过清晰的科普内容和客观的数据追踪，让更多人能够理解和参与到这场技术变革中。
        </p>
      </div>

      <!-- 更新机制 -->
      <div class="card p-6 md:p-8 mb-8">
        <h2 class="text-xl font-semibold text-text-primary mb-6 flex items-center gap-2">
          <span class="text-2xl">🔄</span>
          数据更新机制
        </h2>

        <div class="space-y-6">
          <div class="flex gap-4">
            <div class="w-10 h-10 rounded-full bg-accent-green/15 text-accent-green flex items-center justify-center shrink-0 font-bold">
              1
            </div>
            <div>
              <h3 class="text-text-primary font-medium mb-1">定时触发</h3>
              <p class="text-text-secondary text-sm">每周一 09:00（北京时间），Agent 自动启动拉取任务</p>
            </div>
          </div>

          <div class="flex gap-4">
            <div class="w-10 h-10 rounded-full bg-accent-blue/15 text-accent-blue flex items-center justify-center shrink-0 font-bold">
              2
            </div>
            <div>
              <h3 class="text-text-primary font-medium mb-1">GitHub API 拉取</h3>
              <p class="text-text-secondary text-sm">遍历 AI 相关主题，调用 GitHub Search API 搜索热门仓库</p>
            </div>
          </div>

          <div class="flex gap-4">
            <div class="w-10 h-10 rounded-full bg-accent-purple/15 text-accent-purple flex items-center justify-center shrink-0 font-bold">
              3
            </div>
            <div>
              <h3 class="text-text-primary font-medium mb-1">筛选与分类</h3>
              <p class="text-text-secondary text-sm">按 star 数量筛选，自动分类到对应主题，计算本周增长量</p>
            </div>
          </div>

          <div class="flex gap-4">
            <div class="w-10 h-10 rounded-full bg-accent-gold/15 text-accent-gold flex items-center justify-center shrink-0 font-bold">
              4
            </div>
            <div>
              <h3 class="text-text-primary font-medium mb-1">更新入库</h3>
              <p class="text-text-secondary text-sm">更新仓库信息、Release 动态和 Star 历史数据</p>
            </div>
          </div>
        </div>
      </div>

      <!-- 技术栈 -->
      <div class="card p-6 md:p-8">
        <h2 class="text-xl font-semibold text-text-primary mb-6 flex items-center gap-2">
          <span class="text-2xl">🛠️</span>
          技术栈
        </h2>

        <div class="grid grid-cols-2 md:grid-cols-3 gap-4">
          <div v-for="tech in techStack" :key="tech.name" class="flex items-center gap-3 p-3 bg-white/3 rounded-lg">
            <div class="w-10 h-10 rounded-lg flex items-center justify-center text-lg" :style="{ backgroundColor: tech.color + '15' }">
              {{ tech.icon }}
            </div>
            <div>
              <div class="text-text-primary font-medium text-sm">{{ tech.name }}</div>
              <div class="text-text-muted text-xs">{{ tech.desc }}</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
const { fetchStats } = useApi()

const statsList = ref([
  { value: '...', label: '收录仓库' },
  { value: '...', label: 'AI 主题' },
  { value: '...', label: '科普文章' },
  { value: '...', label: '本周新增' }
])

const techStack = [
  { name: 'Vue 3', desc: '前端框架', icon: '💚', color: '#42b883' },
  { name: 'Nuxt', desc: '元框架', icon: '⚡', color: '#00dc82' },
  { name: 'Tailwind CSS', desc: '样式框架', icon: '🎨', color: '#38bdf8' },
  { name: 'FastAPI', desc: 'Web 框架', icon: '🚀', color: '#009688' },
  { name: 'SQLite', desc: '数据存储', icon: '🗄️', color: '#003b57' },
  { name: 'GitHub API', desc: '数据来源', icon: '🐙', color: '#333' }
]

onMounted(async () => {
  const stats = await fetchStats()
  statsList.value = [
    { value: stats.total_repos.toString(), label: '收录仓库' },
    { value: stats.total_topics.toString(), label: 'AI 主题' },
    { value: stats.total_articles.toString(), label: '科普文章' },
    { value: `+${stats.weekly_new_repos}`, label: '本周新增' }
  ]
})
</script>
