<template>
  <view class="header-wrap" :style="topStyle">
    <view class="search-wrap" :style="searchWrapStyle">
      <view class="search-bar" :style="searchBarStyle">
        <image class="search-icon" src="/static/icon/search.png" mode="aspectFit" />
        <input
          :value="modelValue"
          class="search-input"
          :style="searchBarStyle"
          type="text"
          :placeholder="searchPlaceholder"
          placeholder-class="search-placeholder"
          @input="onInput"
        />
      </view>
    </view>

    <view class="switch-wrap">
      <view class="switch-left">
        <view
          v-for="item in leftItems"
          :key="item.key"
          class="tab-item"
          :class="activeLeftKey === item.key ? 'tab-item-active' : ''"
          @tap="$emit('change-left', item.key)"
        >
          <text class="tab-text" :class="activeLeftKey === item.key ? 'tab-text-active' : ''">{{ item.label }}</text>
        </view>
      </view>

      <view class="switch-right">
        <button
          v-for="item in rightItems"
          :key="item.key"
          class="ctrl-btn"
          :class="isRightActive(item.key) ? 'ctrl-btn-active-filter' : ''"
          hover-class="ctrl-btn-active"
          @tap="$emit('tap-right', item.key)"
        >
          <text class="ctrl-text" :class="isRightActive(item.key) ? 'ctrl-text-active' : ''">{{ item.label }}</text>
          <view v-if="item.showArrow !== false" class="arrow" :class="isRightActive(item.key) ? 'arrow-active' : ''"></view>
          <view v-if="item.dot" class="dot"></view>
        </button>
      </view>
    </view>
  </view>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  modelValue: {
    type: String,
    default: ''
  },
  searchPlaceholder: {
    type: String,
    default: '搜索'
  },
  topPaddingPx: {
    type: Number,
    default: 0
  },
  rightInsetPx: {
    type: Number,
    default: 0
  },
  searchBarHeightPx: {
    type: Number,
    default: 44
  },
  leftItems: {
    type: Array,
    default: () => []
  },
  activeLeftKey: {
    type: String,
    default: ''
  },
  rightItems: {
    type: Array,
    default: () => []
  },
  activeRightKeys: {
    type: Array,
    default: () => []
  }
})

const emit = defineEmits(['update:modelValue', 'change-left', 'tap-right'])

const topStyle = computed(() => `padding-top:${Math.max(Number(props.topPaddingPx || 0), 0)}px;`)
const searchBarStyle = computed(() => `height:${Math.max(Number(props.searchBarHeightPx || 44), 34)}px;`)
const searchWrapStyle = computed(() => {
  const rightPaddingPx = 16 + Math.max(Number(props.rightInsetPx || 0), 0)
  return `padding:0 ${rightPaddingPx}px 8px 16px;`
})

const isRightActive = (key) => {
  return props.activeRightKeys.includes(key)
}

const onInput = (event) => {
  emit('update:modelValue', event?.detail?.value || '')
}
</script>

<style scoped>
.header-wrap {
  position: sticky;
  top: 0;
  z-index: 20;
  background: #ffffff;
  border-bottom: 1rpx solid #f1f5f9;
  padding-bottom: 10rpx;
}

.search-wrap {
  padding: 0 32rpx;
}

.search-bar {
  height: 88rpx;
  border-radius: 16rpx;
  background: #f1f5f9;
  display: flex;
  align-items: center;
}

.search-icon {
  width: 32rpx;
  height: 32rpx;
  margin-left: 24rpx;
  flex-shrink: 0;
}

.search-input {
  flex: 1;
  height: 88rpx;
  border: 0;
  background: transparent;
  padding: 0 20rpx 0 10rpx;
  color: #0f172a;
  font-size: 26rpx;
}

.search-placeholder {
  color: #94a3b8;
}

.switch-wrap {
  height: 84rpx;
  padding: 0 24rpx;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16rpx;
}

.switch-left {
  display: flex;
  align-items: center;
  gap: 24rpx;
  min-width: 0;
}

.tab-item {
  height: 84rpx;
  display: inline-flex;
  align-items: center;
}

.tab-text {
  color: #4b5563;
  font-size: 26rpx;
  line-height: 30rpx;
  font-weight: 500;
}

.tab-text-active {
  color: #111827;
  font-weight: 700;
}

.switch-right {
  display: flex;
  align-items: center;
  gap: 10rpx;
  flex-shrink: 0;
}

.ctrl-btn {
  height: 52rpx;
  min-width: 96rpx;
  padding: 0 12rpx;
  border: 0;
  border-radius: 10rpx;
  background: #f3f4f6;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6rpx;
  position: relative;
}

.ctrl-btn::after {
  border: 0;
}

.ctrl-btn-active {
  opacity: 0.82;
}

.ctrl-btn-active-filter {
  background: rgba(26, 87, 219, 0.12);
}

.ctrl-text {
  color: #374151;
  font-size: 22rpx;
  line-height: 26rpx;
  font-weight: 600;
}

.ctrl-text-active {
  color: #1a57db;
}

.arrow {
  width: 0;
  height: 0;
  border-left: 5rpx solid transparent;
  border-right: 5rpx solid transparent;
  border-top: 8rpx solid #c7ccd4;
  margin-top: 2rpx;
}

.arrow-active {
  border-top-color: #1a57db;
}

.dot {
  position: absolute;
  top: 10rpx;
  right: 8rpx;
  width: 10rpx;
  height: 10rpx;
  border-radius: 999rpx;
  background: #1a57db;
}

@media (prefers-color-scheme: dark) {
  .header-wrap {
    background: #111621;
    border-bottom-color: #1e293b;
  }

  .search-bar {
    background: #1e293b;
  }

  .search-input {
    color: #f8fafc;
  }

  .search-placeholder {
    color: #64748b;
  }

  .tab-text {
    color: #94a3b8;
  }

  .tab-text-active {
    color: #f8fafc;
  }

  .ctrl-btn {
    background: #1f2937;
  }

  .ctrl-btn-active-filter {
    background: rgba(59, 130, 246, 0.2);
  }

  .ctrl-text {
    color: #d1d5db;
  }

  .ctrl-text-active {
    color: #93c5fd;
  }

  .arrow {
    border-top-color: #6b7280;
  }

  .arrow-active {
    border-top-color: #93c5fd;
  }
}
</style>
