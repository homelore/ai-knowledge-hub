// 格式化工具
export function useFormat() {
  const formatNumber = (num: number): string => {
    if (num >= 1000000) {
      return (num / 1000000).toFixed(1) + 'M'
    }
    if (num >= 1000) {
      return (num / 1000).toFixed(1) + 'k'
    }
    return num.toString()
  }

  const formatDate = (dateStr: string): string => {
    const date = new Date(dateStr)
    const now = new Date()
    const diffMs = now.getTime() - date.getTime()
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24))

    if (diffDays === 0) return '今天'
    if (diffDays === 1) return '昨天'
    if (diffDays < 7) return `${diffDays} 天前`
    if (diffDays < 30) return `${Math.floor(diffDays / 7)} 周前`
    if (diffDays < 365) return `${Math.floor(diffDays / 30)} 个月前`
    return `${Math.floor(diffDays / 365)} 年前`
  }

  const formatDateFull = (dateStr: string): string => {
    const date = new Date(dateStr)
    return date.toLocaleDateString('zh-CN', {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    })
  }

  const formatReadTime = (minutes: number): string => {
    if (minutes < 1) return '不到 1 分钟'
    return `${minutes} 分钟阅读`
  }

  const difficultyLabel = (level: string): string => {
    const map: Record<string, string> = {
      beginner: '入门',
      intermediate: '进阶',
      advanced: '高级'
    }
    return map[level] || level
  }

  const difficultyColor = (level: string): string => {
    const map: Record<string, string> = {
      beginner: 'bg-accent-green/20 text-accent-green',
      intermediate: 'bg-accent-blue/20 text-accent-blue',
      advanced: 'bg-accent-purple/20 text-accent-purple'
    }
    return map[level] || 'bg-text-muted/20 text-text-muted'
  }

  return {
    formatNumber,
    formatDate,
    formatDateFull,
    formatReadTime,
    difficultyLabel,
    difficultyColor
  }
}
