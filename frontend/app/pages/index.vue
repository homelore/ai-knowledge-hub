<template>
  <div>
    <!-- Hero Section -->
    <section class="relative overflow-hidden py-20 md:py-28">
      <div class="absolute inset-0 bg-gradient-hero pointer-events-none"></div>
      <div class="absolute top-0 left-1/2 -translate-x-1/2 w-[800px] h-[400px] bg-accent-purple/10 blur-[120px] rounded-full pointer-events-none"></div>

      <div class="max-w-7xl mx-auto px-6 relative">
        <div class="max-w-3xl mx-auto text-center">
          <span class="chip bg-accent-blue/10 text-accent-blue mb-6">
            <svg class="w-3.5 h-3.5 mr-1.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"/>
            </svg>
            每周更新 · 追踪 AI 前沿
          </span>

          <h1 class="text-4xl md:text-6xl font-bold mb-6 leading-tight">
            <span class="gradient-text">探索人工智能</span>
            <br />
            <span class="text-text-primary">的无限可能</span>
          </h1>

          <p class="text-text-secondary text-lg md:text-xl leading-relaxed mb-10 max-w-2xl mx-auto">
            从科普知识到 GitHub 热门项目，一站式了解 AI 世界。
            <br class="hidden md:block" />
            每周自动拉取最新技术动态，不错过每一个重要突破。
          </p>

          <div class="flex flex-col sm:flex-row items-center justify-center gap-4">
            <NuxtLink
              to="/repos"
              class="px-6 py-3 bg-gradient-text text-white font-medium rounded-lg shadow-glow hover:shadow-glowBlue transition-all hover:-translate-y-0.5"
            >
              浏览热门仓库
            </NuxtLink>
            <NuxtLink
              to="/articles/llm-explained"
              class="px-6 py-3 border border-white/15 text-text-primary font-medium rounded-lg hover:bg-white/5 transition-colors"
            >
              开始学习 AI 知识
            </NuxtLink>
          </div>
        </div>

        <!-- 统计数字 -->
        <div class="grid grid-cols-2 md:grid-cols-4 gap-6 mt-20 max-w-4xl mx-auto">
          <div v-for="stat in heroStats" :key="stat.label" class="text-center">
            <div class="text-3xl md:text-4xl font-bold gradient-text">{{ stat.value }}</div>
            <div class="text-text-muted text-sm mt-1">{{ stat.label }}</div>
          </div>
        </div>
      </div>
    </section>

    <!-- 本周热门仓库 -->
    <section class="py-16 md:py-20">
      <div class="max-w-7xl mx-auto px-6">
        <div class="flex items-end justify-between mb-10">
          <div>
            <h2 class="text-2xl md:text-3xl font-bold text-text-primary mb-2">
              本周热门仓库
            </h2>
            <p class="text-text-secondary text-sm">
              按 star 增长数排序 · 数据每周更新
            </p>
          </div>
          <NuxtLink to="/repos" class="text-accent-blue text-sm font-medium hover:text-accent-purple transition-colors hidden sm:flex items-center gap-1">
            查看全部
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"/>
            </svg>
          </NuxtLink>
        </div>

        <div v-if="loading" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          <div v-for="i in 6" :key="i" class="card p-5 h-48 animate-pulse">
            <div class="h-5 bg-white/10 rounded w-3/4 mb-4"></div>
            <div class="h-4 bg-white/5 rounded w-full mb-2"></div>
            <div class="h-4 bg-white/5 rounded w-5/6 mb-4"></div>
            <div class="h-6 bg-white/5 rounded-full w-20"></div>
          </div>
        </div>

        <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          <RepoCard v-for="repo in topRepos" :key="repo.id" :repo="repo" />
        </div>
      </div>
    </section>

    <!-- 主题分类 -->
    <section class="py-16 md:py-20 border-t border-white/5">
      <div class="max-w-7xl mx-auto px-6">
        <div class="text-center mb-12">
          <h2 class="text-2xl md:text-3xl font-bold text-text-primary mb-2">
            探索 AI 主题
          </h2>
          <p class="text-text-secondary text-sm">
            按领域分类，深入了解不同方向的 AI 技术
          </p>
        </div>

        <div v-if="topicsLoading" class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
          <div v-for="i in 6" :key="i" class="card p-5 text-center animate-pulse">
            <div class="w-12 h-12 rounded-xl bg-white/10 mx-auto mb-3"></div>
            <div class="h-5 bg-white/10 rounded w-20 mx-auto mb-2"></div>
            <div class="h-3 bg-white/5 rounded w-16 mx-auto"></div>
          </div>
        </div>

        <div v-else class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
          <NuxtLink
            v-for="topic in topics"
            :key="topic.name"
            :to="`/topics/${topic.name}`"
            class="card p-5 text-center transition-all duration-300 hover:-translate-y-1 group gradient-border"
          >
            <div class="text-3xl mb-3">{{ topic.icon }}</div>
            <h3 class="text-text-primary font-semibold text-sm mb-1 group-hover:text-accent-blue transition-colors">
              {{ topic.display_name }}
            </h3>
            <p class="text-text-muted text-xs">{{ topic.repo_count }} 个仓库</p>
          </NuxtLink>
        </div>
      </div>
    </section>

    <!-- 科普文章推荐 -->
    <section class="py-16 md:py-20 border-t border-white/5">
      <div class="max-w-7xl mx-auto px-6">
        <div class="flex items-end justify-between mb-10">
          <div>
            <h2 class="text-2xl md:text-3xl font-bold text-text-primary mb-2">
              AI 科普文章
            </h2>
            <p class="text-text-secondary text-sm">
              从零开始，系统学习人工智能基础知识
            </p>
          </div>
        </div>

        <div v-if="articlesLoading" class="grid grid-cols-1 md:grid-cols-3 gap-5">
          <div v-for="i in 3" :key="i" class="card p-5 h-52 animate-pulse">
            <div class="h-6 bg-white/10 rounded-full w-16 mb-4"></div>
            <div class="h-6 bg-white/10 rounded w-full mb-3"></div>
            <div class="h-4 bg-white/5 rounded w-full mb-2"></div>
            <div class="h-4 bg-white/5 rounded w-4/5 mb-4"></div>
            <div class="flex gap-2">
              <div class="h-6 bg-white/5 rounded-full w-14"></div>
              <div class="h-6 bg-white/5 rounded-full w-14"></div>
            </div>
          </div>
        </div>

        <div v-else class="grid grid-cols-1 md:grid-cols-3 gap-5">
          <ArticleCard v-for="article in beginnerArticles" :key="article.id" :article="article" />
        </div>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import RepoCard from '~/components/RepoCard.vue'
import ArticleCard from '~/components/ArticleCard.vue'

const { fetchRepos, fetchTopics, fetchArticles, fetchStats } = useApi()

// Hero 统计
const heroStats = ref([
  { value: '...', label: '收录仓库' },
  { value: '...', label: 'AI 主题' },
  { value: '...', label: '科普文章' },
  { value: '...', label: '本周新增' }
])

// 本周热门
const loading = ref(true)
const topRepos = ref<any[]>([])

// 主题
const topicsLoading = ref(true)
const topics = ref<any[]>([])

// 入门文章
const articlesLoading = ref(true)
const beginnerArticles = ref<any[]>([])

// 加载数据
onMounted(async () => {
  try {
    const [reposResult, topicsResult, articlesResult, statsResult] = await Promise.all([
      fetchRepos({ sort: 'weekly_gain', limit: 6 }),
      fetchTopics(),
      fetchArticles({ difficulty: 'beginner', limit: 3 }),
      fetchStats()
    ])

    topRepos.value = reposResult.items
    topics.value = topicsResult
    beginnerArticles.value = articlesResult

    heroStats.value = [
      { value: statsResult.total_repos.toString(), label: '收录仓库' },
      { value: statsResult.total_topics.toString(), label: 'AI 主题' },
      { value: statsResult.total_articles.toString(), label: '科普文章' },
      { value: `+${statsResult.weekly_new_repos}`, label: '本周新增' }
    ]
  } finally {
    loading.value = false
    topicsLoading.value = false
    articlesLoading.value = false
  }
})
</script>
