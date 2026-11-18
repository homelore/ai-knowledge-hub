<template>
  <div class="max-w-6xl mx-auto px-6 py-14">
    <!-- 页头 -->
    <header class="text-center mb-10">
      <h1 class="text-3xl md:text-4xl font-bold mb-3">
        <span class="gradient-text">帮我挑一个能跑起来的项目</span>
      </h1>
      <p class="text-text-secondary text-sm md:text-base">
        三个问题，给你 5 个真正适合你现在水平的 GitHub 项目
      </p>
    </header>

    <!-- 未开始 -->
    <div v-if="stage === 'idle'" class="card p-10 text-center max-w-xl mx-auto">
      <p class="text-text-secondary mb-6 leading-relaxed">
        不用注册、不用登录。回答三个问题，我们按你的方向、水平和偏好排序，
        并告诉你每个项目<span class="text-accent-blue">第一步该做什么</span>。
      </p>
      <button
        class="px-7 py-3 bg-gradient-text text-white font-medium rounded-lg shadow-glow hover:shadow-glowBlue transition-all hover:-translate-y-0.5 disabled:opacity-60"
        :disabled="loading"
        @click="start"
      >
        {{ loading ? '准备中…' : '开始推荐' }}
      </button>
    </div>

    <!-- 提问 -->
    <div v-else-if="stage === 'question' && question" class="max-w-2xl mx-auto">
      <div class="card p-6 md:p-8">
        <div class="flex items-center justify-between mb-5">
          <span class="text-xs text-text-muted">
            第 {{ answeredCount + 1 }} 步 / 共 3 步
          </span>
          <span class="chip text-xs">引擎：{{ engine === 'llm' ? 'LLM' : '规则' }}</span>
        </div>

        <h2 class="text-text-primary text-lg font-semibold mb-5">
          {{ question.text }}
        </h2>

        <div class="grid gap-3" :class="question.type === 'multi' ? 'sm:grid-cols-2' : ''">
          <button
            v-for="option in question.options"
            :key="option.value"
            class="text-left p-4 rounded-xl border transition-all duration-200"
            :class="isSelected(option.value)
              ? 'border-accent-blue bg-white/5'
              : 'border-white/10 hover:border-white/25 hover:bg-white/5'"
            @click="toggleOption(option.value)"
          >
            <div class="text-text-primary text-sm font-medium">{{ option.label }}</div>
            <div v-if="option.description" class="text-text-muted text-xs mt-1 leading-relaxed">
              {{ option.description }}
            </div>
          </button>
        </div>

        <div v-if="question.type === 'multi'" class="mt-6 flex items-center justify-between">
          <span class="text-xs text-text-muted">可多选，至少选 1 个</span>
          <button
            class="px-6 py-2.5 bg-gradient-text text-white text-sm font-medium rounded-lg disabled:opacity-40"
            :disabled="selected.length === 0 || loading"
            @click="confirmMulti"
          >
            {{ loading ? '推荐中…' : '下一步' }}
          </button>
        </div>

        <p class="text-text-muted text-xs mt-4">
          也可以直接打字告诉我，例如「我是刚入门的学生，想做 RAG 项目」
        </p>
      </div>

      <p v-if="error" class="text-accent-red text-sm text-center mt-4">{{ error }}</p>
    </div>

    <!-- 结果 -->
    <div v-else-if="stage === 'result'">
      <div class="flex flex-wrap items-center justify-between gap-4 mb-6">
        <div class="text-sm text-text-secondary">
          为你精选 {{ results.length }} 个项目
          <span class="text-text-muted ml-2">
            （引擎：{{ engine === 'llm' ? 'LLM 精排' : '规则排序' }}）
          </span>
        </div>
        <div class="flex items-center gap-3">
          <button
            class="px-4 py-2 text-sm rounded-lg border border-white/10 hover:border-white/30 transition-colors disabled:opacity-50"
            :disabled="loading"
            @click="refresh"
          >
            换一批
          </button>
          <button
            class="px-4 py-2 text-sm rounded-lg text-text-secondary hover:text-text-primary transition-colors"
            @click="reset"
          >
            重新开始
          </button>
        </div>
      </div>

      <div class="grid gap-5 md:grid-cols-2">
        <article
          v-for="item in results"
          :key="item.repo_id"
          class="card p-5 gradient-border transition-all duration-300 hover:shadow-glow"
        >
          <div class="flex items-start justify-between gap-3 mb-2">
            <a
              :href="item.url || `/repos/${item.repo_id}`"
              :target="item.url ? '_blank' : '_self'"
              rel="noopener"
              class="text-text-primary font-semibold hover:text-accent-blue transition-colors line-clamp-1"
              @click="clickRepo(item)"
            >
              {{ item.full_name }}
            </a>
            <span class="text-xs text-accent-gold shrink-0">★ {{ formatNumber(item.stars) }}</span>
          </div>

          <p class="text-text-secondary text-sm leading-relaxed line-clamp-2 mb-3">
            {{ item.description }}
          </p>

          <!-- 推荐理由 -->
          <div class="rounded-lg bg-white/5 p-3 mb-3">
            <div class="text-xs text-accent-blue mb-1">为什么推荐你</div>
            <p class="text-text-secondary text-sm leading-relaxed">{{ item.reason }}</p>
          </div>

          <!-- 第一步 -->
          <div class="text-sm mb-3">
            <span class="text-xs text-accent-green mr-1.5">第一步</span>
            <span class="text-text-secondary">{{ item.first_step }}</span>
          </div>

          <div class="flex flex-wrap gap-1.5 mb-4">
            <TopicBadge v-for="topic in item.topics.slice(0, 3)" :key="topic" :name="topic">
              {{ topic }}
            </TopicBadge>
          </div>

          <!-- 关联文章 -->
          <div v-if="item.related_articles?.length" class="border-t border-white/5 pt-3 mb-3">
            <div class="text-xs text-text-muted mb-1.5">先补概念</div>
            <NuxtLink
              v-for="article in item.related_articles"
              :key="article.slug"
              :to="`/articles/${article.slug}`"
              class="block text-xs text-text-secondary hover:text-accent-blue transition-colors line-clamp-1"
            >
              · {{ article.title }}
            </NuxtLink>
          </div>

          <div class="flex items-center justify-between pt-3 border-t border-white/5">
            <NuxtLink
              :to="`/repos/${item.repo_id}`"
              class="text-sm text-accent-blue hover:underline"
              @click="clickRepo(item)"
            >
              查看详情 →
            </NuxtLink>
            <button
              class="text-xs text-text-muted hover:text-accent-red transition-colors"
              @click="skip(item.repo_id)"
            >
              不感兴趣
            </button>
          </div>
        </article>
      </div>
    </div>

    <p v-if="error && stage !== 'question'" class="text-accent-red text-sm text-center mt-6">
      {{ error }}
    </p>
  </div>
</template>

<script setup lang="ts">
import TopicBadge from '~/components/TopicBadge.vue'

useHead({ title: '项目推荐 · AI Knowledge Hub' })

const {
  stage, question, results, engine, loading, error,
  start, answer, refresh, skip, clickRepo, reset,
} = useRecommend()

const selected = ref<string[]>([])
const answeredCount = ref(0)

const isSelected = (value: string) => selected.value.includes(value)

const toggleOption = (value: string) => {
  if (question.value?.type === 'multi') {
    selected.value = isSelected(value)
      ? selected.value.filter((v) => v !== value)
      : [...selected.value, value]
    return
  }
  // 单选：直接提交
  submit(value)
}

const confirmMulti = () => {
  if (!selected.value.length || !question.value) return
  submit(selected.value)
}

const submit = async (value: string | string[]) => {
  if (!question.value) return
  const id = question.value.id
  selected.value = []
  answeredCount.value += 1
  await answer(id, value)
}

const formatNumber = (value: number) => {
  if (!value) return '0'
  return value >= 1000 ? `${(value / 1000).toFixed(1)}k` : String(value)
}
</script>
