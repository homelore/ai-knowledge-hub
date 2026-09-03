// https://nuxt.com/docs/api/configuration/nuxt-config
export default defineNuxtConfig({
  compatibilityDate: '2025-07-15',
  devtools: { enabled: true },
  modules: ['@nuxtjs/tailwindcss'],
  css: ['~/assets/css/main.css'],
  app: {
    head: {
      title: 'AI Knowledge Hub — 探索人工智能的世界',
      meta: [
        { name: 'description', content: 'AI 科普知识与 GitHub 每周技术动态' },
        { name: 'theme-color', content: '#0f172a' }
      ]
    }
  },
  tailwindcss: {
    configPath: 'tailwind.config.js'
  },
  // API 代理：前端 /api/* 请求转发到后端 FastAPI
  // routeRules 在 dev 和 production 都生效
  routeRules: {
    '/api/**': {
      proxy: 'http://localhost:8000/api/**',
    }
  },
  runtimeConfig: {
    public: {
      apiBase: ''  // 开发环境走 proxy，生产环境通过 NUXT_PUBLIC_API_BASE 设置
    }
  }
})
