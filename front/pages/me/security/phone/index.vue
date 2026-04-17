<template>
  <view class="phone-bind-page">
    <view class="content-wrap">
      <view class="card form-card">
        <view class="field-block">
          <text class="field-label">新手机号</text>
          <input
            v-model="phone"
            class="field-input"
            type="number"
            maxlength="11"
            placeholder="请输入11位手机号"
            placeholder-class="field-placeholder"
          />
        </view>

        <view class="field-block">
          <text class="field-label">{{ codeFieldLabel }}</text>
          <view class="code-row">
            <input
              v-model="code"
              class="field-input code-input"
              type="number"
              maxlength="6"
              :placeholder="codePlaceholder"
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
        {{ submitLoading ? '提交中...' : '确认绑定' }}
      </button>
    </view>
  </view>
</template>

<script setup>
import { computed, onUnmounted, ref, watch } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import { bindPhone, sendPhoneBindCode } from '../../../../api/auth'
import { getCurrentUserProfile } from '../../../../api/user'

const PHONE_REGEX = /^1\d{10}$/
const CODE_REGEX = /^\d{4,8}$/
const COUNTDOWN_SECONDS = 60

const phone = ref('')
const code = ref('')
const currentPhoneMasked = ref('未绑定')
const hasBoundPhone = ref(false)
const sendingCode = ref(false)
const submitLoading = ref(false)
const countdown = ref(0)
let countdownTimer = null

const normalizePhone = (value) => String(value || '').replace(/\D/g, '').slice(0, 11)
const normalizeCode = (value) => String(value || '').replace(/\D/g, '').slice(0, 8)

watch(phone, (value) => {
  const nextValue = normalizePhone(value)
  if (nextValue !== value) {
    phone.value = nextValue
  }
})

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

const codeFieldLabel = computed(() => {
  return hasBoundPhone.value ? '原手机号验证码' : '验证码'
})

const codePlaceholder = computed(() => {
  return hasBoundPhone.value ? '请输入原号验证码' : '请输入验证码'
})

const showToast = (title) => {
  uni.showToast({
    title,
    icon: 'none'
  })
}

const maskPhone = (rawPhone) => {
  const raw = String(rawPhone || '').replace(/\D/g, '')
  if (!PHONE_REGEX.test(raw)) {
    return '未绑定'
  }
  return `${raw.slice(0, 3)}****${raw.slice(7)}`
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

const loadCurrentPhone = async () => {
  try {
    const profile = await getCurrentUserProfile()
    currentPhoneMasked.value = maskPhone(profile?.phone)
    hasBoundPhone.value = PHONE_REGEX.test(String(profile?.phone || '').replace(/\D/g, ''))
  } catch (err) {
    if (err?.statusCode === 401) {
      uni.navigateTo({
        url: '/pages/auth/login/index'
      })
      return
    }
    showToast(err?.message || '获取用户信息失败')
  }
}

const onSendCode = async () => {
  if (codeDisabled.value) {
    return
  }

  const currentPhone = normalizePhone(phone.value)
  phone.value = currentPhone
  if (!PHONE_REGEX.test(currentPhone)) {
    showToast('请输入正确的手机号')
    return
  }

  sendingCode.value = true
  try {
    const result = await sendPhoneBindCode(currentPhone)
    startCountdown()
    if (result?.debug_code) {
      code.value = result.debug_code
      showToast(`验证码已发送: ${result.debug_code}`)
      return
    }
    const sendPhone = maskPhone(result?.phone || currentPhone)
    if (hasBoundPhone.value) {
      showToast(`验证码已发送至原手机号 ${sendPhone}`)
      return
    }
    showToast(`验证码已发送至新手机号 ${sendPhone}`)
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

  const currentPhone = normalizePhone(phone.value)
  const currentCode = normalizeCode(code.value)
  phone.value = currentPhone
  code.value = currentCode

  if (!PHONE_REGEX.test(currentPhone)) {
    showToast('请输入正确的手机号')
    return
  }

  if (!CODE_REGEX.test(currentCode)) {
    showToast('请输入正确的验证码')
    return
  }

  submitLoading.value = true
  try {
    const result = await bindPhone(currentPhone, currentCode)
    currentPhoneMasked.value = result?.masked_phone || maskPhone(result?.phone || currentPhone)
    showToast('手机号绑定成功')
    setTimeout(() => {
      uni.navigateBack()
    }, 250)
  } catch (err) {
    if (err?.statusCode === 401) {
      uni.navigateTo({
        url: '/pages/auth/login/index'
      })
      return
    }
    showToast(err?.message || '手机号绑定失败，请稍后重试')
  } finally {
    submitLoading.value = false
  }
}

onShow(() => {
  loadCurrentPhone()
})

onUnmounted(() => {
  if (countdownTimer) {
    clearInterval(countdownTimer)
    countdownTimer = null
  }
})
</script>

<style scoped>
.phone-bind-page {
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
  .phone-bind-page,
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
