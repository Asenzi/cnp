<template>
  <view class="filter-empty-page"></view>
</template>

<script setup>
import { onLoad } from '@dcloudio/uni-app'

onLoad((query) => {
  if (!query?.name) {
    return
  }

  uni.setNavigationBarTitle({
    title: decodeURIComponent(query.name)
  })
})
</script>

<style scoped>
.filter-empty-page {
  min-height: 100vh;
  background: #f6f6f8;
}

@media (prefers-color-scheme: dark) {
  .filter-empty-page {
    background: #111621;
  }
}
</style>
