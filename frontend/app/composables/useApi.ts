// API 封装 — 连接后端 FastAPI
// 开发环境通过 Nuxt devProxy 转发到 http://localhost:8000

interface Repo {
  id: number
  github_id: number
  full_name: string
  name: string
  description: string
  url: string
  stars: number
  forks: number
  language: string
  license: string
  weekly_star_gain: number
  topics: string[]
  github_updated_at: string
  releases?: any[]
}

interface Topic {
  name: string
  display_name: string
  description: string
  color: string
  icon: string
  sort_order: number
  repo_count: number
}

interface Article {
  id: number
  slug: string
  title: string
  summary: string
  difficulty: string
  read_time: number
  tags: string[]
  published: boolean
  created_at: string
  content?: string
  related?: Article[]
}

interface Release {
  id: number
  repo_id: number
  tag_name: string
  release_name: string
  body: string
  url: string
  is_prerelease: boolean
  published_at: string
}

interface StarHistoryItem {
  week: string
  stars: number
}

interface FetchReposParams {
  page?: number
  limit?: number
  topic?: string
  language?: string
  sort?: 'stars' | 'weekly_gain' | 'updated'
}

interface FetchReposResult {
  items: Repo[]
  total: number
  page: number
  has_more: boolean
}

// 延迟导入 marked，避免 SSR 报错
let markedFn: ((text: string) => string) | null = null
async function getMarked() {
  if (!markedFn) {
    const { marked } = await import('marked')
    markedFn = marked
  }
  return markedFn
}

export function useApi() {
  // 获取仓库列表
  const fetchRepos = async (params: FetchReposParams = {}): Promise<FetchReposResult> => {
    const query: Record<string, any> = {
      page: params.page || 1,
      page_size: params.limit || 12,
    }
    if (params.topic) query.topic = params.topic
    if (params.language) query.language = params.language
    if (params.sort) query.sort = params.sort

    const data = await $fetch<any>('/api/repos', { query })
    const limit = params.limit || 12
    const page = params.page || 1
    return {
      items: data.items || [],
      total: data.total || 0,
      page,
      has_more: page * limit < (data.total || 0),
    }
  }

  // 获取仓库详情
  const fetchRepo = async (id: number): Promise<Repo | null> => {
    try {
      const data = await $fetch<any>(`/api/repos/${id}`)
      return data
    } catch {
      return null
    }
  }

  // 获取仓库 Release
  const fetchRepoReleases = async (repoId: number, _limit = 5): Promise<Release[]> => {
    try {
      const data = await $fetch<any>(`/api/repos/${repoId}/releases`)
      return Array.isArray(data) ? data : []
    } catch {
      return []
    }
  }

  // 获取 Star 历史
  const fetchRepoStarHistory = async (repoId: number): Promise<StarHistoryItem[]> => {
    try {
      const data = await $fetch<any>(`/api/repos/${repoId}/star-history`)
      return Array.isArray(data) ? data : []
    } catch {
      return []
    }
  }

  // 获取所有主题
  const fetchTopics = async (): Promise<Topic[]> => {
    try {
      const data = await $fetch<any>('/api/topics')
      return Array.isArray(data) ? data : []
    } catch {
      return []
    }
  }

  // 获取单个主题
  const fetchTopic = async (name: string): Promise<Topic | null> => {
    try {
      const data = await $fetch<any>(`/api/topics/${name}`)
      return data
    } catch {
      return null
    }
  }

  // 获取主题下的仓库
  const fetchTopicRepos = async (topicName: string): Promise<Repo[]> => {
    try {
      const data = await $fetch<any>(`/api/topics/${topicName}/repos`, {
        query: { page: 1, page_size: 50 }
      })
      return data.items || []
    } catch {
      return []
    }
  }

  // 获取文章列表
  const fetchArticles = async (params: { difficulty?: string; tag?: string; limit?: number } = {}): Promise<Article[]> => {
    const query: Record<string, any> = {
      page: 1,
      page_size: params.limit || 20,
    }
    if (params.difficulty) query.difficulty = params.difficulty
    if (params.tag) query.topic = params.tag

    try {
      const data = await $fetch<any>('/api/articles', { query })
      return data.items || []
    } catch {
      return []
    }
  }

  // 获取文章详情（含渲染后的 HTML 正文 + 相关文章）
  const fetchArticle = async (slug: string): Promise<Article | null> => {
    try {
      const data = await $fetch<any>(`/api/articles/${slug}`)
      return data
    } catch {
      return null
    }
  }

  // 获取相关文章（已包含在文章详情响应中，此函数做兼容处理）
  const fetchRelatedArticles = async (slug: string, _limit = 3): Promise<Article[]> => {
    try {
      const data = await $fetch<any>(`/api/articles/${slug}`)
      return data.related || []
    } catch {
      return []
    }
  }

  // 获取统计数据
  const fetchStats = async () => {
    try {
      const data = await $fetch<any>('/api/stats/summary')
      return {
        total_repos: data.total_repos || 0,
        total_articles: data.total_articles || 0,
        total_topics: data.total_topics || 0,
        last_fetch_time: data.last_fetch_time || null,
        last_fetch_week: data.last_fetch_week || null,
        weekly_new_repos: data.weekly_new_repos || 0,
      }
    } catch {
      return {
        total_repos: 0,
        total_articles: 0,
        total_topics: 0,
        last_fetch_time: null,
        last_fetch_week: null,
        weekly_new_repos: 0,
      }
    }
  }

  // 获取最近拉取日志
  const fetchLastFetchLog = async () => {
    try {
      const data = await $fetch<any>('/api/stats/last-fetch')
      return data || null
    } catch {
      return null
    }
  }

  return {
    fetchRepos,
    fetchRepo,
    fetchRepoReleases,
    fetchRepoStarHistory,
    fetchTopics,
    fetchTopic,
    fetchTopicRepos,
    fetchArticles,
    fetchArticle,
    fetchRelatedArticles,
    fetchStats,
    fetchLastFetchLog
  }
}
