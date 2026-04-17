<template>
  <web-view v-if="src" :src="src" />
</template>

<script setup>
import { ref } from 'vue'
import { onLoad } from '@dcloudio/uni-app'

const src = ref('')

onLoad((query) => {
  const title = decodeURIComponent(String(query?.title || '网页详情'))
  const url = decodeURIComponent(String(query?.url || ''))
  src.value = url
  if (title) {
    uni.setNavigationBarTitle({
      title
    })
  }
})
</script>
