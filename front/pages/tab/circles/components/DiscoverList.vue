<template>
  <view class="list-wrap">
    <CircleDirectoryCard
      v-for="item in items"
      :key="item.id"
      :circle="item"
      @interest="$emit('interest', $event)"
    />
  </view>
</template>

<script setup>
import CircleDirectoryCard from './CircleDirectoryCard.vue'

defineProps({
  items: {
    type: Array,
    default: () => []
  }
})

defineEmits(['interest'])
</script>

<style scoped>
.list-wrap {
  padding: 18rpx 24rpx 24rpx;
  background: #f6f6f8;
  display: flex;
  flex-direction: column;
  gap: 18rpx;
}
</style>
