<template>
  <view class="publish-page">
    <scroll-view class="publish-scroll" scroll-y :show-scrollbar="false">
      <view class="page-body">
        <view class="mode-strip">
          <button
            v-for="item in modeOptions"
            :key="item.key"
            class="mode-tab"
            :class="form.mode === item.key ? 'mode-tab-active' : ''"
            hover-class="mode-tab-hover"
            @tap="setMode(item.key)"
          >
            <text class="mode-tab-label">{{ item.title }}</text>
            <view v-if="form.mode === item.key" class="mode-tab-line"></view>
          </button>
        </view>

        <view class="card title-card">
          <input
            class="title-input"
            :value="form.title"
            maxlength="120"
            placeholder="请输入标题"
            placeholder-class="placeholder-title"
            @input="onInputTitle"
          />
        </view>

        <view class="card editor-card">
          <textarea
            class="desc-input"
            :value="form.description"
            maxlength="5000"
            :placeholder="descriptionPlaceholder"
            placeholder-class="placeholder-body"
            :show-confirm-bar="false"
            auto-height
            @input="onInputDescription"
          />

          <view class="media-section">
            <text class="media-label">上传图片 (最多9张)</text>

            <view class="media-grid">
              <view
                v-for="(item, index) in imageList"
                :key="`${item}-${index}`"
                class="media-item"
              >
                <image class="media-image" mode="aspectFill" :src="item" @tap="onPreviewImage(index)" />
                <button class="remove-btn" hover-class="remove-btn-active" @tap.stop="onRemoveImage(index)">
                  ×
                </button>
              </view>

              <button
                v-if="imageList.length < 9"
                class="upload-tile"
                hover-class="upload-tile-hover"
                :disabled="uploading || loadingDetail"
                @tap="onChooseImages"
              >
                <text class="upload-icon">+</text>
                <text class="upload-text">{{ uploading ? uploadProgressText : '添加图片' }}</text>
              </button>
            </view>
          </view>
        </view>

        <view v-if="form.mode === 'venue'" class="card venue-card">
          <view class="card-head">
            <text class="card-head-title">定位信息</text>
          </view>

          <button class="industry-trigger" hover-class="industry-trigger-hover" @tap="onChooseLocation">
            <view class="industry-trigger-content sync-trigger-content">
              <text v-if="venueForm.location" class="sync-selected-text">{{ venueForm.location }}</text>
              <text v-else class="industry-trigger-placeholder">点击选择定位</text>
            </view>
            <text class="industry-trigger-arrow">›</text>
          </button>
        </view>

        <view class="card tags-card">
          <view class="card-head">
            <text class="card-head-title">行业/资源标签</text>
          </view>

          <button class="industry-trigger" hover-class="industry-trigger-hover" @tap="openIndustryPopup">
            <view class="industry-trigger-content">
              <text v-if="normalizedIndustry" class="industry-selected-text">{{ normalizedIndustry }}</text>
              <text v-else class="industry-trigger-placeholder">点击选择行业标签</text>
            </view>
            <text class="industry-trigger-arrow">›</text>
          </button>
        </view>

        <view class="card sync-card">
          <view class="card-head">
            <text class="card-head-title">同步到圈子</text>
          </view>

          <button class="industry-trigger" hover-class="industry-trigger-hover" @tap="openCirclePopup">
            <view class="industry-trigger-content sync-trigger-content">
              <text v-if="selectedCircleNamesText" class="sync-selected-text">{{ selectedCircleNamesText }}</text>
              <text v-else class="industry-trigger-placeholder">点击选择要同步的圈子</text>
            </view>
            <text class="industry-trigger-arrow">›</text>
          </button>

          <text class="sync-meta-text">{{ syncMetaText }}</text>
        </view>

        <view class="card settings-card">
          <text class="settings-label">信息有效期</text>

          <view class="settings-grid">
            <button
              v-for="item in validityOptions"
              :key="item.value"
              class="settings-option"
              :class="selectedValidity === item.value ? 'settings-option-active' : ''"
              hover-class="settings-option-hover"
              @tap="selectedValidity = item.value"
            >
              {{ item.label }}
            </button>
          </view>
        </view>

        <view class="card visibility-card">
          <view>
            <text class="card-head-title">谁可以看</text>
            <text class="visibility-subtitle">控制资源的曝光范围</text>
          </view>

          <view class="visibility-switch">
            <button
              v-for="item in visibilityOptions"
              :key="item.value"
              class="visibility-option"
              :class="selectedVisibility === item.value ? 'visibility-option-active' : ''"
              hover-class="visibility-option-hover"
              @tap="selectedVisibility = item.value"
            >
              {{ item.label }}
            </button>
          </view>
        </view>
      </view>
    </scroll-view>

    <view class="bottom-bar">
      <button
        class="submit-btn"
        :class="submitDisabled ? 'submit-btn-disabled' : ''"
        :disabled="submitDisabled"
        hover-class="submit-btn-hover"
        @tap="onSubmit"
      >
        <text>{{ submitButtonText }}</text>
        <text class="submit-btn-arrow">›</text>
      </button>
    </view>

    <view v-if="loadingDetail" class="loading-mask">
      <view class="loading-card">
        <text class="loading-title">加载中</text>
        <text class="loading-desc">正在读取资源内容...</text>
      </view>
    </view>

    <view v-if="industryPopupVisible" class="filter-mask" @tap="closeIndustryPopup">
      <view class="filter-panel" @tap.stop>
        <view class="panel-head">
          <text class="panel-title">选择行业</text>
          <text class="panel-subtitle">用于标记当前发布的资源方向</text>
        </view>

        <view class="section">
          <view class="section-label">行业方向</view>
          <view class="option-grid">
            <view
              v-for="industry in industryOptions"
              :key="`industry-${industry}`"
              class="option-chip"
              :class="draftIndustry === industry ? 'option-chip-active' : ''"
              @tap="onPickDraftIndustry(industry)"
            >
              <text
                class="option-chip-text"
                :class="draftIndustry === industry ? 'option-chip-text-active' : ''"
              >
                {{ industry }}
              </text>
            </view>
          </view>
        </view>

        <view class="actions">
          <button class="reset-btn" hover-class="reset-btn-active" @tap="resetIndustryPopup">不限行业</button>
          <button class="apply-btn" hover-class="apply-btn-active" @tap="applyIndustryPopup">应用行业</button>
        </view>
      </view>
    </view>

    <view v-if="circlePopupVisible" class="filter-mask" @tap="closeCirclePopup">
      <view class="filter-panel" @tap.stop>
        <view class="panel-head">
          <text class="panel-title">选择同步圈子</text>
          <text class="panel-subtitle">{{ syncMetaText }}</text>
        </view>

        <view class="section">
          <view class="section-label">我的圈子</view>
          <view v-if="myCircles.length" class="circle-option-list">
            <view
              v-for="circle in myCircles"
              :key="circle.circle_code"
              class="circle-option"
              :class="draftSelectedCircleCodes.includes(circle.circle_code) ? 'circle-option-active' : ''"
              @tap="toggleDraftCircle(circle.circle_code)"
            >
              <view class="circle-option-main">
                <text class="circle-option-name">{{ circle.name }}</text>
                <text class="circle-option-meta">{{ circle.industry_label }} · {{ circle.member_count }}人</text>
              </view>
              <view class="circle-option-check">
                <view
                  class="circle-option-check-core"
                  :class="draftSelectedCircleCodes.includes(circle.circle_code) ? 'circle-option-check-core-active' : ''"
                ></view>
              </view>
            </view>
          </view>
          <view v-else class="empty-circle-wrap">
            <text class="empty-circle-text">{{ circleEmptyText }}</text>
          </view>
        </view>

        <view class="actions">
          <button class="reset-btn" hover-class="reset-btn-active" @tap="resetCirclePopup">清空选择</button>
          <button class="apply-btn" hover-class="apply-btn-active" @tap="applyCirclePopup">应用圈子</button>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup>
import { computed, ref } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
import { getMyCircles } from '../../../api/circle'
import { getCurrentUserProfile } from '../../../api/user'
import {
  createResourcePost,
  getResourceDetail,
  updateResourcePost,
  uploadResourceImage
} from '../../../api/post'
import { INDUSTRY_OPTIONS } from '../../../utils/industry-options'

const modeOptions = [
  { key: 'cooperate', title: '找合作' },
  { key: 'resource', title: '找资源' },
  { key: 'venue', title: '发布活动' }
]

const validityOptions = [ 
  { value: '3d', label: '3天' },
  { value: '7d', label: '7天' },
  { value: '30d', label: '30天' },
  { value: 'forever', label: '永久' }
]

const visibilityOptions = [
  { value: 'all', label: '所有人' },
  { value: 'verified', label: '仅实名用户' }
]

const ACTIVITY_META_LABELS = {
  area: '活动面积',
  capacity: '容纳人数',
  location: '活动地点'
}

const LEGACY_VENUE_META_LABELS = {
  area: '场地面积',
  capacity: '容纳人数',
  location: '地理位置'
}

const form = ref({
  mode: 'venue',
  title: '',
  industry_label: '',
  description: '',
  images: [],
  sync_circle_codes: []
})

const venueForm = ref({
  area: '',
  capacity: '',
  location: ''
})

const selectedValidity = ref('30d')
const selectedVisibility = ref('all')
const industryPopupVisible = ref(false)
const draftIndustry = ref('')
const circlePopupVisible = ref(false)
const draftSelectedCircleCodes = ref([])
const myCircles = ref([])
const currentUserState = ref({})

const editingPostCode = ref('')
const uploading = ref(false)
const submitting = ref(false)
const loadingDetail = ref(false)
const uploadProgress = ref({
  done: 0,
  total: 0
})

let openerEventChannel = null

const isEditMode = computed(() => Boolean(editingPostCode.value))
const imageList = computed(() => (Array.isArray(form.value.images) ? form.value.images : []))
const selectedCircleCodes = computed(() => (Array.isArray(form.value.sync_circle_codes) ? form.value.sync_circle_codes : []))
const normalizedTitle = computed(() => String(form.value.title || '').trim())
const normalizedIndustry = computed(() => String(form.value.industry_label || '').trim())
const normalizedDescription = computed(() => String(form.value.description || '').trim())
const storedUserInfo = computed(() => {
  const payload = uni.getStorageSync('userInfo')
  return payload && typeof payload === 'object' ? payload : {}
})
const syncLimit = computed(() => {
  const info = Object.keys(currentUserState.value || {}).length ? currentUserState.value : storedUserInfo.value || {}
  const candidateFlags = [
    info?.is_member,
    info?.member_opened,
    info?.is_vip,
    info?.vip_opened,
    info?.pro_member
  ]
  if (candidateFlags.some(Boolean)) {
    return 5
  }
  const memberStatus = String(info?.member_status || info?.vip_status || '').trim().toLowerCase()
  if (['active', 'opened', 'member', 'vip', 'paid', 'enabled', 'on'].includes(memberStatus)) {
    return 5
  }
  return info?.is_verified ? 1 : 0
})
const selectedCircleNamesText = computed(() => {
  const codeSet = new Set(selectedCircleCodes.value.map((item) => String(item || '').trim().toUpperCase()))
  const names = myCircles.value
    .filter((item) => codeSet.has(String(item?.circle_code || '').trim().toUpperCase()))
    .map((item) => String(item?.name || '').trim())
    .filter(Boolean)
  return names.join('、')
})
const syncMetaText = computed(() => {
  if (syncLimit.value <= 0) {
    return '完成实名认证后可同步到圈子'
  }
  if (syncLimit.value === 1) {
    return `实名用户最多同步 1 个圈子，当前已选 ${selectedCircleCodes.value.length}/1`
  }
  return `会员用户最多同步 5 个圈子，当前已选 ${selectedCircleCodes.value.length}/5`
})
const circleEmptyText = computed(() => {
  if (syncLimit.value <= 0) {
    return '完成实名认证后可选择圈子同步'
  }
  return '暂无可同步的圈子'
})

const descriptionPlaceholder = computed(() => {
  if (form.value.mode === 'venue') {
    return '请输入资源或活动详情描述...'
  }
  return '请输入资源或合作详情描述...'
})

const submitDisabled = computed(() => {
  return (
    uploading.value
    || submitting.value
    || loadingDetail.value
    || normalizedTitle.value.length < 2
    || normalizedDescription.value.length < 5
  )
})

const submitButtonText = computed(() => {
  if (submitting.value) {
    return isEditMode.value ? '保存中' : '发布中'
  }
  return isEditMode.value ? '保存修改' : '立即发布'
})

const uploadProgressText = computed(() => {
  if (!uploading.value || !uploadProgress.value.total) {
    return '添加图片'
  }
  return `上传中 ${uploadProgress.value.done}/${uploadProgress.value.total}`
})

const industryOptions = computed(() => {
  return INDUSTRY_OPTIONS
})

const showToast = (title) => {
  uni.showToast({
    title,
    icon: 'none'
  })
}

const ensureLocationPermission = async () => {
  const setting = await new Promise((resolve) => {
    uni.getSetting({
      success: resolve,
      fail: () => resolve({ authSetting: {} })
    })
  })

  if (setting?.authSetting?.['scope.userLocation']) {
    return true
  }

  try {
    await new Promise((resolve, reject) => {
      uni.authorize({
        scope: 'scope.userLocation',
        success: resolve,
        fail: reject
      })
    })
    return true
  } catch (err) {
    const message = String(err?.errMsg || '').toLowerCase()
    if (message.includes('auth deny') || message.includes('deny') || message.includes('authorize')) {
      showToast('请在设置中开启定位权限')
    } else {
      showToast('定位权限未开启')
    }
    return false
  }
}

const setMode = (mode) => {
  const nextMode = String(mode || '').trim()
  form.value.mode = ['cooperate', 'resource', 'venue'].includes(nextMode) ? nextMode : 'cooperate'
}

const onInputTitle = (event) => {
  form.value.title = String(event?.detail?.value || '')
}

const onInputDescription = (event) => {
  form.value.description = String(event?.detail?.value || '')
}

const openIndustryPopup = () => {
  draftIndustry.value = normalizedIndustry.value
  industryPopupVisible.value = true
}

const openCirclePopup = () => {
  if (syncLimit.value <= 0) {
    showToast('完成实名认证后才可同步到圈子')
    return
  }
  draftSelectedCircleCodes.value = [...selectedCircleCodes.value]
  circlePopupVisible.value = true
}

const closeCirclePopup = () => {
  circlePopupVisible.value = false
}

const toggleDraftCircle = (circleCode) => {
  const code = String(circleCode || '').trim().toUpperCase()
  if (!code) {
    return
  }
  const current = [...draftSelectedCircleCodes.value]
  const index = current.indexOf(code)
  if (index >= 0) {
    current.splice(index, 1)
    draftSelectedCircleCodes.value = current
    return
  }
  if (current.length >= syncLimit.value) {
    showToast(`最多选择 ${syncLimit.value} 个圈子`)
    return
  }
  draftSelectedCircleCodes.value = [...current, code]
}

const resetCirclePopup = () => {
  draftSelectedCircleCodes.value = []
  form.value.sync_circle_codes = []
  closeCirclePopup()
}

const applyCirclePopup = () => {
  form.value.sync_circle_codes = [...draftSelectedCircleCodes.value]
  closeCirclePopup()
}

const closeIndustryPopup = () => {
  industryPopupVisible.value = false
}

const onPickDraftIndustry = (value) => {
  draftIndustry.value = String(value || '').trim()
}

const resetIndustryPopup = () => {
  draftIndustry.value = ''
  form.value.industry_label = ''
  closeIndustryPopup()
}

const applyIndustryPopup = () => {
  form.value.industry_label = String(draftIndustry.value || '').trim()
  closeIndustryPopup()
}

const onInputVenueArea = (event) => {
  venueForm.value.area = String(event?.detail?.value || '').trim()
}

const onInputVenueCapacity = (event) => {
  venueForm.value.capacity = String(event?.detail?.value || '').trim()
}

const onChooseLocation = async () => {
  try {
    const permitted = await ensureLocationPermission()
    if (!permitted) {
      return
    }

    const result = await new Promise((resolve, reject) => {
      uni.chooseLocation({
        success: resolve,
        fail: reject
      })
    })
    const name = String(result?.name || '').trim()
    const address = String(result?.address || '').trim()
    venueForm.value.location = [name, address].filter(Boolean).join(' / ')
  } catch (err) {
    const message = String(err?.errMsg || '')
    if (!message || message.includes('cancel') || message.includes('chooseLocation:fail cancel')) {
      return
    }
    if (message.includes('auth deny') || message.includes('permission')) {
      showToast('请在设置中开启定位权限')
      return
    }
    showToast(message || '位置选择失败，请检查定位服务')
  }
}

const onRemoveImage = (index) => {
  const safeIndex = Number(index || 0)
  form.value.images = imageList.value.filter((_, itemIndex) => itemIndex !== safeIndex)
}

const onPreviewImage = (index) => {
  if (!imageList.value.length) {
    return
  }
  uni.previewImage({
    urls: imageList.value,
    current: imageList.value[Math.max(Number(index || 0), 0)] || imageList.value[0]
  })
}

const onChooseImages = async () => {
  if (uploading.value || loadingDetail.value) {
    return
  }

  const remain = 9 - imageList.value.length
  if (remain <= 0) {
    showToast('最多上传 9 张图片')
    return
  }

  let selected = null
  try {
    selected = await new Promise((resolve, reject) => {
      uni.chooseImage({
        count: remain,
        sizeType: ['compressed'],
        sourceType: ['album', 'camera'],
        success: resolve,
        fail: reject
      })
    })
  } catch {
    return
  }

  const tempFilePaths = Array.isArray(selected?.tempFilePaths) ? selected.tempFilePaths : []
  if (!tempFilePaths.length) {
    return
  }

  const nextImages = [...imageList.value]
  let successCount = 0
  let failedCount = 0

  uploading.value = true
  uploadProgress.value = {
    done: 0,
    total: tempFilePaths.length
  }

  try {
    for (let index = 0; index < tempFilePaths.length; index += 1) {
      const path = tempFilePaths[index]
      uni.showLoading({
        title: `上传中 ${index + 1}/${tempFilePaths.length}`,
        mask: true
      })

      try {
        const data = await uploadResourceImage(path, `resource-image-${index + 1}.jpg`)
        const url = String(data?.url || '').trim()
        if (url && nextImages.length < 9) {
          nextImages.push(url)
          form.value.images = [...nextImages]
          successCount += 1
        } else {
          failedCount += 1
        }
      } catch {
        failedCount += 1
      } finally {
        uploadProgress.value = {
          done: index + 1,
          total: tempFilePaths.length
        }
      }
    }

    if (successCount && failedCount) {
      showToast(`已上传 ${successCount} 张，失败 ${failedCount} 张`)
    } else if (successCount) {
      showToast(`已上传 ${successCount} 张图片`)
    } else {
      showToast('图片上传失败，请重试')
    }
  } finally {
    uploading.value = false
    uploadProgress.value = {
      done: 0,
      total: 0
    }
    uni.hideLoading()
  }
}

const loadMyCircles = async () => {
  if (syncLimit.value <= 0) {
    myCircles.value = []
    return
  }
  try {
    const payload = await getMyCircles({ offset: 0, limit: 100 })
    myCircles.value = Array.isArray(payload?.items) ? payload.items : []
  } catch {
    myCircles.value = []
  }
}

const loadCurrentUserState = async () => {
  try {
    const profile = await getCurrentUserProfile()
    currentUserState.value = profile && typeof profile === 'object' ? profile : {}
  } catch {
    currentUserState.value = {}
  }
}

const stripVenueMetaFromDescription = (rawDescription) => {
  const source = String(rawDescription || '').trim()
  if (!source) {
    return {
      description: '',
      venue: {
        area: '',
        capacity: '',
        location: ''
      }
    }
  }

  const lines = source.split(/\n+/)
  const remaining = []
  const venue = {
    area: '',
    capacity: '',
    location: ''
  }

  const stripPrefix = (value, label) => {
    const prefix = `${label}\uFF1A`
    if (!value.startsWith(prefix)) {
      return ''
    }
    return value.replace(prefix, '').trim()
  }

  lines.forEach((line) => {
    const value = String(line || '').trim()
    if (!value) {
      return
    }

    const activityArea = stripPrefix(value, ACTIVITY_META_LABELS.area)
    const legacyArea = stripPrefix(value, LEGACY_VENUE_META_LABELS.area)
    if (activityArea || legacyArea) {
      venue.area = (activityArea || legacyArea).replace(/\u33A1/g, '').trim()
      return
    }

    const activityCapacity = stripPrefix(value, ACTIVITY_META_LABELS.capacity)
    const legacyCapacity = stripPrefix(value, LEGACY_VENUE_META_LABELS.capacity)
    if (activityCapacity || legacyCapacity) {
      venue.capacity = (activityCapacity || legacyCapacity).replace(/\u4eba/g, '').trim()
      return
    }

    const activityLocation = stripPrefix(value, ACTIVITY_META_LABELS.location)
    const legacyLocation = stripPrefix(value, LEGACY_VENUE_META_LABELS.location)
    if (activityLocation || legacyLocation) {
      venue.location = activityLocation || legacyLocation
      return
    }

    remaining.push(value)
  })

  return {
    description: remaining.join('\n'),
    venue
  }
}

const buildSubmitDescription = () => {
  const base = normalizedDescription.value
  if (form.value.mode !== 'venue') {
    return base
  }

  const metaLines = []
  if (venueForm.value.area) {
    metaLines.push(`${ACTIVITY_META_LABELS.area}\uFF1A${venueForm.value.area}\u33A1`)
  }
  if (venueForm.value.capacity) {
    metaLines.push(`${ACTIVITY_META_LABELS.capacity}\uFF1A${venueForm.value.capacity}\u4eba`)
  }
  if (venueForm.value.location) {
    metaLines.push(`${ACTIVITY_META_LABELS.location}\uFF1A${venueForm.value.location}`)
  }

  return [base, ...metaLines].filter(Boolean).join('\n')
}

const loadEditingDetail = async () => {
  if (!editingPostCode.value) {
    return
  }

  loadingDetail.value = true
  try {
    const data = await getResourceDetail(editingPostCode.value)
    const mode = String(data?.mode || 'cooperate').trim()
    const parsedVenue = stripVenueMetaFromDescription(String(data?.description || ''))

    form.value = {
      mode: ['cooperate', 'resource', 'venue'].includes(mode) ? mode : 'cooperate',
      title: String(data?.title || '').trim(),
      industry_label: String(data?.industry_label || '').trim(),
      description: parsedVenue.description,
      sync_circle_codes: Array.isArray(data?.circle_syncs)
        ? data.circle_syncs
          .map((item) => String(item?.circle_code || '').trim().toUpperCase())
          .filter(Boolean)
        : [],
      images: Array.isArray(data?.images)
        ? data.images.map((item) => String(item || '').trim()).filter(Boolean)
        : []
    }

    venueForm.value = parsedVenue.venue
  } catch (err) {
    showToast(err?.message || '资源详情加载失败')
    setTimeout(() => {
      uni.navigateBack()
    }, 260)
  } finally {
    loadingDetail.value = false
  }
}

const onSubmit = async () => {
  const title = normalizedTitle.value
  const description = buildSubmitDescription()

  if (title.length < 2) {
    showToast('标题至少 2 个字')
    return
  }

  if (normalizedDescription.value.length < 5) {
    showToast('描述至少 5 个字')
    return
  }

  if (uploading.value) {
    showToast('请等待图片上传完成')
    return
  }

  if (form.value.mode === 'venue' && !String(venueForm.value.location || '').trim()) {
    showToast('请先选择定位')
    return
  }

  if (submitting.value || loadingDetail.value) {
    return
  }

  submitting.value = true
  try {
    const payload = {
      mode: form.value.mode,
      title,
      industry_label: normalizedIndustry.value,
      description,
      images: imageList.value,
      sync_circle_codes: selectedCircleCodes.value
    }

    const result = isEditMode.value
      ? await updateResourcePost(editingPostCode.value, payload)
      : await createResourcePost(payload)

    const review = result && typeof result._review === 'object' ? result._review : null
    if (review?.review_required) {
      showToast(isEditMode.value ? '资源修改已提交审核' : '资源内容已提交审核')
      setTimeout(() => {
        uni.navigateBack()
      }, 220)
      return
    }

    showToast(isEditMode.value ? '保存成功' : '发布成功')
    if (openerEventChannel) {
      openerEventChannel.emit(isEditMode.value ? 'updated' : 'created', result || {})
    }
    setTimeout(() => {
      uni.navigateBack()
    }, 220)
  } catch (err) {
    showToast(err?.message || (isEditMode.value ? '保存失败，请稍后重试' : '发布失败，请稍后重试'))
  } finally {
    submitting.value = false
  }
}

onLoad((query = {}) => {
  if (typeof uni.getOpenerEventChannel === 'function') {
    openerEventChannel = uni.getOpenerEventChannel()
  }

  editingPostCode.value = String(query?.postCode || '').trim()
  uni.setNavigationBarTitle({
    title: editingPostCode.value ? '编辑资源' : '发布资源'
  })

  loadCurrentUserState().finally(() => {
    loadMyCircles()
  })
  if (editingPostCode.value) {
    loadEditingDetail()
  }
})
</script>

<style scoped>
.publish-page {
  min-height: 100vh;
  background: #f6f6f8;
  color: #0f172a;
}

.publish-scroll {
  height: calc(100vh - 144rpx - env(safe-area-inset-bottom));
}

.page-body {
  width: 100%;
  box-sizing: border-box;
  padding: 24rpx 32rpx 48rpx;
}

.mode-strip {
  display: flex;
  align-items: center;
  justify-content: flex-start;
  gap: 40rpx;
  padding: 8rpx 0 16rpx;
}

.mode-tab,
.upload-tile,
.remove-btn,
.settings-option,
.visibility-option,
.submit-btn,
.location-trigger,
.industry-trigger,
.reset-btn,
.apply-btn {
  border: 0;
}

.mode-tab::after,
.upload-tile::after,
.remove-btn::after,
.settings-option::after,
.visibility-option::after,
.submit-btn::after,
.location-trigger::after,
.industry-trigger::after,
.reset-btn::after,
.apply-btn::after {
  border: 0;
}

.mode-tab {
  position: relative;
  display: inline-flex;
  flex: 0 0 auto;
  width: auto;
  min-width: 0;
  margin: 0;
  padding: 0;
  background: transparent;
}

.mode-tab-hover,
.upload-tile-hover,
.remove-btn-active,
.settings-option-hover,
.visibility-option-hover,
.submit-btn-hover,
.location-trigger-hover,
.industry-trigger-hover,
.reset-btn-active,
.apply-btn-active {
  opacity: 0.88;
}

.mode-tab-label {
  display: block;
  color: #94a3b8;
  font-size: 30rpx;
  line-height: 40rpx;
  font-weight: 700;
}

.mode-tab-active .mode-tab-label {
  color: #1a57db;
}

.mode-tab-line {
  position: absolute;
  left: 0;
  right: 0;
  bottom: -6rpx;
  height: 4rpx;
  border-radius: 999rpx;
  background: #1a57db;
}

.card,
.venue-panel {
  margin-top: 20rpx;
  border-radius: 20rpx;
}

.card {
  background: #ffffff;
  box-shadow: 0 4rpx 16rpx rgba(15, 23, 42, 0.04);
}

.title-card {
  padding: 24rpx 28rpx;
}

.title-input {
  width: 100%;
  color: #0f172a;
  font-size: 32rpx;
  line-height: 44rpx;
  font-weight: 700;
}

.placeholder-title {
  color: #cbd5e1;
  font-size: 32rpx;
  line-height: 44rpx;
  font-weight: 700;
}

.editor-card {
  padding: 24rpx 28rpx;
}

.desc-input {
  width: 100%;
  min-height: 160rpx;
  color: #475569;
  font-size: 28rpx;
  line-height: 40rpx;
}

.placeholder-body {
  color: #94a3b8;
  font-size: 28rpx;
  line-height: 40rpx;
}

.media-section {
  margin-top: 20rpx;
}

.media-label,
.settings-label {
  display: block;
  color: #94a3b8;
  font-size: 22rpx;
  line-height: 28rpx;
  font-weight: 700;
}

.media-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 12rpx;
  margin-top: 20rpx;
}

.media-item,
.upload-tile {
  width: 180rpx;
  height: 180rpx;
  border-radius: 20rpx;
}

.media-item {
  position: relative;
  overflow: hidden;
  background: #e2e8f0;
}

.media-image {
  width: 100%;
  height: 100%;
}

.remove-btn {
  position: absolute;
  top: 6rpx;
  right: 6rpx;
  width: 36rpx;
  height: 36rpx;
  border-radius: 999rpx;
  background: rgba(15, 23, 42, 0.66);
  color: #ffffff;
  font-size: 26rpx;
  line-height: 36rpx;
  text-align: center;
  padding: 0;
}

.upload-tile {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 6rpx;
  margin: 0;
  background: #f8fafc;
  border: 2rpx dashed #e2e8f0;
  color: #94a3b8;
}

.upload-icon {
  font-size: 38rpx;
  line-height: 38rpx;
  font-weight: 300;
}

.upload-text {
  font-size: 20rpx;
  line-height: 26rpx;
}

.venue-panel {
  padding: 24rpx 28rpx;
  background: #ffffff;
  box-shadow: 0 4rpx 16rpx rgba(15, 23, 42, 0.04);
}

.venue-head {
  display: flex;
  align-items: center;
  gap: 10rpx;
  margin-bottom: 16rpx;
}

.venue-head-mark {
  width: 16rpx;
  height: 16rpx;
  border-radius: 4rpx;
  background: #1a57db;
  box-shadow: 0 0 0 6rpx rgba(26, 87, 219, 0.12);
}

.venue-head-title {
  color: #0f172a;
  font-size: 28rpx;
  line-height: 38rpx;
  font-weight: 700;
}

.venue-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 24rpx;
  padding: 20rpx 0;
}

.venue-row-line {
  border-bottom: 2rpx solid rgba(203, 213, 225, 0.55);
}

.venue-label {
  color: #475569;
  font-size: 28rpx;
  line-height: 40rpx;
}

.venue-input {
  width: 180rpx;
  text-align: right;
  color: #0f172a;
  font-size: 28rpx;
  line-height: 40rpx;
  font-weight: 800;
}

.location-trigger {
  padding: 0;
  background: transparent;
}

.location-trigger-text {
  color: #1a57db;
  font-size: 28rpx;
  line-height: 40rpx;
  font-weight: 600;
}

.venue-card,
.tags-card,
.sync-card,
.settings-card,
.visibility-card {
  padding: 24rpx 28rpx;
}

.card-head {
  display: flex;
  align-items: center;
  justify-content: flex-start;
  gap: 20rpx;
}

.card-head-title {
  color: #0f172a;
  font-size: 28rpx;
  line-height: 38rpx;
  font-weight: 700;
}

.card-head-action {
  color: #1a57db;
  font-size: 24rpx;
  line-height: 34rpx;
  font-weight: 600;
}

.industry-trigger {
  margin-top: 20rpx;
  padding: 0 24rpx;
  height: 80rpx;
  border-radius: 16rpx;
  background: #f8fafc;
  border: 2rpx solid #e2e8f0;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.industry-trigger-content {
  min-width: 0;
  display: flex;
  align-items: center;
}

.sync-trigger-content {
  flex: 1;
}

.industry-selected-text {
  max-width: 100%;
  color: #1a57db;
  font-size: 24rpx;
  line-height: 36rpx;
  font-weight: 600;
}

.industry-trigger-placeholder {
  color: #94a3b8;
  font-size: 26rpx;
  line-height: 38rpx;
}

.industry-trigger-arrow {
  color: #94a3b8;
  font-size: 34rpx;
  line-height: 34rpx;
}

.sync-selected-text {
  color: #1e293b;
  font-size: 24rpx;
  line-height: 36rpx;
}

.sync-meta-text {
  display: block;
  margin-top: 12rpx;
  color: #94a3b8;
  font-size: 22rpx;
  line-height: 30rpx;
}

.filter-mask {
  position: fixed;
  inset: 0;
  z-index: 66;
  background: rgba(2, 6, 23, 0.45);
  display: flex;
  align-items: flex-end;
}

.filter-panel {
  width: 100%;
  border-radius: 24rpx 24rpx 0 0;
  background: #ffffff;
  padding: 28rpx 32rpx calc(28rpx + env(safe-area-inset-bottom));
}

.panel-head {
  display: flex;
  flex-direction: column;
  gap: 6rpx;
}

.panel-title {
  color: #0f172a;
  font-size: 32rpx;
  line-height: 42rpx;
  font-weight: 700;
}

.panel-subtitle {
  color: #64748b;
  font-size: 22rpx;
  line-height: 30rpx;
}

.section {
  margin-top: 24rpx;
}

.section-label {
  color: #334155;
  font-size: 24rpx;
  line-height: 32rpx;
  font-weight: 600;
}

.option-grid {
  margin-top: 16rpx;
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12rpx;
}

.circle-option-list {
  margin-top: 16rpx;
  display: flex;
  flex-direction: column;
  gap: 12rpx;
}

.circle-option {
  border-radius: 16rpx;
  border: 1rpx solid #e2e8f0;
  background: #f8fafc;
  padding: 18rpx 20rpx;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16rpx;
}

.circle-option-active {
  background: rgba(26, 87, 219, 0.08);
  border-color: rgba(26, 87, 219, 0.32);
}

.circle-option-main {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 4rpx;
}

.circle-option-name {
  color: #0f172a;
  font-size: 26rpx;
  line-height: 38rpx;
  font-weight: 700;
}

.circle-option-meta {
  color: #64748b;
  font-size: 22rpx;
  line-height: 30rpx;
}

.circle-option-check {
  width: 40rpx;
  height: 40rpx;
  border-radius: 999rpx;
  border: 2rpx solid #cbd5e1;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  background: #ffffff;
}

.circle-option-check-core {
  width: 16rpx;
  height: 16rpx;
  border-radius: 999rpx;
  background: transparent;
}

.circle-option-check-core-active {
  background: #1a57db;
}

.empty-circle-wrap {
  margin-top: 16rpx;
  padding: 28rpx 24rpx;
  border-radius: 18rpx;
  background: #f8fafc;
}

.empty-circle-text {
  color: #94a3b8;
  font-size: 24rpx;
  line-height: 34rpx;
}

.option-chip {
  min-height: 68rpx;
  border-radius: 14rpx;
  padding: 0 18rpx;
  border: 1rpx solid #e2e8f0;
  background: #f8fafc;
  display: flex;
  align-items: center;
  justify-content: center;
  text-align: center;
}

.option-chip-active {
  background: rgba(26, 87, 219, 0.1);
  border-color: rgba(26, 87, 219, 0.35);
}

.option-chip-text {
  color: #475569;
  font-size: 24rpx;
  line-height: 32rpx;
  font-weight: 500;
}

.option-chip-text-active {
  color: #1a57db;
  font-weight: 700;
}

.actions {
  margin-top: 24rpx;
  display: flex;
  align-items: center;
  gap: 12rpx;
}

.reset-btn,
.apply-btn {
  height: 72rpx;
  border-radius: 12rpx;
  font-size: 26rpx;
  line-height: 72rpx;
  font-weight: 700;
}

.reset-btn {
  flex: 1;
  background: #f1f5f9;
  color: #475569;
}

.apply-btn {
  flex: 2;
  background: #1a57db;
  color: #ffffff;
}

.settings-grid {
  display: flex;
  gap: 12rpx;
  margin-top: 20rpx;
}

.settings-option {
  flex: 1;
  height: 72rpx;
  border-radius: 14rpx;
  background: #ffffff;
  border: 2rpx solid #f1f5f9;
  color: #64748b;
  font-size: 24rpx;
  line-height: 68rpx;
  font-weight: 700;
  text-align: center;
}

.settings-option-active {
  background: #1a57db;
  border-color: #1a57db;
  color: #ffffff;
}

.visibility-subtitle {
  display: block;
  margin-top: 6rpx;
  color: #94a3b8;
  font-size: 20rpx;
  line-height: 26rpx;
}

.visibility-switch {
  display: flex;
  gap: 8rpx;
  margin-top: 20rpx;
  padding: 6rpx;
  border-radius: 14rpx;
  background: #f1f5f9;
}

.visibility-option {
  flex: 1;
  height: 60rpx;
  border-radius: 10rpx;
  background: transparent;
  color: #64748b;
  font-size: 22rpx;
  line-height: 60rpx;
  font-weight: 700;
  text-align: center;
}

.visibility-option-active {
  background: #ffffff;
  color: #1a57db;
  box-shadow: 0 4rpx 12rpx rgba(15, 23, 42, 0.06);
}

.bottom-bar {
  position: fixed;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 20;
  padding: 20rpx 32rpx calc(20rpx + env(safe-area-inset-bottom));
  background: rgba(255, 255, 255, 0.9);
  border-top: 2rpx solid rgba(226, 232, 240, 0.72);
}

.submit-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10rpx;
  width: 100%;
  height: 88rpx;
  border-radius: 20rpx;
  background: #1a57db;
  color: #ffffff;
  font-size: 30rpx;
  line-height: 40rpx;
  font-weight: 700;
  box-shadow: 0 12rpx 28rpx rgba(26, 87, 219, 0.18);
}

.submit-btn-arrow {
  font-size: 32rpx;
  line-height: 32rpx;
}

.submit-btn-disabled {
  background: #e5e7eb;
  color: #a1a1aa;
  box-shadow: none;
}

.loading-mask {
  position: fixed;
  inset: 0;
  z-index: 30;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(15, 23, 42, 0.18);
}

.loading-card {
  width: 260rpx;
  padding: 24rpx 20rpx;
  border-radius: 20rpx;
  background: rgba(255, 255, 255, 0.96);
  text-align: center;
}

.loading-title {
  display: block;
  color: #0f172a;
  font-size: 28rpx;
  line-height: 38rpx;
  font-weight: 700;
}

.loading-desc {
  display: block;
  margin-top: 8rpx;
  color: #64748b;
  font-size: 24rpx;
  line-height: 32rpx;
}
</style>
