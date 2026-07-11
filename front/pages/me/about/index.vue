<template>
  <view class="about-page">
    <view class="pattern-layer"></view>
    <view class="custom-nav" :style="navStyle">
      <view class="nav-inner">
        <view class="nav-back" hover-class="nav-back-active" @tap="goBack">
          <image class="nav-back-icon" src="https://cos.cnptec.site/static/me-icons/arrow-back-dark.png" mode="aspectFit" />
        </view>
        <text class="nav-title">关于我们</text>
        <view class="nav-capsule-space"></view>
      </view>
    </view>
    <scroll-view class="page-scroll" scroll-y :show-scrollbar="false">
      <view class="page-body" :style="pageBodyStyle">
        <view class="hero-section">
          <view class="brand-mark-wrap">
            <view class="brand-glow"></view>
            <view class="brand-mark">
              <view class="brand-mark-inner">
                <view class="node node-center"></view>
                <view class="node node-top"></view>
                <view class="node node-left"></view>
                <view class="node node-right"></view>
                <view class="node node-bottom-left"></view>
                <view class="node node-bottom-right"></view>
                <view class="link link-top"></view>
                <view class="link link-left"></view>
                <view class="link link-right"></view>
                <view class="link link-bottom-left"></view>
                <view class="link link-bottom-right"></view>
              </view>
            </view>
          </view>

          <text class="brand-name">QuanMaiLian</text>
          <text class="brand-subtitle">专业生态平台</text>
        </view>

        <view class="mission-card">
          <view class="mission-corner"></view>
          <view class="mission-title-row">
            <view class="mission-line"></view>
            <text class="mission-title">我们的愿景</text>
          </view>
          <text class="mission-copy">
            圈脉链（QuanMaiLian）是致力于连接高端商务网络与战略资源管理的顶尖专业生态平台。我们为现代精英阶层打造无缝对接的交互界面，助力用户通过经认证的渠道实现同步协作与影响力的规模化增长。
          </text>
        </view>

        <view class="info-list">
          <view
            v-for="item in infoItems"
            :key="item.key"
            class="info-card"
            hover-class="info-card-active"
            @tap="copyInfo(item)"
          >
            <view class="info-icon" :class="item.iconClass">
              <image class="info-icon-image" :src="item.iconPath" mode="aspectFit" />
            </view>
            <view class="info-copy">
              <text class="info-label">{{ item.label }}</text>
              <text class="info-value">{{ item.value }}</text>
            </view>
            <image class="chevron" src="https://cos.cnptec.site/static/me-icons/chevron-light.png" mode="aspectFit" />
          </view>
        </view>
      </view>
    </scroll-view>
  </view>
</template>

<script setup>
const { statusBarHeight = 0 } = uni.getSystemInfoSync()
const navHeight = 52
const navStyle = `padding-top:${statusBarHeight}px;`
const pageBodyStyle = `padding-top:${statusBarHeight + navHeight + 26}px;`

const infoItems = [
  {
    key: 'website',
    label: '官方网站',
    value: 'www.quanmailian.com',
    toast: '网址已复制',
    iconPath: 'https://cos.cnptec.site/static/me-icons/info-gray.png',
    iconClass: 'info-icon-blue'
  },
  {
    key: 'wechat',
    label: '官方微信',
    value: 'e1032405044',
    toast: '微信号已复制',
    iconPath: 'https://cos.cnptec.site/static/icon/chat.png',
    iconClass: 'info-icon-green'
  },
  {
    key: 'business',
    label: '商务合作',
    value: '19879931021@163.com',
    toast: '邮箱已复制',
    iconPath: 'https://cos.cnptec.site/static/me-icons/event-orange.png',
    iconClass: 'info-icon-orange'
  }
]

const copyInfo = (item) => {
  uni.setClipboardData({
    data: item.value,
    success: () => {
      uni.showToast({
        title: item.toast,
        icon: 'none'
      })
    }
  })
}

const goBack = () => {
  const pages = getCurrentPages()
  if (pages.length > 1) {
    uni.navigateBack()
    return
  }

  uni.switchTab({
    url: '/pages/tab/me/index'
  })
}

</script>

<style scoped>
.about-page {
  position: relative;
  min-height: 100vh;
  overflow: hidden;
  background:
    radial-gradient(circle at 0 0, rgba(191, 219, 254, 0.64), transparent 38%),
    radial-gradient(circle at 100% 4%, rgba(224, 242, 254, 0.78), transparent 42%),
    #f8fafc;
  color: #0f172a;
}

.pattern-layer {
  position: absolute;
  left: 0;
  right: 0;
  top: 0;
  bottom: 0;
  pointer-events: none;
  opacity: 0.38;
  background-image:
    linear-gradient(rgba(26, 87, 219, 0.08) 2rpx, transparent 2rpx),
    linear-gradient(90deg, rgba(26, 87, 219, 0.08) 2rpx, transparent 2rpx);
  background-size: 40rpx 40rpx;
}

.page-scroll {
  position: relative;
  z-index: 1;
  height: 100vh;
}

.custom-nav {
  position: fixed;
  z-index: 10;
  left: 0;
  right: 0;
  top: 0;
  background: rgba(248, 250, 252, 0.72);
  backdrop-filter: blur(18rpx);
}

.nav-inner {
  position: relative;
  height: 52px;
  padding: 0 32rpx;
  display: flex;
  align-items: center;
  justify-content: space-between;
  box-sizing: border-box;
}

.nav-back {
  width: 76rpx;
  height: 76rpx;
  border-radius: 999rpx;
  background: rgba(255, 255, 255, 0.72);
  box-shadow: 0 8rpx 22rpx rgba(15, 23, 42, 0.08);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.nav-back-active {
  opacity: 0.75;
  transform: scale(0.96);
}

.nav-back-icon {
  width: 36rpx;
  height: 36rpx;
}

.nav-title {
  position: absolute;
  left: 160rpx;
  right: 160rpx;
  text-align: center;
  color: #0f172a;
  font-size: 32rpx;
  font-weight: 800;
  line-height: 1;
}

.nav-capsule-space {
  width: 176rpx;
  height: 64rpx;
  flex-shrink: 0;
}

.page-body {
  padding: 42rpx 40rpx calc(56rpx + env(safe-area-inset-bottom));
  display: flex;
  flex-direction: column;
  gap: 42rpx;
  box-sizing: border-box;
}

.hero-section {
  padding: 34rpx 0 28rpx;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.brand-mark-wrap {
  position: relative;
  width: 184rpx;
  height: 184rpx;
  display: flex;
  align-items: center;
  justify-content: center;
}

.brand-glow {
  position: absolute;
  left: -28rpx;
  right: -28rpx;
  top: -28rpx;
  bottom: -28rpx;
  border-radius: 999rpx;
  background: rgba(26, 87, 219, 0.13);
  filter: blur(22rpx);
}

.brand-mark {
  position: relative;
  width: 152rpx;
  height: 152rpx;
  border-radius: 38rpx;
  background: linear-gradient(145deg, #2f6df0, #1a57db);
  box-shadow: 0 24rpx 46rpx rgba(26, 87, 219, 0.25);
  transform: rotate(-4deg);
  display: flex;
  align-items: center;
  justify-content: center;
}

.brand-mark-inner {
  position: relative;
  width: 102rpx;
  height: 102rpx;
  border-radius: 28rpx;
  border: 2rpx solid rgba(255, 255, 255, 0.28);
  background: rgba(255, 255, 255, 0.08);
  transform: rotate(4deg);
}

.node {
  position: absolute;
  z-index: 2;
  width: 18rpx;
  height: 18rpx;
  border-radius: 999rpx;
  background: #ffffff;
}

.node-center {
  left: 42rpx;
  top: 42rpx;
}

.node-top {
  left: 42rpx;
  top: 14rpx;
}

.node-left {
  left: 16rpx;
  top: 44rpx;
}

.node-right {
  right: 16rpx;
  top: 44rpx;
}

.node-bottom-left {
  left: 26rpx;
  bottom: 18rpx;
}

.node-bottom-right {
  right: 26rpx;
  bottom: 18rpx;
}

.link {
  position: absolute;
  z-index: 1;
  left: 49rpx;
  top: 49rpx;
  width: 4rpx;
  height: 34rpx;
  border-radius: 999rpx;
  background: rgba(255, 255, 255, 0.86);
  transform-origin: 2rpx 2rpx;
}

.link-top {
  transform: rotate(180deg);
}

.link-left {
  transform: rotate(265deg);
}

.link-right {
  transform: rotate(88deg);
}

.link-bottom-left {
  transform: rotate(215deg);
}

.link-bottom-right {
  transform: rotate(145deg);
}

.brand-name {
  margin-top: 36rpx;
  color: #0f172a;
  font-size: 50rpx;
  font-weight: 800;
  line-height: 1.1;
  letter-spacing: 0;
}

.brand-subtitle {
  margin-top: 12rpx;
  color: #64748b;
  font-size: 22rpx;
  font-weight: 700;
  letter-spacing: 8rpx;
}

.mission-card,
.info-card {
  background: rgba(255, 255, 255, 0.78);
  border: 1rpx solid rgba(255, 255, 255, 0.9);
  box-shadow: 0 22rpx 46rpx rgba(30, 64, 175, 0.06);
  backdrop-filter: blur(18rpx);
}

.mission-card {
  position: relative;
  overflow: hidden;
  border-radius: 32rpx;
  padding: 56rpx 52rpx;
}

.mission-corner {
  position: absolute;
  right: -58rpx;
  top: -58rpx;
  width: 180rpx;
  height: 180rpx;
  border-radius: 999rpx;
  background: rgba(26, 87, 219, 0.06);
}

.mission-title-row {
  position: relative;
  display: flex;
  align-items: center;
  gap: 20rpx;
  margin-bottom: 32rpx;
}

.mission-line {
  width: 58rpx;
  height: 4rpx;
  border-radius: 999rpx;
  background: #1a57db;
}

.mission-title {
  color: #1a57db;
  font-size: 22rpx;
  font-weight: 900;
  letter-spacing: 1rpx;
}

.mission-copy {
  position: relative;
  color: #334155;
  font-size: 28rpx;
  font-weight: 500;
  line-height: 1.85;
  text-align: justify;
}

.info-list {
  display: flex;
  flex-direction: column;
  gap: 28rpx;
}

.info-card {
  min-height: 136rpx;
  border-radius: 30rpx;
  padding: 0 28rpx;
  display: flex;
  align-items: center;
  gap: 28rpx;
  box-sizing: border-box;
  transition: transform 0.16s ease, opacity 0.16s ease;
}

.info-card-active {
  opacity: 0.78;
  transform: scale(0.99);
}

.info-icon {
  width: 86rpx;
  height: 86rpx;
  border-radius: 24rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.info-icon-blue {
  background: #eef4ff;
}

.info-icon-green {
  background: #ecfdf3;
}

.info-icon-orange {
  background: #fff7ed;
}

.info-icon-image {
  width: 42rpx;
  height: 42rpx;
}

.info-copy {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 10rpx;
}

.info-label {
  color: #94a3b8;
  font-size: 22rpx;
  font-weight: 800;
}

.info-value {
  color: #0f172a;
  font-size: 30rpx;
  font-weight: 800;
  line-height: 1.15;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.chevron {
  width: 32rpx;
  height: 32rpx;
  flex-shrink: 0;
}

@media (prefers-color-scheme: dark) {
  .about-page {
    background:
      radial-gradient(circle at 0 0, rgba(30, 64, 175, 0.34), transparent 36%),
      radial-gradient(circle at 100% 0, rgba(14, 165, 233, 0.18), transparent 40%),
      #101622;
    color: #f8fafc;
  }

  .pattern-layer {
    opacity: 0.14;
  }

  .custom-nav {
    background: rgba(16, 22, 34, 0.72);
  }

  .nav-back {
    background: rgba(15, 23, 42, 0.82);
    box-shadow: none;
  }

  .nav-title {
    color: #f8fafc;
  }

  .brand-name,
  .info-value {
    color: #f8fafc;
  }

  .brand-subtitle,
  .mission-copy {
    color: #cbd5e1;
  }

  .mission-card,
  .info-card {
    background: rgba(15, 23, 42, 0.78);
    border-color: rgba(51, 65, 85, 0.86);
    box-shadow: none;
  }

  .info-label {
    color: #94a3b8;
  }
}
</style>
