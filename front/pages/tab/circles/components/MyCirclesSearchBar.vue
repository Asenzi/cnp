<template>
  <view class="search-wrap">
    <view class="search-icon">
      <view class="search-ring"></view>
      <view class="search-tail"></view>
    </view>
    <input
      :value="modelValue"
      class="search-input"
      type="text"
      placeholder="搜索已加入的圈子"
      placeholder-class="search-placeholder"
      @input="onInput"
    />
  </view>
</template>

<script setup>
defineProps({
  modelValue: {
    type: String,
    default: ''
  }
})

const emit = defineEmits(['search'])

const onInput = (event) => {
  emit('search', event?.detail?.value || '')
}
</script>

<style scoped>
.search-wrap {
  position: relative;
}

.search-icon {
  position: absolute;
  left: 22rpx;
  top: 50%;
  transform: translateY(-50%);
  width: 24rpx;
  height: 24rpx;
  z-index: 2;
}

.search-ring {
  width: 14rpx;
  height: 14rpx;
  border: 2rpx solid #94a3b8;
  border-radius: 999rpx;
}

.search-tail {
  position: absolute;
  right: 0;
  bottom: 1rpx;
  width: 7rpx;
  height: 2rpx;
  border-radius: 999rpx;
  background: #94a3b8;
  transform: rotate(45deg);
}

.search-input {
  width: 100%;
  height: 80rpx;
  border-radius: 16rpx;
  background: #f1f5f9;
  border: 0;
  padding-left: 62rpx;
  padding-right: 24rpx;
  box-sizing: border-box;
  color: #0f172a;
  font-size: 26rpx;
}

.search-placeholder {
  color: #94a3b8;
}

@media (prefers-color-scheme: dark) {
  .search-input {
    background: #1e293b;
    color: #f8fafc;
  }

  .search-placeholder {
    color: #64748b;
  }

  .search-ring {
    border-color: #64748b;
  }

  .search-tail {
    background: #64748b;
  }
}
</style>
