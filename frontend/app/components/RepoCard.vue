<template>
  <NuxtLink :to="`/repos/${repo.id}`" class="repo-card block group">
    <div class="card p-5 h-full transition-all duration-300 hover:shadow-glow hover:-translate-y-1 gradient-border">
      <!-- 头部：仓库名 + 语言 -->
      <div class="flex items-start justify-between gap-3 mb-3">
        <h3 class="text-text-primary font-semibold text-base group-hover:text-accent-blue transition-colors line-clamp-1">
          {{ repo.full_name }}
        </h3>
        <span v-if="repo.language" class="text-xs text-text-muted shrink-0">
          <span class="inline-block w-2 h-2 rounded-full mr-1.5 align-middle" :style="{ backgroundColor: langColor }"></span>
          {{ repo.language }}
        </span>
      </div>

      <!-- 描述 -->
      <p class="text-text-secondary text-sm leading-relaxed line-clamp-2 mb-4 min-h-[40px]">
        {{ repo.description }}
      </p>

      <!-- 主题标签 -->
      <div class="flex flex-wrap gap-1.5 mb-4">
        <TopicBadge v-for="topic in repo.topics.slice(0, 3)" :key="topic" :name="topic">
          {{ topicName(topic) }}
        </TopicBadge>
      </div>

      <!-- 底部：star + fork + 增长 -->
      <div class="flex items-center justify-between text-sm pt-3 border-t border-white/5">
        <div class="flex items-center gap-4">
          <span class="flex items-center gap-1.5 text-text-secondary">
            <svg class="w-4 h-4 text-accent-gold" fill="currentColor" viewBox="0 0 20 20">
              <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z"/>
            </svg>
            {{ formatNumber(repo.stars) }}
          </span>
          <span class="flex items-center gap-1.5 text-text-muted">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8.684 13.342C8.886 12.938 9 12.482 9 12c0-.482-.114-.938-.316-1.342m0 2.684a3 3 0 110-2.684m0 2.684l6.632 3.316m-6.632-6l6.632-3.316m0 0a3 3 0 105.367-2.684 3 3 0 00-5.367 2.684zm0 9.316a3 3 0 105.368 2.684 3 3 0 00-5.368-2.684z"/>
            </svg>
            {{ formatNumber(repo.forks) }}
          </span>
        </div>
        <span class="flex items-center gap-1 text-accent-green text-xs font-medium">
          <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 10l7-7m0 0l7 7m-7-7v18"/>
          </svg>
          +{{ formatNumber(repo.weekly_star_gain) }}
        </span>
      </div>
    </div>
  </NuxtLink>
</template>

<script setup lang="ts">
import TopicBadge from './TopicBadge.vue'

interface Repo {
  id: number
  full_name: string
  description: string
  stars: number
  forks: number
  language: string
  weekly_star_gain: number
  topics: string[]
}

interface Props {
  repo: Repo
}

const props = defineProps<Props>()

const { formatNumber } = useFormat()

const langColors: Record<string, string> = {
  Python: '#3572A5',
  TypeScript: '#3178c6',
  JavaScript: '#f1e05a',
  Go: '#00ADD8',
  Rust: '#dea584',
  Java: '#b07219'
}

const langColor = computed(() => {
  return langColors[props.repo.language] || '#64748b'
})

const topicNames: Record<string, string> = {
  llm: 'LLM',
  rag: 'RAG',
  agent: 'Agent',
  transformer: 'Transformer',
  diffusion: 'Diffusion',
  mlops: 'MLOps'
}

const topicName = (name: string) => topicNames[name] || name
</script>

<style scoped>
.line-clamp-1 {
  display: -webkit-box;
  -webkit-line-clamp: 1;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
.line-clamp-2 {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
</style>
