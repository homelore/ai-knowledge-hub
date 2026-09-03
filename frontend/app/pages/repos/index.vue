<template>
  <div class="py-12 md:py-16">
    <div class="max-w-7xl mx-auto px-6">
      <!-- 页面标题 -->
      <div class="mb-8">
        <h1 class="text-3xl md:text-4xl font-bold text-text-primary mb-2">
          仓库动态
        </h1>
        <p class="text-text-secondary">
          追踪 GitHub 上最热门的 AI 开源项目 · 按 star 数量筛选
        </p>
      </div>

      <!-- 筛选栏 -->
      <div class="card p-4 mb-8">
        <div class="flex flex-col md:flex-row md:items-center gap-4">
          <!-- 主题筛选 -->
          <div class="flex items-center gap-2 flex-wrap">
            <span class="text-text-muted text-sm whitespace-nowrap">主题：</span>
            <button
              v-for="topic in allTopics"
              :key="topic.name"
              :class="[
                'chip text-xs transition-colors',
                selectedTopics.includes(topic.name)
                  ? 'bg-accent-purple/20 text-accent-purple'
                  : 'bg-white/5 text-text-secondary hover:bg-white/10'
              ]"
              @click="toggleTopic(topic.name)"
            >
              {{ topic.display_name }}
            </button>
            <button
              v-if="selectedTopics.length > 0"
              class="chip text-xs bg-white/5 text-text-muted hover:bg-white/10 transition-colors"
              @click="selectedTopics = []"
            >
              清除
            </button>
          </div>

          <div class="md:ml-auto flex items-center gap-4">
            <!-- 排序 -->
            <select
              v-model="sortBy"
              class="bg-bg-card border border-white/10 rounded-lg px-3 py-1.5 text-sm text-text-primary focus:outline-none focus:border-accent-purple/50"
            >
              <option value="stars">Star 总数</option>
              <option value="weekly_gain">本周增长</option>
              <option value="updated">最近更新</option>
            </select>
          </div>
        </div>
      </div>

      <!-- 最近更新提示 -->
      <div v-if="lastFetch" class="flex items-center gap-2 mb-6 text-sm text-text-muted">
        <span class="w-2 h-2 rounded-full bg-accent-green"></span>
        最近更新：{{ formatDate(lastFetch.finished_at) }} · {{ lastFetch.new_count }} 个新仓库
      </div>

      <!-- 结果计数 -->
      <div class="text-text-muted text-sm mb-4">
        共 {{ total }} 个仓库
      </div>

      <!-- 仓库网格 -->
      <div v-if="loading" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
        <div v-for="i in 9" :key="i" class="card p-5 h-48 animate-pulse">
          <div class="h-5 bg-white/10 rounded w-3/4 mb-4"></div>
          <div class="h-4 bg-white/5 rounded w-full mb-2"></div>
          <div class="h-4 bg-white/5 rounded w-5/6 mb-4"></div>
          <div class="h-6 bg-white/5 rounded-full w-20"></div>
        </div>
      </div>

      <div v-else-if="repos.length === 0" class="text-center py-16">
        <div class="text-4xl mb-4">🔍</div>
        <p class="text-text-secondary">没有找到匹配的仓库</p>
      </div>

      <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
        <RepoCard v-for="repo in repos" :key="repo.id" :repo="repo" />
      </div>

      <!-- 加载更多 -->
      <div v-if="hasMore && !loading" class="text-center mt-10">
        <button
          @click="loadMore"
          class="px-6 py-2.5 border border-white/15 text-text-primary text-sm font-medium rounded-lg hover:bg-white/5 transition-colors"
        >
          加载更多
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import RepoCard from '~/components/RepoCard.vue'

const { fetchRepos, fetchTopics, fetchLastFetchLog } = useApi()
const { formatDate } = useFormat()

const repos = ref<any[]>([])
const loading = ref(true)
const total = ref(0)
const page = ref(1)
const hasMore = ref(true)
const sortBy = ref('weekly_gain')
const selectedTopics = ref<string[]>([])
const allTopics = ref<any[]>([])
const lastFetch = ref<any>(null)

const loadRepos = async (reset = false) => {
  if (reset) {
    page.value = 1
    repos.value = []
    hasMore.value = true
  }

  loading.value = true
  try {
    const result = await fetchRepos({
      page: page.value,
      limit: 9,
      sort: sortBy.value as any,
      topic: selectedTopics.value[0] || undefined
    })
    repos.value = reset ? result.items : [...repos.value, ...result.items]
    total.value = result.total
    hasMore.value = result.has_more
  } finally {
    loading.value = false
  }
}

const loadMore = () => {
  page.value++
  loadRepos()
}

const toggleTopic = (name: string) => {
  const idx = selectedTopics.value.indexOf(name)
  if (idx > -1) {
    selectedTopics.value.splice(idx, 1)
  } else {
    selectedTopics.value = [name] // 单选模式，简化实现
  }
  loadRepos(true)
}

// 监听排序变化
watch(sortBy, () => loadRepos(true))

onMounted(async () => {
  const [topicsResult, fetchLogResult] = await Promise.all([
    fetchTopics(),
    fetchLastFetchLog()
  ])
  allTopics.value = topicsResult
  lastFetch.value = fetchLogResult
  loadRepos(true)
})
</script>
