<template>
  <view class="tabs-wrap">
    <view
      v-for="(item, index) in tabs"
      :key="item.key"
      class="tab-item"
      :class="{ 'tab-item-active': activeIndex === index }"
      @tap="emit('change', index)"
    >
      <text class="tab-text" :class="{ 'tab-text-active': activeIndex === index }">{{ item.label }}</text>
    </view>
  </view>
</template>

<script setup>
defineProps({
  tabs: {
    type: Array,
    default: () => []
  },
  activeIndex: {
    type: Number,
    default: 0
  }
})

const emit = defineEmits(['change'])
</script>

<style scoped>.tabs-wrap{display:flex;background:#fff;border-bottom:1rpx solid #e7eaf2;border-radius:24rpx 24rpx 0 0;margin-top:16rpx}.tab-item{flex:1;height:72rpx;display:flex;align-items:center;justify-content:center;border-bottom:3rpx solid transparent}.tab-item-active{border-color:#2160ff}.tab-text{font-size:30rpx;color:#757782}.tab-text-active{color:#111;font-weight:600}</style>