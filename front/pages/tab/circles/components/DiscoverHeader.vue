<template>
  <view class="header-wrap">
    <view class="brand-row">
      <text class="brand-title">圈脉链</text>
    </view>

    <view class="search-row">
      <view class="search-icon-wrap">
        <view class="search-icon">
          <view class="search-ring"></view>
          <view class="search-tail"></view>
        </view>
      </view>
      <input
        :value="keyword"
        class="search-input"
        type="text"
        placeholder="搜索全球商圈、顶尖人脉..."
        placeholder-class="search-placeholder"
        @input="onInput"
      />
    </view>

    <scroll-view class="filters-scroll hide-scrollbar" scroll-x enable-flex>
      <view class="filters-row">
        <view
          v-for="item in filters"
          :key="item"
          class="chip"
          hover-class="chip-active"
          @tap="emit('filter-tap', item)"
        >
          <text class="chip-text">{{ item }}</text>
          <image class="chip-arrow" mode="aspectFit" src="/static/me-icons/expand-more-slate.png" />
        </view>
      </view>
    </scroll-view>
  </view>
</template>

<script setup>
defineProps({
  keyword: {
    type: String,
    default: ''
  },
  filters: {
    type: Array,
    default: () => []
  }
})

const emit = defineEmits(['search', 'filter-tap'])

const onInput = (event) => {
  emit('search', event?.detail?.value || '')
}
</script>

<style scoped>
.header-wrap {
  position: sticky;
  top: 0;
  z-index: 20;
  background: rgba(255, 255, 255, 0.82);
  backdrop-filter: blur(12rpx);
  padding: 24rpx 32rpx 12rpx;
}

.brand-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding-right: 192rpx;
  margin-bottom: 16rpx;
}

.brand-title {
  color: #1a57db;
  font-size: 40rpx;
  line-height: 48rpx;
  font-weight: 700;
}

.search-row {
  position: relative;
}

.search-icon-wrap {
  position: absolute;
  left: 20rpx;
  top: 50%;
  transform: translateY(-50%);
  z-index: 2;
}

.search-icon {
  position: relative;
  width: 26rpx;
  height: 26rpx;
}

.search-ring {
  width: 16rpx;
  height: 16rpx;
  border: 2rpx solid #636e88;
  border-radius: 999rpx;
}

.search-tail {
  position: absolute;
  right: 1rpx;
  bottom: 2rpx;
  width: 8rpx;
  height: 2rpx;
  border-radius: 999rpx;
  background: #636e88;
  transform: rotate(45deg);
}

.search-input {
  width: 100%;
  height: 72rpx;
  border-radius: 20rpx;
  border: 0;
  background: #f1f5f9;
  color: #111318;
  font-size: 24rpx;
  padding-left: 66rpx;
  padding-right: 20rpx;
  box-sizing: border-box;
}

.search-placeholder {
  color: #636e88;
}

.filters-scroll {
  margin-top: 14rpx;
  white-space: nowrap;
}

.filters-row {
  display: inline-flex;
  gap: 12rpx;
  padding: 4rpx 0 6rpx;
}

.chip {
  display: inline-flex;
  align-items: center;
  gap: 6rpx;
  padding: 10rpx 22rpx;
  border-radius: 999rpx;
  border: 1rpx solid #e2e8f0;
  background: #ffffff;
  box-shadow: 0 2rpx 8rpx rgba(15, 23, 42, 0.08);
}

.chip-active {
  opacity: 0.82;
}

.chip-text {
  color: #111318;
  font-size: 24rpx;
  line-height: 32rpx;
  font-weight: 500;
}

.chip-arrow {
  width: 22rpx;
  height: 22rpx;
  opacity: 0.75;
}

.hide-scrollbar::-webkit-scrollbar {
  display: none;
}

@media (prefers-color-scheme: dark) {
  .header-wrap {
    background: rgba(17, 22, 33, 0.82);
  }

  .search-input {
    background: #1e293b;
    color: #f8fafc;
  }

  .search-placeholder {
    color: #94a3b8;
  }

  .search-ring {
    border-color: #94a3b8;
  }

  .search-tail {
    background: #94a3b8;
  }

  .chip {
    background: #1e293b;
    border-color: #334155;
    box-shadow: none;
  }

  .chip-text {
    color: #f8fafc;
  }
}
</style>
