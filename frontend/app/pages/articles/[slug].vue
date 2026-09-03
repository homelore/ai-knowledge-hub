<template>
  <div class="py-12 md:py-16">
    <div class="max-w-3xl mx-auto px-6">
      <!-- 返回 -->
      <NuxtLink to="/" class="inline-flex items-center gap-1 text-text-muted text-sm hover:text-text-secondary transition-colors mb-6">
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7"/>
        </svg>
        返回首页
      </NuxtLink>

      <div v-if="loading" class="animate-pulse">
        <div class="h-10 bg-white/10 rounded w-4/5 mb-4"></div>
        <div class="h-5 bg-white/5 rounded w-1/3 mb-8"></div>
        <div class="space-y-3">
          <div class="h-4 bg-white/5 rounded w-full"></div>
          <div class="h-4 bg-white/5 rounded w-full"></div>
          <div class="h-4 bg-white/5 rounded w-5/6"></div>
        </div>
      </div>

      <article v-else-if="article" class="article-content">
        <!-- 文章头部 -->
        <header class="mb-10">
          <div class="flex items-center gap-3 mb-4">
            <span :class="['chip', difficultyColor(article.difficulty)]">
              {{ difficultyLabel(article.difficulty) }}
            </span>
            <span class="text-text-muted text-sm">{{ formatReadTime(article.read_time) }}</span>
            <span class="text-text-muted text-sm">·</span>
            <span class="text-text-muted text-sm">{{ formatDateFull(article.created_at) }}</span>
          </div>

          <h1 class="text-3xl md:text-4xl font-bold text-text-primary leading-tight mb-4">
            {{ article.title }}
          </h1>

          <p class="text-text-secondary text-lg leading-relaxed">
            {{ article.summary }}
          </p>

          <!-- 标签 -->
          <div class="flex flex-wrap gap-2 mt-6 pt-6 border-t border-white/5">
            <TopicBadge v-for="tag in article.tags" :key="tag" :name="tag">
              {{ tagLabel(tag) }}
            </TopicBadge>
          </div>
        </header>

        <!-- 正文 -->
        <div
          class="prose prose-invert max-w-none"
          v-html="renderedContent"
        ></div>

        <!-- 上下篇 -->
        <div v-if="relatedArticles.length > 0" class="mt-16 pt-8 border-t border-white/5">
          <h3 class="text-lg font-semibold text-text-primary mb-4">相关文章</h3>
          <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
            <ArticleCard v-for="a in relatedArticles" :key="a.id" :article="a" />
          </div>
        </div>
      </article>

      <div v-else class="text-center py-16">
        <p class="text-text-secondary">文章不存在</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import TopicBadge from '~/components/TopicBadge.vue'
import ArticleCard from '~/components/ArticleCard.vue'

const { fetchArticle } = useApi()
const { formatReadTime, formatDateFull, difficultyLabel, difficultyColor } = useFormat()

const route = useRoute()
const slug = computed(() => route.params.slug as string)

const article = ref<any>(null)
const loading = ref(true)
const relatedArticles = ref<any[]>([])

const tagLabels: Record<string, string> = {
  llm: 'LLM',
  rag: 'RAG',
  agent: 'Agent',
  transformer: 'Transformer',
  diffusion: 'Diffusion',
  mlops: 'MLOps'
}

const tagLabel = (tag: string) => tagLabels[tag] || tag

const renderedContent = computed(() => {
  if (!article.value) return ''
  // 后端已渲染为 HTML，直接使用
  return article.value.content || ''
})

onMounted(async () => {
  try {
    const articleData = await fetchArticle(slug.value)
    article.value = articleData
    // 文章详情接口已返回 related 字段
    relatedArticles.value = articleData?.related || []
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
/* 文章内容样式 */
.prose :deep(h1) {
  @apply text-2xl font-bold text-text-primary mt-10 mb-4;
}
.prose :deep(h2) {
  @apply text-xl font-bold text-text-primary mt-8 mb-3;
}
.prose :deep(h3) {
  @apply text-lg font-semibold text-text-primary mt-6 mb-2;
}
.prose :deep(p) {
  @apply text-text-secondary leading-relaxed my-4;
}
.prose :deep(ul) {
  @apply text-text-secondary leading-relaxed my-4 pl-6 list-disc;
}
.prose :deep(ol) {
  @apply text-text-secondary leading-relaxed my-4 pl-6 list-decimal;
}
.prose :deep(li) {
  @apply my-2;
}
.prose :deep(strong) {
  @apply text-text-primary font-semibold;
}
.prose :deep(a) {
  @apply text-accent-blue hover:text-accent-purple underline underline-offset-2;
}
.prose :deep(blockquote) {
  @apply border-l-4 border-accent-purple/40 pl-4 my-4 text-text-secondary italic;
}
.prose :deep(code) {
  @apply bg-bg-card text-accent-green px-1.5 py-0.5 rounded text-sm font-mono;
}
.prose :deep(pre) {
  @apply bg-bg-card border border-white/5 rounded-card p-4 my-6 overflow-x-auto;
}
.prose :deep(pre code) {
  @apply bg-transparent p-0 text-text-primary;
}
.prose :deep(hr) {
  @apply border-white/10 my-8;
}
.prose :deep(table) {
  @apply w-full my-6 border-collapse;
}
.prose :deep(th) {
  @apply text-left text-text-primary font-semibold p-3 border-b border-white/10;
}
.prose :deep(td) {
  @apply text-text-secondary p-3 border-b border-white/5;
}
</style>
