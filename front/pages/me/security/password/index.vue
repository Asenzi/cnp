<template>
  <view class="password-page">
    <view class="content-wrap">
      <view class="card form-card">
        <view class="field-block">
          <text class="field-label">验证码</text>
          <view class="code-row">
            <input
              v-model="code"
              class="field-input code-input"
              type="number"
              maxlength="6"
              placeholder="请输入验证码"
              placeholder-class="field-placeholder"
            />
            <button
              class="code-btn"
              :class="{ 'code-btn-disabled': codeDisabled }"
              :disabled="codeDisabled"
              hover-class="code-btn-active"
              @tap="onSendCode"
            >
              {{ codeButtonText }}
            </button>
          </view>
        </view>

        <view class="field-block">
          <text class="field-label">新密码</text>
          <input
            v-model="newPassword"
            class="field-input"
            type="text"
            password
            maxlength="32"
            placeholder="请输入6-32位新密码"
            placeholder-class="field-placeholder"
          />
        </view>

        <view class="field-block">
          <text class="field-label">确认新密码</text>
          <input
            v-model="confirmPassword"
            class="field-input"
            type="text"
            password
            maxlength="32"
            placeholder="请再次输入新密码"
            placeholder-class="field-placeholder"
          />
        </view>
      </view>
    </view>

    <view class="footer-wrap">
      <button
        class="submit-btn"
        :class="{ 'submit-btn-disabled': submitLoading }"
        :disabled="submitLoading"
        hover-class="submit-btn-active"
        @tap="onSubmit"
      >
        {{ submitLoading ? '提交中...' : '确认修改' }}
      </button>
    </view>
  </view>
</template>

<script setup>
import { computed, onUnmounted, ref, watch } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import { changePasswordBySms, sendPasswordChangeCode } from '../../../../api/auth'
import { getCurrentUserProfile } from '../../../../api/user'

const COUNTDOWN_SECONDS = 60
const CODE_REGEX = /^\d{4,8}$/

const code = ref('')
const newPassword = ref('')
const confirmPassword = ref('')
const sendingCode = ref(false)
const submitLoading = ref(false)
const countdown = ref(0)
let countdownTimer = null

const normalizeCode = (value) => String(value || '').replace(/\D/g, '').slice(0, 8)
watch(code, (value) => {
  const nextValue = normalizeCode(value)
  if (nextValue !== value) {
    code.value = nextValue
  }
})

const codeDisabled = computed(() => sendingCode.value || countdown.value > 0)
const codeButtonText = computed(() => {
  if (sendingCode.value) {
    return '发送中...'
  }
  if (countdown.value > 0) {
    return `${countdown.value}s`
  }
  return '获取验证码'
})

const showToast = (title) => {
  uni.showToast({
    title,
    icon: 'none'
  })
}

const startCountdown = () => {
  if (countdownTimer) {
    clearInterval(countdownTimer)
  }
  countdown.value = COUNTDOWN_SECONDS
  countdownTimer = setInterval(() => {
    countdown.value -= 1
    if (countdown.value <= 0) {
      clearInterval(countdownTimer)
      countdownTimer = null
      countdown.value = 0
    }
  }, 1000)
}

const ensurePhoneBound = async () => {
  try {
    const profile = await getCurrentUserProfile()
    const phone = String(profile?.phone || '').replace(/\D/g, '')
    if (!/^1\d{10}$/.test(phone)) {
      showToast('手机号未绑定，无法修改密码')
      setTimeout(() => {
        uni.navigateBack()
      }, 200)
      return false
    }
    return true
  } catch (err) {
    if (err?.statusCode === 401) {
      uni.navigateTo({
        url: '/pages/auth/login/index'
      })
      return false
    }
    showToast(err?.message || '获取用户信息失败')
    return false
  }
}

const onSendCode = async () => {
  if (codeDisabled.value) {
    return
  }

  sendingCode.value = true
  try {
    const result = await sendPasswordChangeCode()
    startCountdown()
    if (result?.debug_code) {
      code.value = result.debug_code
      showToast(`验证码已发送: ${result.debug_code}`)
      return
    }
    showToast('验证码已发送')
  } catch (err) {
    if (err?.statusCode === 401) {
      uni.navigateTo({
        url: '/pages/auth/login/index'
      })
      return
    }
    showToast(err?.message || '发送失败，请稍后重试')
  } finally {
    sendingCode.value = false
  }
}

const onSubmit = async () => {
  if (submitLoading.value) {
    return
  }

  const currentCode = normalizeCode(code.value)
  code.value = currentCode
  const pwd = String(newPassword.value || '')
  const pwd2 = String(confirmPassword.value || '')

  if (!CODE_REGEX.test(currentCode)) {
    showToast('请输入正确的验证码')
    return
  }

  if (pwd.length < 6 || pwd.length > 32) {
    showToast('新密码长度需为6-32位')
    return
  }

  if (pwd !== pwd2) {
    showToast('两次输入的新密码不一致')
    return
  }

  submitLoading.value = true
  try {
    const result = await changePasswordBySms(currentCode, pwd)
    showToast('密码修改成功，请重新登录')
    if (result?.force_relogin) {
      uni.removeStorageSync('token')
      uni.removeStorageSync('isLoggedIn')
      uni.removeStorageSync('userInfo')
    }
    setTimeout(() => {
      uni.reLaunch({
        url: '/pages/auth/login/index'
      })
    }, 250)
  } catch (err) {
    if (err?.statusCode === 401) {
      uni.navigateTo({
        url: '/pages/auth/login/index'
      })
      return
    }
    showToast(err?.message || '修改密码失败，请稍后重试')
  } finally {
    submitLoading.value = false
  }
}

onShow(async () => {
  await ensurePhoneBound()
})

onUnmounted(() => {
  if (countdownTimer) {
    clearInterval(countdownTimer)
    countdownTimer = null
  }
})
</script>

<style scoped>
.password-page {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  background: #f6f6f8;
}

.content-wrap {
  flex: 1;
  padding: 16px;
  box-sizing: border-box;
}

.card {
  background: #ffffff;
  border-radius: 12px;
  border: 1px solid #f1f5f9;
  box-shadow: 0 2px 8px rgba(15, 23, 42, 0.04);
  padding: 16px;
  box-sizing: border-box;
}

.form-card {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.field-block {
  display: flex;
  flex-direction: column;
}

.field-label {
  font-size: 14px;
  line-height: 20px;
  color: #334155;
  font-weight: 600;
  margin-bottom: 8px;
}

.field-input {
  width: 100%;
  height: 48px;
  border-radius: 10px;
  border: 1px solid #e2e8f0;
  background: #ffffff;
  box-sizing: border-box;
  padding: 0 14px;
  font-size: 16px;
  color: #0f172a;
}

.field-placeholder {
  color: #94a3b8;
}

.code-row {
  display: flex;
  gap: 10px;
  align-items: center;
}

.code-input {
  flex: 1;
  min-width: 0;
}

.code-btn {
  width: 120px;
  height: 48px;
  border-radius: 10px;
  border: 0;
  background: rgba(26, 87, 219, 0.1);
  color: #1a57db;
  font-size: 14px;
  font-weight: 600;
  display: flex;
  align-items: center;
  justify-content: center;
}

.code-btn-active {
  opacity: 0.85;
}

.code-btn-disabled {
  opacity: 0.6;
}

.footer-wrap {
  padding: 12px 16px calc(16px + env(safe-area-inset-bottom));
  background: #f6f6f8;
  box-sizing: border-box;
}

.submit-btn {
  width: 100%;
  height: 50px;
  border-radius: 12px;
  border: 0;
  background: #1a57db;
  color: #ffffff;
  font-size: 18px;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 10px 24px rgba(26, 87, 219, 0.25);
}

.submit-btn-active {
  transform: scale(0.98);
}

.submit-btn-disabled {
  opacity: 0.8;
}

@media (prefers-color-scheme: dark) {
  .password-page,
  .footer-wrap {
    background: #111621;
  }

  .card {
    background: #0f172a;
    border-color: #1e293b;
    box-shadow: none;
  }

  .field-label {
    color: #cbd5e1;
  }

  .field-input {
    background: #1e293b;
    border-color: #334155;
    color: #f8fafc;
  }

  .field-placeholder {
    color: #64748b;
  }

  .code-btn {
    background: rgba(26, 87, 219, 0.22);
    color: #60a5fa;
  }
}
</style>
