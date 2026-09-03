<template>
  <div class="py-12 md:py-16">
    <div class="max-w-7xl mx-auto px-6">
      <NuxtLink to="/repos" class="inline-flex items-center gap-1 text-text-muted text-sm hover:text-text-secondary transition-colors mb-6">
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7"/>
        </svg>
        返回全部仓库
      </NuxtLink>

      <div v-if="loading" class="animate-pulse mb-10">
        <div class="h-12 bg-white/10 rounded w-48 mb-3"></div>
        <div class="h-5 bg-white/5 rounded w-96"></div>
      </div>

      <template v-else-if="topic">
        <!-- 主题头部 -->
        <div class="card p-6 md:p-8 mb-10 gradient-border" :style="{ boxShadow: `0 0 60px ${topic.color}15` }">
          <div class="flex items-start gap-4">
            <div
              class="w-16 h-16 rounded-2xl flex items-center justify-center text-3xl shrink-0"
              :style="{ backgroundColor: topic.color + '15' }"
            >
              {{ topic.icon }}
            </div>
            <div>
              <h1 class="text-3xl font-bold text-text-primary mb-2">
                {{ topic.display_name }}
              </h1>
              <p class="text-text-secondary leading-relaxed max-w-2xl">
                {{ topic.description }}
              </p>
              <div class="mt-4">
                <span class="chip" :style="{ backgroundColor: topic.color + '20', color: topic.color }">
                  {{ topic.repo_count }} 个仓库
                </span>
              </div>
            </div>
          </div>
        </div>

        <!-- 仓库列表 -->
        <div class="mb-12">
          <h2 class="text-xl font-semibold text-text-primary mb-6">相关仓库</h2>
          <div v-if="reposLoading" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
            <div v-for="i in 6" :key="i" class="card p-5 h-48 animate-pulse">
              <div class="h-5 bg-white/10 rounded w-3/4 mb-4"></div>
              <div class="h-4 bg-white/5 rounded w-full mb-2"></div>
              <div class="h-4 bg-white/5 rounded w-5/6 mb-4"></div>
              <div class="h-6 bg-white/5 rounded-full w-20"></div>
            </div>
          </div>
          <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
            <RepoCard v-for="repo in topicRepos" :key="repo.id" :repo="repo" />
          </div>
        </div>

        <!-- 相关主题 -->
        <div class="mb-12">
          <h2 class="text-xl font-semibold text-text-primary mb-6">相关主题</h2>
          <div class="flex flex-wrap gap-3">
            <NuxtLink
              v-for="t in relatedTopics"
              :key="t.name"
              :to="`/topics/${t.name}`"
              class="chip text-sm py-2 px-4 transition-all hover:-translate-y-0.5"
              :style="{ backgroundColor: t.color + '15', color: t.color }"
            >
              <span class="mr-1.5">{{ t.icon }}</span>
              {{ t.display_name }}
            </NuxtLink>
          </div>
        </div>

        <!-- 相关文章 -->
        <div v-if="relatedArticles.length > 0">
          <h2 class="text-xl font-semibold text-text-primary mb-6">相关科普文章</h2>
          <div class="grid grid-cols-1 md:grid-cols-3 gap-5">
            <ArticleCard v-for="article in relatedArticles" :key="article.id" :article="article" />
          </div>
        </div>
      </template>

      <div v-else class="text-center py-16">
        <p class="text-text-secondary">主题不存在</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import RepoCard from '~/components/RepoCard.vue'
import ArticleCard from '~/components/ArticleCard.vue'

const { fetchTopic, fetchTopicRepos, fetchTopics, fetchArticles } = useApi()

const route = useRoute()
const topicName = computed(() => route.params.topic as string)

const topic = ref<any>(null)
const loading = ref(true)
const topicRepos = ref<any[]>([])
const reposLoading = ref(true)
const allTopics = ref<any[]>([])
const relatedArticles = ref<any[]>([])

const relatedTopics = computed(() => {
  return allTopics.value.filter(t => t.name !== topicName.value).slice(0, 5)
})

onMounted(async () => {
  try {
    const [topicData, reposData, topicsData, articlesData] = await Promise.all([
      fetchTopic(topicName.value),
      fetchTopicRepos(topicName.value),
      fetchTopics(),
      fetchArticles({ tag: topicName.value, limit: 3 })
    ])
    topic.value = topicData
    topicRepos.value = reposData
    allTopics.value = topicsData
    relatedArticles.value = articlesData
  } finally {
    loading.value = false
    reposLoading.value = false
  }
})
</script>
