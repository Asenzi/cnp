<template>
  <view class="masonry-wrap">
    <view class="column">
      <DiscoverMasonryCard
        v-for="item in leftColumn"
        :key="item.id"
        :circle="item"
      />
    </view>

    <view class="column">
      <DiscoverMasonryCard
        v-for="item in rightColumn"
        :key="item.id"
        :circle="item"
      />
    </view>
  </view>
</template>

<script setup>
import { computed } from 'vue'
import DiscoverMasonryCard from './DiscoverMasonryCard.vue'

const props = defineProps({
  items: {
    type: Array,
    default: () => []
  }
})

const leftColumn = computed(() => props.items.filter((_, index) => index % 2 === 0))
const rightColumn = computed(() => props.items.filter((_, index) => index % 2 === 1))
</script>

<style scoped>
.masonry-wrap {
  padding: 0 24rpx 24rpx;
  display: flex;
  align-items: flex-start;
  gap: 14rpx;
}

.column {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 16rpx;
}
</style>
