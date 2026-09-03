<template>
  <span
    class="chip"
    :style="{ backgroundColor: topicColor + '20', color: topicColor }"
  >
    <slot />
  </span>
</template>

<script setup lang="ts">
interface Props {
  name: string
  size?: 'sm' | 'md'
}

const props = withDefaults(defineProps<Props>(), {
  size: 'md'
})

const colorMap: Record<string, string> = {
  llm: '#a78bfa',
  rag: '#34d399',
  agent: '#60a5fa',
  transformer: '#fbbf24',
  diffusion: '#f472b6',
  mlops: '#c084fc'
}

const topicColor = computed(() => {
  return colorMap[props.name] || '#94a3b8'
})
</script>
