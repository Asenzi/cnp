<template>
  <view class="list-wrap">
    <DiscoverListCard
      v-for="item in items"
      :key="item.id"
      :circle="item"
    />
  </view>
</template>

<script setup>
import DiscoverListCard from './DiscoverListCard.vue'

defineProps({
  items: {
    type: Array,
    default: () => []
  }
})
</script>

<style scoped>
.list-wrap {
  padding: 0 32rpx 24rpx;
  display: flex;
  flex-direction: column;
  gap: 18rpx;
}
</style>
