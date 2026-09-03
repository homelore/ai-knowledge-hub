<template>
  <NuxtLink :to="`/articles/${article.slug}`" class="article-card block group">
    <div class="card p-5 h-full transition-all duration-300 hover:shadow-glowBlue hover:-translate-y-1 gradient-border">
      <!-- 顶部标签 -->
      <div class="flex items-center gap-2 mb-3">
        <span :class="['chip', difficultyColor(article.difficulty)]">
          {{ difficultyLabel(article.difficulty) }}
        </span>
        <span class="text-xs text-text-muted">{{ formatReadTime(article.read_time) }}</span>
      </div>

      <!-- 标题 -->
      <h3 class="text-text-primary font-semibold text-lg mb-2 group-hover:text-accent-blue transition-colors line-clamp-2">
        {{ article.title }}
      </h3>

      <!-- 摘要 -->
      <p class="text-text-secondary text-sm leading-relaxed line-clamp-3 mb-4">
        {{ article.summary }}
      </p>

      <!-- 底部：标签 -->
      <div class="flex flex-wrap gap-1.5 pt-3 border-t border-white/5">
        <TopicBadge v-for="tag in article.tags.slice(0, 3)" :key="tag" :name="tag">
          {{ topicName(tag) }}
        </TopicBadge>
      </div>
    </div>
  </NuxtLink>
</template>

<script setup lang="ts">
import TopicBadge from './TopicBadge.vue'

interface Article {
  slug: string
  title: string
  summary: string
  difficulty: string
  read_time: number
  tags: string[]
}

interface Props {
  article: Article
}

defineProps<Props>()

const { formatReadTime, difficultyLabel, difficultyColor } = useFormat()

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
.line-clamp-2 {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
.line-clamp-3 {
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
</style>
