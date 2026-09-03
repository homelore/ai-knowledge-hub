<template>
  <div class="min-h-screen flex flex-col bg-bg">
    <NavBar />
    <main class="flex-1 pt-16">
      <NuxtPage />
    </main>

    <!-- Footer -->
    <footer class="border-t border-white/5 py-8 mt-16">
      <div class="max-w-7xl mx-auto px-6">
        <div class="flex flex-col md:flex-row items-center justify-between gap-4">
          <div class="flex items-center gap-2">
            <div class="w-7 h-7 rounded-lg bg-gradient-text flex items-center justify-center text-white font-bold text-xs">
              AI
            </div>
            <span class="text-text-secondary text-sm">AI Knowledge Hub</span>
          </div>
          <p class="text-text-muted text-xs">
            数据来源：GitHub API · 每周自动更新
          </p>
        </div>
      </div>
    </footer>
  </div>
</template>
