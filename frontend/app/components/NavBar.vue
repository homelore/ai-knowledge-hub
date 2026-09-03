<template>
  <header class="fixed top-0 left-0 right-0 z-50 bg-bg-soft backdrop-blur-md border-b border-white/5">
    <div class="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
      <!-- Logo -->
      <NuxtLink to="/" class="flex items-center gap-2.5 group">
        <div class="w-9 h-9 rounded-xl bg-gradient-text flex items-center justify-center text-white font-bold text-sm shadow-glow">
          AI
        </div>
        <span class="text-text-primary font-semibold text-lg group-hover:gradient-text transition-all">
          Knowledge Hub
        </span>
      </NuxtLink>

      <!-- 导航链接 -->
      <nav class="hidden md:flex items-center gap-8">
        <NuxtLink to="/" class="text-text-secondary hover:text-text-primary text-sm font-medium transition-colors">
          首页
        </NuxtLink>
        <NuxtLink to="/repos" class="text-text-secondary hover:text-text-primary text-sm font-medium transition-colors">
          仓库动态
        </NuxtLink>
        <NuxtLink to="/topics/llm" class="text-text-secondary hover:text-text-primary text-sm font-medium transition-colors">
          主题分类
        </NuxtLink>
        <NuxtLink to="/articles/llm-explained" class="text-text-secondary hover:text-text-primary text-sm font-medium transition-colors">
          科普文章
        </NuxtLink>
        <NuxtLink to="/about" class="text-text-secondary hover:text-text-primary text-sm font-medium transition-colors">
          关于
        </NuxtLink>
      </nav>

      <!-- 右侧：本周编号 -->
      <div class="hidden sm:flex items-center gap-2">
        <span class="chip bg-accent-purple/10 text-accent-purple">
          <svg class="w-3.5 h-3.5 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"/>
          </svg>
          WEEK {{ currentWeek }}
        </span>
      </div>

      <!-- 移动端菜单按钮 -->
      <button class="md:hidden text-text-secondary p-2" @click="mobileMenuOpen = !mobileMenuOpen">
        <svg v-if="!mobileMenuOpen" class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16"/>
        </svg>
        <svg v-else class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
        </svg>
      </button>
    </div>

    <!-- 移动端菜单 -->
    <div v-if="mobileMenuOpen" class="md:hidden border-t border-white/5 bg-bg-soft backdrop-blur-md">
      <nav class="px-6 py-4 flex flex-col gap-3">
        <NuxtLink to="/" class="text-text-secondary hover:text-text-primary text-sm font-medium py-2 transition-colors" @click="mobileMenuOpen = false">
          首页
        </NuxtLink>
        <NuxtLink to="/repos" class="text-text-secondary hover:text-text-primary text-sm font-medium py-2 transition-colors" @click="mobileMenuOpen = false">
          仓库动态
        </NuxtLink>
        <NuxtLink to="/topics/llm" class="text-text-secondary hover:text-text-primary text-sm font-medium py-2 transition-colors" @click="mobileMenuOpen = false">
          主题分类
        </NuxtLink>
        <NuxtLink to="/articles/llm-explained" class="text-text-secondary hover:text-text-primary text-sm font-medium py-2 transition-colors" @click="mobileMenuOpen = false">
          科普文章
        </NuxtLink>
        <NuxtLink to="/about" class="text-text-secondary hover:text-text-primary text-sm font-medium py-2 transition-colors" @click="mobileMenuOpen = false">
          关于
        </NuxtLink>
      </nav>
    </div>
  </header>
</template>

<script setup lang="ts">
const mobileMenuOpen = ref(false)

// 计算当前 ISO 周
const currentWeek = computed(() => {
  const now = new Date()
  const start = new Date(now.getFullYear(), 0, 1)
  const diff = now.getTime() - start.getTime()
  const oneWeek = 1000 * 60 * 60 * 24 * 7
  return Math.ceil(diff / oneWeek).toString().padStart(2, '0')
})
</script>
