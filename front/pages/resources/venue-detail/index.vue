<template>
  <view class="venue-detail-page">
    <!-- 空白页面，等待设计 -->
  </view>
</template>

<script setup>
import { ref } from 'vue'
import { onLoad } from '@dcloudio/uni-app'

const postCode = ref('')

onLoad((query = {}) => {
  postCode.value = String(query?.postCode || '').trim()
})
</script>

<style scoped>
.venue-detail-page {
  min-height: 100vh;
  background: #f6f6f8;
}
</style>
