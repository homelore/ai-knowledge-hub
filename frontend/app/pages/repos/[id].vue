<template>
  <div class="py-12 md:py-16">
    <div class="max-w-5xl mx-auto px-6">
      <!-- 返回 -->
      <NuxtLink to="/repos" class="inline-flex items-center gap-1 text-text-muted text-sm hover:text-text-secondary transition-colors mb-6">
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7"/>
        </svg>
        返回仓库列表
      </NuxtLink>

      <div v-if="loading" class="animate-pulse">
        <div class="h-8 bg-white/10 rounded w-1/3 mb-4"></div>
        <div class="h-5 bg-white/5 rounded w-2/3 mb-6"></div>
        <div class="h-64 bg-white/5 rounded-card mb-8"></div>
      </div>

      <template v-else-if="repo">
        <!-- 头部信息 -->
        <div class="card p-6 md:p-8 mb-8 gradient-border">
          <div class="flex flex-col md:flex-row md:items-start md:justify-between gap-4 mb-4">
            <div>
              <h1 class="text-2xl md:text-3xl font-bold text-text-primary mb-2">
                {{ repo.full_name }}
              </h1>
              <p class="text-text-secondary leading-relaxed">
                {{ repo.description }}
              </p>
            </div>
            <a
              :href="repo.url"
              target="_blank"
              rel="noopener"
              class="shrink-0 inline-flex items-center gap-2 px-4 py-2 bg-white/5 border border-white/10 rounded-lg text-text-primary text-sm hover:bg-white/10 transition-colors"
            >
              <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 24 24">
                <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/>
              </svg>
              在 GitHub 查看
            </a>
          </div>

          <!-- 主题标签 -->
          <div class="flex flex-wrap gap-2 mb-6">
            <TopicBadge v-for="topic in repo.topics" :key="topic" :name="topic">
              {{ topicName(topic) }}
            </TopicBadge>
          </div>

          <!-- 统计数据 -->
          <div class="grid grid-cols-2 md:grid-cols-4 gap-4 pt-6 border-t border-white/5">
            <div>
              <div class="text-2xl font-bold text-accent-gold">{{ formatNumber(repo.stars) }}</div>
              <div class="text-text-muted text-xs mt-1">Stars</div>
            </div>
            <div>
              <div class="text-2xl font-bold text-text-primary">{{ formatNumber(repo.forks) }}</div>
              <div class="text-text-muted text-xs mt-1">Forks</div>
            </div>
            <div>
              <div class="text-2xl font-bold text-accent-green">+{{ formatNumber(repo.weekly_star_gain) }}</div>
              <div class="text-text-muted text-xs mt-1">本周增长</div>
            </div>
            <div>
              <div class="text-2xl font-bold text-text-primary">{{ repo.language }}</div>
              <div class="text-text-muted text-xs mt-1">主要语言</div>
            </div>
          </div>
        </div>

        <!-- Star 趋势图 -->
        <div v-if="starHistory.length > 0" class="card p-6 mb-8">
          <h2 class="text-lg font-semibold text-text-primary mb-4">Star 增长趋势</h2>
          <div class="h-48 relative">
            <svg class="w-full h-full" viewBox="0 0 600 160" preserveAspectRatio="none">
              <!-- 网格线 -->
              <line x1="0" y1="40" x2="600" y2="40" stroke="rgba(148,163,184,0.1)" stroke-dasharray="4 4"/>
              <line x1="0" y1="80" x2="600" y2="80" stroke="rgba(148,163,184,0.1)" stroke-dasharray="4 4"/>
              <line x1="0" y1="120" x2="600" y2="120" stroke="rgba(148,163,184,0.1)" stroke-dasharray="4 4"/>

              <!-- 渐变填充 -->
              <defs>
                <linearGradient id="starGradient" x1="0%" y1="0%" x2="0%" y2="100%">
                  <stop offset="0%" style="stop-color:#34d399;stop-opacity:0.3"/>
                  <stop offset="100%" style="stop-color:#34d399;stop-opacity:0"/>
                </linearGradient>
              </defs>

              <!-- 面积图 -->
              <path :d="areaPath" fill="url(#starGradient)"/>

              <!-- 折线 -->
              <path :d="linePath" fill="none" stroke="#34d399" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>

              <!-- 数据点 -->
              <circle
                v-for="(point, i) in chartPoints"
                :key="i"
                :cx="point.x"
                :cy="point.y"
                r="4"
                fill="#0f172a"
                stroke="#34d399"
                stroke-width="2"
              />
            </svg>

            <!-- X 轴标签 -->
            <div class="flex justify-between text-xs text-text-muted mt-2 px-1">
              <span v-for="item in starHistory" :key="item.week">
                {{ item.week.replace('2026-W', 'W') }}
              </span>
            </div>
          </div>
        </div>

        <!-- Release 动态 -->
        <div class="card p-6">
          <h2 class="text-lg font-semibold text-text-primary mb-4">最近版本发布</h2>

          <div v-if="releasesLoading" class="space-y-4">
            <div v-for="i in 3" :key="i" class="animate-pulse">
              <div class="h-5 bg-white/10 rounded w-32 mb-2"></div>
              <div class="h-4 bg-white/5 rounded w-full mb-1"></div>
              <div class="h-4 bg-white/5 rounded w-5/6"></div>
            </div>
          </div>

          <div v-else-if="releases.length === 0" class="text-text-muted text-sm py-8 text-center">
            暂无 Release 数据
          </div>

          <div v-else class="space-y-4">
            <div v-for="release in releases" :key="release.id" class="pb-4 border-b border-white/5 last:border-0 last:pb-0">
              <div class="flex items-center gap-3 mb-2">
                <span class="chip bg-accent-blue/15 text-accent-blue font-mono text-xs">
                  {{ release.tag_name }}
                </span>
                <span class="text-text-muted text-xs">{{ formatDate(release.published_at) }}</span>
              </div>
              <h3 class="text-text-primary font-medium mb-2">{{ release.release_name }}</h3>
              <p class="text-text-secondary text-sm leading-relaxed whitespace-pre-line line-clamp-3">
                {{ release.body }}
              </p>
            </div>
          </div>
        </div>
      </template>

      <div v-else class="text-center py-16">
        <p class="text-text-secondary">仓库不存在</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import TopicBadge from '~/components/TopicBadge.vue'

const { fetchRepo, fetchRepoReleases, fetchRepoStarHistory } = useApi()
const { formatNumber, formatDate } = useFormat()

const route = useRoute()
const repoId = computed(() => Number(route.params.id))

const repo = ref<any>(null)
const loading = ref(true)
const releases = ref<any[]>([])
const releasesLoading = ref(true)
const starHistory = ref<any[]>([])

const topicNames: Record<string, string> = {
  llm: 'LLM',
  rag: 'RAG',
  agent: 'Agent',
  transformer: 'Transformer',
  diffusion: 'Diffusion',
  mlops: 'MLOps'
}

const topicName = (name: string) => topicNames[name] || name

// 计算图表坐标点
const chartPoints = computed(() => {
  if (starHistory.value.length === 0) return []
  const data = starHistory.value
  const minStar = Math.min(...data.map(d => d.stars))
  const maxStar = Math.max(...data.map(d => d.stars))
  const range = maxStar - minStar || 1
  const width = 600
  const height = 140
  const padding = 10

  return data.map((d, i) => ({
    x: (i / (data.length - 1)) * width,
    y: height - padding - ((d.stars - minStar) / range) * (height - padding * 2)
  }))
})

const linePath = computed(() => {
  if (chartPoints.value.length === 0) return ''
  return chartPoints.value.map((p, i) => {
    return `${i === 0 ? 'M' : 'L'} ${p.x} ${p.y}`
  }).join(' ')
})

const areaPath = computed(() => {
  if (chartPoints.value.length === 0) return ''
  const points = chartPoints.value
  const lastX = points[points.length - 1].x
  return `${linePath.value} L ${lastX} 150 L 0 150 Z`
})

onMounted(async () => {
  try {
    const [repoData, releasesData, historyData] = await Promise.all([
      fetchRepo(repoId.value),
      fetchRepoReleases(repoId.value),
      fetchRepoStarHistory(repoId.value)
    ])
    repo.value = repoData
    releases.value = releasesData
    starHistory.value = historyData
  } finally {
    loading.value = false
    releasesLoading.value = false
  }
})
</script>

<style scoped>
.line-clamp-3 {
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
</style>
