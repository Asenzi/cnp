<template>
  <view class="edit-page">
    <view class="page-shell">
      <view class="top-nav" :style="navStyle">
        <view class="back-btn" hover-class="back-btn-hover" @tap="goBack">
          <image class="back-icon" mode="aspectFit" src="/static/me-icons/arrow-back-dark.png" />
        </view>
        <text class="nav-title">编辑个人资料</text>
        <view class="nav-placeholder"></view>
      </view>

      <view class="avatar-section">
        <view class="avatar-stack" hover-class="avatar-stack-hover" @tap="onChangeAvatar">
          <view class="avatar-wrap">
            <image
              class="avatar"
              mode="aspectFill"
              src="https://lh3.googleusercontent.com/aida-public/AB6AXuBv9YKCNjpwt1WC_48xYSN3N4YEpDhhyvw_aVkDmEWdVG7lGGTHR1QGrn657-jukxQE2Z7YC6iOe9d8bRKAiZQm6OdW-TZrSdkZjw9sqB4MzYzWw5yFBmMJ3UfXoL4wg5HvBfdlSFLO0joC5ss07Py9JOKQTsOem00Dow4VYev6AnZInfJZWKr2eOz_F9HEZ343esMbKqzGP4XaZrvXQxUtB5hqyFOxqyeijBkF3uuZuWTP4COt2DkHeHMgjJypLHSfdNppuBokLl3o"
            />
            <view class="camera-badge">
              <image class="camera-icon" mode="aspectFit" src="/static/me-icons/camera-white.png" />
            </view>
          </view>
          <text class="avatar-tip">点击更换头像</text>
        </view>
      </view>

      <view class="form-wrap">
        <view class="field-group">
          <text class="field-label">昵称</text>
          <input v-model="nickname" class="field-input" placeholder="请输入您的昵称" placeholder-class="field-placeholder" />
        </view>

        <view class="field-group">
          <text class="field-label">行业与职位</text>
          <view class="picker-wrap">
            <picker
              class="picker-control"
              mode="selector"
              :range="industryOptions"
              range-key="label"
              :value="industryIndex"
              @change="onIndustryChange"
            >
              <view class="picker-text">{{ industryOptions[industryIndex].label }}</view>
            </picker>
            <image class="expand-icon" mode="aspectFit" src="/static/me-icons/expand-more-slate.png" />
          </view>
        </view>

        <view class="field-group">
          <text class="field-label">个人简介</text>
          <textarea
            v-model="bio"
            class="field-textarea"
            placeholder="描述您的专业背景、成就或合作需求..."
            placeholder-class="field-placeholder"
            maxlength="-1"
          />
        </view>

        <view class="field-group">
          <text class="field-label">名片附件</text>

          <view class="upload-area" hover-class="upload-area-hover" @tap="onUploadCard">
            <view class="upload-inner">
              <image class="upload-icon" mode="aspectFit" src="/static/me-icons/upload-primary.png" />
              <text class="upload-text">点击或拖拽上传名片 (JPG, PNG, PDF)</text>
            </view>
          </view>

          <view class="file-list">
            <view v-for="(file, index) in attachedFiles" :key="file.name" class="file-item">
              <view class="file-left">
                <image class="file-type-icon" mode="aspectFit" src="/static/me-icons/image-primary.png" />
                <view class="file-meta">
                  <text class="file-name">{{ file.name }}</text>
                  <text class="file-size">{{ file.size }}</text>
                </view>
              </view>
              <view class="file-remove" hover-class="file-remove-hover" @tap="removeFile(index)">
                <image class="cancel-icon" mode="aspectFit" src="/static/me-icons/cancel-slate.png" />
              </view>
            </view>
          </view>
        </view>

        <view class="toggle-card">
          <view class="toggle-copy">
            <text class="toggle-title">展示联系方式</text>
            <text class="toggle-desc">允许经过认证的用户查看您的手机号</text>
          </view>
          <view class="switch-wrap" @tap="toggleShowContact">
            <view class="switch-track" :class="{ 'switch-track-on': showContact }"></view>
            <view class="switch-thumb" :class="{ 'switch-thumb-on': showContact }"></view>
          </view>
        </view>

        <view class="save-wrap">
          <view class="save-btn" hover-class="save-btn-hover" @tap="onSave">
            <text class="save-text">保存修改</text>
          </view>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup>
import { ref } from 'vue'

const { statusBarHeight = 0 } = uni.getSystemInfoSync()
const navStyle = `padding-top:${statusBarHeight}px;`

const nickname = ref('张建国')
const bio = ref(
  '拥有10年互联网大厂项目管理经验，专注于B2B数字化转型。目前正在寻找供应链领域的合作伙伴。诚挚欢迎各行业精英交流合作。'
)

const showContact = ref(true)

const industryOptions = [
  { value: 'tech', label: '互联网 / 软件工程师' },
  { value: 'finance', label: '金融服务 / 投资分析师' },
  { value: 'marketing', label: '市场营销 / 品牌经理' },
  { value: 'manufacturing', label: '智能制造 / 项目经理' }
]
const industryIndex = ref(0)

const attachedFiles = ref([{ name: '个人名片_正面.jpg', size: '1.2 MB' }])

const goBack = () => {
  if (getCurrentPages().length > 1) {
    uni.navigateBack()
    return
  }

  uni.switchTab({
    url: '/pages/tab/me/index'
  })
}

const onChangeAvatar = () => {}

const onIndustryChange = (event) => {
  industryIndex.value = Number(event.detail.value || 0)
}

const onUploadCard = () => {}

const removeFile = (index) => {
  attachedFiles.value.splice(index, 1)
}

const toggleShowContact = () => {
  showContact.value = !showContact.value
}

const onSave = () => {}
</script>

<style scoped>
.edit-page {
  min-height: 100vh;
  background: #f6f6f8;
}

.page-shell {
  min-height: 100vh;
  max-width: 750rpx;
  margin: 0 auto;
  background: #ffffff;
  box-shadow: 0 8rpx 28rpx rgba(15, 23, 42, 0.08);
}

.top-nav {
  position: sticky;
  top: 0;
  z-index: 10;
  display: flex;
  align-items: center;
  gap: 16rpx;
  padding-left: 32rpx;
  padding-right: 32rpx;
  border-bottom: 1rpx solid #f1f5f9;
  background: #ffffff;
}

.back-btn {
  width: 80rpx;
  height: 80rpx;
  border-radius: 999rpx;
  display: flex;
  align-items: center;
  justify-content: center;
}

.back-btn-hover {
  background: #f1f5f9;
}

.back-icon {
  width: 44rpx;
  height: 44rpx;
}

.nav-title {
  flex: 1;
  height: 88rpx;
  line-height: 88rpx;
  text-align: center;
  font-size: 34rpx;
  font-weight: 700;
  color: #0f172a;
}

.nav-placeholder {
  width: 80rpx;
  height: 80rpx;
}

.avatar-section {
  padding: 64rpx;
  padding-bottom: 48rpx;
}

.avatar-stack {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16rpx;
}

.avatar-wrap {
  position: relative;
}

.avatar {
  width: 224rpx;
  height: 224rpx;
  border-radius: 999rpx;
  border: 8rpx solid #f8fafc;
  box-shadow: 0 10rpx 24rpx rgba(15, 23, 42, 0.12);
}

.camera-badge {
  position: absolute;
  right: 0;
  bottom: 0;
  width: 64rpx;
  height: 64rpx;
  border-radius: 999rpx;
  border: 4rpx solid #ffffff;
  background: #1a57db;
  display: flex;
  align-items: center;
  justify-content: center;
}

.camera-icon {
  width: 30rpx;
  height: 30rpx;
}

.avatar-tip {
  font-size: 26rpx;
  color: #64748b;
  font-weight: 500;
}

.form-wrap {
  display: flex;
  flex-direction: column;
  gap: 48rpx;
  padding-left: 32rpx;
  padding-right: 32rpx;
  padding-bottom: calc(96rpx + env(safe-area-inset-bottom));
}

.field-group {
  display: flex;
  flex-direction: column;
  gap: 16rpx;
}

.field-label {
  margin-left: 8rpx;
  font-size: 26rpx;
  font-weight: 700;
  color: #0f172a;
}

.field-input,
.picker-wrap,
.field-textarea {
  border: 1rpx solid #e2e8f0;
  border-radius: 24rpx;
  background: #f8fafc;
  color: #0f172a;
  transition: all 0.2s ease;
}

.field-input {
  height: 96rpx;
  line-height: 96rpx;
  padding: 0 32rpx;
  font-size: 30rpx;
}

.field-placeholder {
  color: #94a3b8;
}

.picker-wrap {
  position: relative;
  height: 96rpx;
  display: flex;
  align-items: center;
  padding-right: 84rpx;
}

.picker-control {
  flex: 1;
  height: 100%;
}

.picker-text {
  height: 96rpx;
  line-height: 96rpx;
  padding-left: 32rpx;
  font-size: 30rpx;
  color: #0f172a;
}

.expand-icon {
  position: absolute;
  right: 24rpx;
  top: 50%;
  width: 36rpx;
  height: 36rpx;
  transform: translateY(-50%);
}

.field-textarea {
  min-height: 256rpx;
  padding: 24rpx 32rpx;
  font-size: 30rpx;
  line-height: 1.7;
  width: 100%;
  box-sizing: border-box;
}

.upload-area {
  height: 256rpx;
  border: 2rpx dashed #e2e8f0;
  border-radius: 24rpx;
  background: rgba(248, 250, 252, 0.8);
  display: flex;
  align-items: center;
  justify-content: center;
}

.upload-area-hover {
  background: #f1f5f9;
}

.upload-inner {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8rpx;
}

.upload-icon {
  width: 64rpx;
  height: 64rpx;
}

.upload-text {
  font-size: 24rpx;
  color: #64748b;
}

.file-list {
  margin-top: 16rpx;
  display: flex;
  flex-direction: column;
  gap: 12rpx;
}

.file-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 24rpx;
  border-radius: 16rpx;
  border: 1rpx solid rgba(26, 87, 219, 0.2);
  background: rgba(26, 87, 219, 0.05);
}

.file-left {
  display: flex;
  align-items: center;
  gap: 16rpx;
}

.file-type-icon {
  width: 40rpx;
  height: 40rpx;
}

.file-meta {
  display: flex;
  flex-direction: column;
  gap: 4rpx;
}

.file-name {
  font-size: 26rpx;
  font-weight: 500;
  color: #0f172a;
}

.file-size {
  font-size: 22rpx;
  color: #64748b;
}

.file-remove {
  width: 48rpx;
  height: 48rpx;
  border-radius: 999rpx;
  display: flex;
  align-items: center;
  justify-content: center;
}

.file-remove-hover {
  background: rgba(148, 163, 184, 0.18);
}

.cancel-icon {
  width: 36rpx;
  height: 36rpx;
}

.toggle-card {
  margin-top: 8rpx;
  padding: 28rpx;
  border-radius: 24rpx;
  border: 1rpx solid #f1f5f9;
  background: #f8fafc;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 24rpx;
}

.toggle-copy {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 4rpx;
}

.toggle-title {
  font-size: 26rpx;
  font-weight: 700;
  color: #0f172a;
}

.toggle-desc {
  font-size: 22rpx;
  color: #64748b;
}

.switch-wrap {
  position: relative;
  width: 88rpx;
  height: 48rpx;
}

.switch-track {
  width: 88rpx;
  height: 48rpx;
  border-radius: 999rpx;
  background: #cbd5e1;
  transition: background 0.2s ease;
}

.switch-track-on {
  background: #1a57db;
}

.switch-thumb {
  position: absolute;
  top: 8rpx;
  left: 8rpx;
  width: 32rpx;
  height: 32rpx;
  border-radius: 999rpx;
  background: #ffffff;
  transition: transform 0.2s ease;
}

.switch-thumb-on {
  transform: translateX(40rpx);
}

.save-wrap {
  margin-top: -16rpx;
}

.save-btn {
  width: 100%;
  height: 96rpx;
  border-radius: 24rpx;
  background: #1a57db;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 12rpx 28rpx rgba(26, 87, 219, 0.25);
}

.save-btn-hover {
  background: #1d4ed8;
}

.save-text {
  font-size: 32rpx;
  color: #ffffff;
  font-weight: 700;
}

@media (prefers-color-scheme: dark) {
  .edit-page {
    background: #111621;
  }

  .page-shell {
    background: #111621;
    box-shadow: none;
  }

  .top-nav {
    background: #111621;
    border-bottom-color: #1e293b;
  }

  .back-btn-hover {
    background: #1e293b;
  }

  .back-icon,
  .expand-icon,
  .cancel-icon {
    filter: invert(90%) sepia(10%) saturate(272%) hue-rotate(177deg) brightness(107%) contrast(95%);
  }

  .nav-title,
  .field-label,
  .picker-text,
  .file-name,
  .toggle-title {
    color: #f1f5f9;
  }

  .avatar {
    border-color: #1e293b;
  }

  .camera-badge {
    border-color: #111621;
  }

  .avatar-tip,
  .upload-text,
  .file-size,
  .toggle-desc {
    color: #94a3b8;
  }

  .field-input,
  .picker-wrap,
  .field-textarea {
    background: #0f172a;
    border-color: #1e293b;
    color: #f1f5f9;
  }

  .field-placeholder {
    color: #64748b;
  }

  .upload-area {
    background: rgba(15, 23, 42, 0.6);
    border-color: #1e293b;
  }

  .upload-area-hover {
    background: #1e293b;
  }

  .file-item {
    border-color: rgba(26, 87, 219, 0.25);
    background: rgba(26, 87, 219, 0.1);
  }

  .file-remove-hover {
    background: rgba(100, 116, 139, 0.25);
  }

  .toggle-card {
    background: #0f172a;
    border-color: #1e293b;
  }

  .switch-track {
    background: #334155;
  }

  .switch-track-on {
    background: #1a57db;
  }
}
</style>
