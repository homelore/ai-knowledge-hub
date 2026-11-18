// 推荐接口封装 — 对话式三轮 + 结果操作 + 埋点
// 与后端 /api/recommend/* 一一对应

export interface RecommendOption {
  value: string
  label: string
  description?: string
}

export interface RecommendQuestion {
  id: 'topics' | 'level' | 'preference'
  type: 'single' | 'multi'
  text: string
  options: RecommendOption[]
}

export interface RecommendItem {
  repo_id: number
  full_name: string
  description: string
  url: string
  stars: number
  language: string
  topics: string[]
  reason: string
  first_step: string
  difficulty: string
  related_articles: { slug: string; title: string }[]
}

export function useRecommend() {
  const sessionId = ref<string | null>(null)
  const stage = ref<'idle' | 'question' | 'result'>('idle')
  const question = ref<RecommendQuestion | null>(null)
  const results = ref<RecommendItem[]>([])
  const engine = ref<string>('rule')
  const loading = ref(false)
  const error = ref<string | null>(null)

  // 埋点：失败静默，不影响主流程
  const track = (event: string, payload: Record<string, any> = {}) => {
    $fetch('/api/recommend/event', {
      method: 'POST',
      body: { session_id: sessionId.value, event, payload },
    }).catch(() => {})
  }

  const applyResponse = (data: any) => {
    sessionId.value = data.session_id || sessionId.value
    engine.value = data.engine || 'rule'
    if (data.stage === 'question') {
      stage.value = 'question'
      question.value = data.question
      results.value = []
    } else {
      stage.value = 'result'
      question.value = null
      results.value = data.recommendations || []
      track('result_viewed', {
        count: results.value.length,
        engine: engine.value,
      })
    }
  }

  const post = async (url: string, body: Record<string, any>) => {
    loading.value = true
    error.value = null
    try {
      const data = await $fetch<any>(url, { method: 'POST', body })
      applyResponse(data)
      return data
    } catch (e: any) {
      error.value = e?.message || '请求失败，请稍后重试'
      return null
    } finally {
      loading.value = false
    }
  }

  // 开始对话
  const start = async () => {
    if (sessionId.value) return
    track('recommend_started')
    await post('/api/recommend/chat', {})
  }

  // 回答当前问题（单选用 value，多选用 values）
  const answer = async (questionId: string, value: string | string[]) => {
    track('question_answered', { question_id: questionId, value })
    await post('/api/recommend/chat', {
      session_id: sessionId.value,
      answers: { [questionId]: value },
    })
  }

  // 换一批：把当前结果排掉
  const refresh = async () => {
    if (!sessionId.value) return
    track('result_refreshed', {
      repo_ids: results.value.map((r) => r.repo_id),
    })
    await post('/api/recommend/action', {
      session_id: sessionId.value,
      action: 'refresh',
      repo_ids: results.value.map((r) => r.repo_id),
    })
  }

  // 不感兴趣：同会话内不再出现
  const skip = async (repoId: number) => {
    if (!sessionId.value) return
    track('result_skipped', { repo_id: repoId })
    await post('/api/recommend/action', {
      session_id: sessionId.value,
      action: 'skip',
      repo_id: repoId,
    })
  }

  // 点击进入仓库详情
  const clickRepo = (item: RecommendItem) => {
    track('result_clicked', {
      repo_id: item.repo_id,
      full_name: item.full_name,
    })
  }

  const reset = () => {
    sessionId.value = null
    stage.value = 'idle'
    question.value = null
    results.value = []
    track('recommend_reset')
  }

  return {
    sessionId,
    stage,
    question,
    results,
    engine,
    loading,
    error,
    start,
    answer,
    refresh,
    skip,
    clickRepo,
    reset,
  }
}
