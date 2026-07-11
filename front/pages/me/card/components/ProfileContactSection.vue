<template>
  <view class="contact-wrap">
    <view class="business-card-frame" @tap="onTapCard">
      <canvas
        id="contactBusinessCard"
        canvas-id="contactBusinessCard"
        class="business-card-canvas"
        :width="canvasWidth"
        :height="canvasHeight"
        :style="canvasStyle"
      ></canvas>
      <cover-view
        v-if="showAccessMask"
        class="business-card-cover-mask"
        @tap.stop="onTapLockedCard"
      >
        <cover-view class="cover-title-row">
          <cover-image class="cover-mask-icon" src="https://cos.cnptec.site/static/icon/suo.png" />
          <cover-view class="cover-mask-title">{{ maskTitle }}</cover-view>
        </cover-view>
        <cover-view v-if="maskDesc" class="cover-mask-desc">{{ maskDesc }}</cover-view>
      </cover-view>
    </view>

  </view>
</template>

<script setup>
import { computed, getCurrentInstance, nextTick, onMounted, onUnmounted, ref, watch } from 'vue'

const CARD_RATIO = 1.66
const CANVAS_ID = 'contactBusinessCard'

const props = defineProps({
  contact: {
    type: Object,
    default: () => ({})
  }
})

const emit = defineEmits(['unlock-contact'])

const instance = getCurrentInstance()
const canvasWidth = ref(0)
const canvasHeight = ref(0)
const avatarDrawPath = ref('')
const avatarImageSize = ref({ width: 0, height: 0 })
const miniappCodeDrawPath = ref('')
const isComponentAlive = ref(true)
let avatarRequestId = 0
let miniappCodeRequestId = 0

const canvasStyle = computed(() => {
  return `width: ${canvasWidth.value}px; height: ${canvasHeight.value}px;`
})

const hasVisibleContact = computed(() => {
  return Boolean(
    props.contact?.contactVisible && (props.contact?.displayPhone || props.contact?.displayWechat || props.contact?.displayEmail)
  )
})

const shouldShowPermissionMask = computed(() => {
  if (hasVisibleContact.value || props.contact?.isSelf) {
    return false
  }
  return true
})

const showAccessMask = computed(() => {
  return Boolean(shouldShowPermissionMask.value)
})

const maskedContactName = computed(() => {
  return String(props.contact?.name || '').trim() || '该用户'
})

const maskTitle = computed(() => {
  return `查看${maskedContactName.value}的联系方式`
})

const maskDesc = computed(() => {
  return '开通会员即可解锁'
})

const lockedTitle = computed(() => {
  return String(props.contact?.contactLockedReason || '').trim() || '暂时无法查看联系方式'
})

const profileName = computed(() => {
  return String(props.contact?.name || '').trim() || '未命名用户'
})

const companyLine = computed(() => String(props.contact?.companyName || '').trim())
const jobTitleLine = computed(() => String(props.contact?.jobTitle || '').trim())

const cityText = computed(() => String(props.contact?.cityName || '').trim() || '圈脉链个人名片')
const contactRows = computed(() => {
  const hiddenValue = '*******'
  if (showAccessMask.value) {
    return [
      ['微信：', hiddenValue],
      ['手机：', hiddenValue],
      ['邮箱：', hiddenValue]
    ]
  }

  return [
    ['微信：', String(props.contact?.displayWechat || '').trim() || hiddenValue],
    ['手机：', String(props.contact?.displayPhone || '').trim() || hiddenValue],
    ['邮箱：', String(props.contact?.displayEmail || '').trim() || hiddenValue]
  ]
})

function measureCanvas() {
  nextTick(() => {
    if (!isComponentAlive.value) {
      return
    }
    const query = uni.createSelectorQuery().in(instance?.proxy)
    query
      .select('.business-card-frame')
      .boundingClientRect((rect) => {
        if (!isComponentAlive.value) {
          return
        }
        const width = Number(rect?.width || 0) || 280
        canvasWidth.value = width
        canvasHeight.value = Math.round(width / CARD_RATIO)
        nextTick(drawBusinessCard)
      })
      .exec()
  })
}

function drawRoundRect(ctx, x, y, width, height, radius) {
  const r = Math.min(radius, width / 2, height / 2)
  ctx.beginPath()
  ctx.moveTo(x + r, y)
  ctx.lineTo(x + width - r, y)
  ctx.quadraticCurveTo(x + width, y, x + width, y + r)
  ctx.lineTo(x + width, y + height - r)
  ctx.quadraticCurveTo(x + width, y + height, x + width - r, y + height)
  ctx.lineTo(x + r, y + height)
  ctx.quadraticCurveTo(x, y + height, x, y + height - r)
  ctx.lineTo(x, y + r)
  ctx.quadraticCurveTo(x, y, x + r, y)
  ctx.closePath()
}

function fillRoundRect(ctx, x, y, width, height, radius, color) {
  drawRoundRect(ctx, x, y, width, height, radius)
  ctx.setFillStyle(color)
  ctx.fill()
}

function drawTextLine(ctx, text, x, y, maxWidth, options = {}) {
  const fontSize = Number(options.fontSize || 14)
  const fontWeight = options.fontWeight || 'normal'
  const color = options.color || '#172033'
  const suffix = options.suffix || '...'
  let content = String(text || '').trim()

  ctx.setFontSize(fontSize)
  ctx.font = `${fontWeight} ${fontSize}px sans-serif`
  ctx.setFillStyle(color)
  ctx.setTextBaseline('top')

  if (!content) {
    return
  }

  while (content.length > 1 && ctx.measureText(`${content}${suffix}`).width > maxWidth) {
    content = content.slice(0, -1)
  }

  const finalText = content === String(text || '').trim() ? content : `${content}${suffix}`
  ctx.fillText(finalText, x, y)
}

function drawWrappedText(ctx, text, x, y, maxWidth, lineHeight, maxLines, options = {}) {
  const source = String(text || '').trim()
  if (!source) {
    return
  }

  let line = ''
  let lineCount = 0
  ctx.setFontSize(Number(options.fontSize || 12))
  ctx.setFillStyle(options.color || '#66758A')
  ctx.setTextBaseline('top')

  for (let i = 0; i < source.length; i += 1) {
    const nextLine = `${line}${source[i]}`
    if (ctx.measureText(nextLine).width > maxWidth && line) {
      drawTextLine(ctx, line, x, y + lineCount * lineHeight, maxWidth, options)
      line = source[i]
      lineCount += 1
      if (lineCount >= maxLines - 1) {
        break
      }
    } else {
      line = nextLine
    }
  }

  if (line && lineCount < maxLines) {
    drawTextLine(ctx, line, x, y + lineCount * lineHeight, maxWidth, options)
  }
}

function drawPaperTexture(ctx, width, height) {
  ctx.setStrokeStyle('#EDF1F6')
  ctx.setLineWidth(0.6)
  for (let i = 0; i < 28; i += 1) {
    const x = (i * 37) % width
    const y = (i * 19) % height
    ctx.beginPath()
    ctx.moveTo(x, y)
    ctx.lineTo(Math.min(width, x + 34), y + 2)
    ctx.stroke()
  }
}

function drawAvatarFallback(ctx, x, y, size) {
  ctx.save()
  fillRoundRect(ctx, x, y, size, size, 12, '#EEF5FF')
  ctx.setFillStyle('#174EA6')
  ctx.setFontSize(18)
  ctx.font = '700 18px sans-serif'
  ctx.setTextAlign('center')
  ctx.setTextBaseline('middle')
  ctx.fillText(profileName.value.slice(0, 1) || '名', x + size / 2, y + size / 2)
  ctx.restore()
}

function drawCardAvatar(ctx, x, y, size) {
  const path = String(avatarDrawPath.value || '').trim()
  const sourceWidth = Number(avatarImageSize.value?.width || 0)
  const sourceHeight = Number(avatarImageSize.value?.height || 0)
  ctx.save()
  drawRoundRect(ctx, x, y, size, size, 12)
  ctx.clip()
  if (path && sourceWidth > 0 && sourceHeight > 0) {
    const scale = Math.max(size / sourceWidth, size / sourceHeight)
    const drawWidth = sourceWidth * scale
    const drawHeight = sourceHeight * scale
    const drawX = x + (size - drawWidth) / 2
    const drawY = y + (size - drawHeight) / 2
    ctx.drawImage(path, drawX, drawY, drawWidth, drawHeight)
  } else if (path) {
    ctx.drawImage(path, x, y, size, size)
  } else {
    ctx.restore()
    drawAvatarFallback(ctx, x, y, size)
    return
  }
  ctx.restore()
}

function drawInlineText(ctx, text, x, centerY, maxWidth, options = {}) {
  const fontSize = Number(options.fontSize || 10)
  const fontWeight = options.fontWeight || 'normal'
  const color = options.color || '#172033'
  const suffix = options.suffix ?? '...'
  let content = String(text || '').trim()

  ctx.setFontSize(fontSize)
  ctx.font = `${fontWeight} ${fontSize}px sans-serif`
  ctx.setFillStyle(color)
  ctx.setTextBaseline('middle')

  if (!content) {
    return
  }

  if (suffix) {
    while (content.length > 1 && ctx.measureText(`${content}${suffix}`).width > maxWidth) {
      content = content.slice(0, -1)
    }
  }

  const finalText = suffix && content !== String(text || '').trim() ? `${content}${suffix}` : content
  ctx.fillText(finalText, x, centerY)
}

function drawContactRow(ctx, label, value, x, y, maxWidth) {
  const rowHeight = 16
  const fontSize = 10
  const centerY = y + rowHeight / 2
  const labelWidth = 38
  drawInlineText(ctx, label, x, centerY, labelWidth, {
    fontSize,
    fontWeight: '700',
    color: '#172033',
    suffix: ''
  })
  drawInlineText(ctx, value, x + labelWidth, centerY, maxWidth - labelWidth, {
    fontSize,
    color: '#172033'
  })
}

function drawMiniappCode(ctx, x, y, size) {
  const path = String(miniappCodeDrawPath.value || '').trim()
  if (!path) {
    return
  }

  fillRoundRect(ctx, x - 7, y - 7, size + 14, size + 14, 10, '#F8FAFD')
  ctx.drawImage(path, x, y, size, size)
}

function splitTextLines(ctx, text, maxWidth, maxLines) {
  const source = String(text || '').trim()
  const lines = []
  let line = ''

  for (let i = 0; i < source.length; i += 1) {
    const nextLine = `${line}${source[i]}`
    if (ctx.measureText(nextLine).width > maxWidth && line) {
      lines.push(line)
      line = source[i]
      if (lines.length >= maxLines - 1) {
        break
      }
    } else {
      line = nextLine
    }
  }

  if (line && lines.length < maxLines) {
    lines.push(line)
  }

  return lines
}

function drawCenteredTextLines(ctx, text, centerX, y, maxWidth, options = {}) {
  const fontSize = Number(options.fontSize || 12)
  const fontWeight = options.fontWeight || 'normal'
  const color = options.color || '#172033'
  const lineHeight = Number(options.lineHeight || fontSize + 6)
  const maxLines = Number(options.maxLines || 2)
  ctx.setFontSize(fontSize)
  ctx.font = `${fontWeight} ${fontSize}px sans-serif`
  ctx.setFillStyle(color)
  ctx.setTextAlign('center')
  ctx.setTextBaseline('top')
  const lines = splitTextLines(ctx, text, maxWidth, maxLines)
  lines.forEach((line, index) => {
    ctx.fillText(line, centerX, y + index * lineHeight)
  })
  ctx.setTextAlign('left')
  return lines.length * lineHeight
}

function drawLockGlyph(ctx, x, y, size) {
  const bodyY = y + size * 0.42
  const bodyHeight = size * 0.48
  fillRoundRect(ctx, x, bodyY, size, bodyHeight, size * 0.14, '#172033')
  ctx.setStrokeStyle('#172033')
  ctx.setLineWidth(Math.max(2, size * 0.12))
  ctx.beginPath()
  ctx.arc(x + size / 2, bodyY, size * 0.28, Math.PI, Math.PI * 2)
  ctx.stroke()
  ctx.setFillStyle('#ffffff')
  ctx.beginPath()
  ctx.arc(x + size / 2, bodyY + bodyHeight * 0.43, size * 0.07, 0, Math.PI * 2)
  ctx.fill()
  ctx.fillRect(x + size / 2 - size * 0.035, bodyY + bodyHeight * 0.47, size * 0.07, size * 0.18)
}

function drawCanvasAccessMask(ctx, width, height) {
  const title = String(maskTitle.value || '').trim()
  const desc = String(maskDesc.value || '').trim()
  const centerX = width / 2
  const titleFontSize = Math.max(12, Math.round(width * 0.038))
  const descFontSize = Math.max(10, Math.round(width * 0.031))
  const maxTextWidth = width * 0.76
  const lockSize = Math.max(15, Math.round(width * 0.045))
  const rowGap = 8
  const titleLineHeight = titleFontSize + 6
  const descLineHeight = descFontSize + 5

  ctx.save()
  ctx.setGlobalAlpha(0.86)
  fillRoundRect(ctx, 0, 0, width, height, 18, '#F8FAFD')
  ctx.setGlobalAlpha(0.22)
  fillRoundRect(ctx, width * 0.08, height * 0.12, width * 0.84, height * 0.76, 22, '#FFFFFF')
  ctx.setGlobalAlpha(1)

  ctx.setFontSize(titleFontSize)
  ctx.font = `700 ${titleFontSize}px sans-serif`
  const titleLines = splitTextLines(ctx, title, maxTextWidth - lockSize - rowGap, 2)
  const titleBlockHeight = Math.max(lockSize, titleLines.length * titleLineHeight)
  const descHeight = desc ? descLineHeight * splitTextLines(ctx, desc, maxTextWidth, 2).length : 0
  const blockGap = desc ? 10 : 0
  const blockHeight = titleBlockHeight + blockGap + descHeight
  let startY = Math.max(20, (height - blockHeight) / 2)

  if (titleLines.length <= 1) {
    const titleText = titleLines[0] || title
    const titleWidth = ctx.measureText(titleText).width
    const rowWidth = lockSize + rowGap + titleWidth
    const rowX = centerX - rowWidth / 2
    drawLockGlyph(ctx, rowX, startY + (titleBlockHeight - lockSize) / 2, lockSize)
    ctx.setFillStyle('#172033')
    ctx.setTextAlign('left')
    ctx.setTextBaseline('middle')
    ctx.fillText(titleText, rowX + lockSize + rowGap, startY + titleBlockHeight / 2)
  } else {
    drawLockGlyph(ctx, centerX - lockSize / 2, startY, lockSize)
    drawCenteredTextLines(ctx, title, centerX, startY + lockSize + 6, maxTextWidth, {
      fontSize: titleFontSize,
      fontWeight: '700',
      color: '#172033',
      lineHeight: titleLineHeight,
      maxLines: 2
    })
    startY += lockSize + 6
  }

  if (desc) {
    drawCenteredTextLines(ctx, desc, centerX, startY + titleBlockHeight + blockGap, maxTextWidth, {
      fontSize: descFontSize,
      fontWeight: '500',
      color: '#66758a',
      lineHeight: descLineHeight,
      maxLines: 2
    })
  }

  ctx.restore()
}

function drawBusinessCard() {
  if (!isComponentAlive.value) {
    return
  }
  if (!canvasWidth.value || !canvasHeight.value) {
    return
  }

  const ctx = uni.createCanvasContext(CANVAS_ID, instance?.proxy)
  const width = canvasWidth.value
  const height = canvasHeight.value
  const margin = Math.max(20, Math.round(width * 0.075))
  const avatarSize = Math.min(86, Math.round(width * 0.24))
  const brandWidth = avatarSize
  const brandX = width - margin - brandWidth
  const topY = Math.max(20, Math.round(height * 0.12))
  const contactStartY = Math.round(height * 0.55)
  const qrSize = Math.min(54, Math.round(width * 0.15), height - contactStartY - 18)
  const qrX = width - margin - qrSize
  const qrY = height - margin - qrSize
  const leftColumnWidth = qrX - margin * 2

  ctx.clearRect(0, 0, width, height)
  fillRoundRect(ctx, 0, 0, width, height, 18, '#FBFCFE')
  drawPaperTexture(ctx, width, height)

  drawTextLine(ctx, profileName.value, margin, topY, brandX - margin - 12, {
    fontSize: Math.max(18, Math.round(width * 0.055)),
    fontWeight: '700',
    color: '#172033'
  })
  const subLineFontSize = Math.max(10, Math.round(width * 0.031))
  const subLineWidth = brandX - margin - 12
  let subLineY = topY + 27
  if (companyLine.value) {
    drawTextLine(ctx, companyLine.value, margin + 1, subLineY, subLineWidth, {
      fontSize: subLineFontSize,
      color: '#374151'
    })
    subLineY += subLineFontSize + 7
  }
  if (jobTitleLine.value) {
    drawTextLine(ctx, jobTitleLine.value, margin + 1, subLineY, subLineWidth, {
      fontSize: subLineFontSize,
      color: '#374151'
    })
  }
  drawCardAvatar(ctx, brandX, topY - 10, avatarSize)

  contactRows.value.forEach(([label, value], index) => {
    drawContactRow(ctx, label, value, margin, contactStartY + index * 25, leftColumnWidth)
  })

  drawMiniappCode(ctx, qrX, qrY, qrSize)
  ctx.draw()
}

function copyValue(value, successTitle) {
  const normalized = String(value || '').trim()
  if (!normalized) {
    return
  }
  uni.setClipboardData({
    data: normalized,
    success: () => {
      uni.showToast({
        title: successTitle,
        icon: 'none'
      })
    }
  })
}

function onTapCard() {
  const actions = []
  if (hasVisibleContact.value && props.contact?.displayWechat) {
    actions.push({ label: '复制微信号', value: props.contact.displayWechat, title: '展示微信号已复制' })
  }
  if (hasVisibleContact.value && props.contact?.displayPhone) {
    actions.push({ label: '复制手机号', value: props.contact.displayPhone, title: '展示手机号已复制' })
  }
  if (hasVisibleContact.value && props.contact?.displayEmail) {
    actions.push({ label: '复制邮箱', value: props.contact.displayEmail, title: '展示邮箱已复制' })
  }

  if (!actions.length) {
    if (showAccessMask.value) {
      emit('unlock-contact')
      return
    }

    uni.showToast({
      title: lockedTitle.value,
      icon: 'none'
    })
    return
  }

  uni.showActionSheet({
    itemList: actions.map((item) => item.label),
    success: (res) => {
      const item = actions[Number(res?.tapIndex || 0)]
      if (item) {
        copyValue(item.value, item.title)
      }
    }
  })
}

function onTapLockedCard() {
  emit('unlock-contact')
}

onMounted(() => {
  isComponentAlive.value = true
  measureCanvas()
})

onUnmounted(() => {
  isComponentAlive.value = false
  avatarRequestId += 1
  miniappCodeRequestId += 1
  avatarDrawPath.value = ''
  avatarImageSize.value = { width: 0, height: 0 }
  miniappCodeDrawPath.value = ''
  canvasWidth.value = 0
  canvasHeight.value = 0
})

watch(
  () => props.contact,
  () => {
    nextTick(() => {
      if (!canvasWidth.value) {
        measureCanvas()
        return
      }
      drawBusinessCard()
    })
  },
  { deep: true }
)

watch(
  () => props.contact?.avatarUrl,
  (avatarUrl) => {
    const requestId = avatarRequestId + 1
    avatarRequestId = requestId
    const source = String(avatarUrl || '').trim()
    avatarDrawPath.value = ''
    avatarImageSize.value = { width: 0, height: 0 }
    if (!source) {
      drawBusinessCard()
      return
    }
    uni.getImageInfo({
      src: source,
      success: (res) => {
        if (!isComponentAlive.value || requestId !== avatarRequestId) {
          return
        }
        avatarDrawPath.value = String(res?.path || source)
        avatarImageSize.value = {
          width: Number(res?.width || 0),
          height: Number(res?.height || 0)
        }
        drawBusinessCard()
      },
      fail: () => {
        if (!isComponentAlive.value || requestId !== avatarRequestId) {
          return
        }
        avatarDrawPath.value = ''
        avatarImageSize.value = { width: 0, height: 0 }
        drawBusinessCard()
      }
    })
  },
  { immediate: true }
)

watch(
  () => props.contact?.miniappCodeUrl,
  (miniappCodeUrl) => {
    const requestId = miniappCodeRequestId + 1
    miniappCodeRequestId = requestId
    const source = String(miniappCodeUrl || '').trim()
    miniappCodeDrawPath.value = ''
    if (!source) {
      drawBusinessCard()
      return
    }
    uni.getImageInfo({
      src: source,
      success: (res) => {
        if (!isComponentAlive.value || requestId !== miniappCodeRequestId) {
          return
        }
        miniappCodeDrawPath.value = String(res?.path || source)
        drawBusinessCard()
      },
      fail: () => {
        if (!isComponentAlive.value || requestId !== miniappCodeRequestId) {
          return
        }
        miniappCodeDrawPath.value = ''
        drawBusinessCard()
      }
    })
  },
  { immediate: true }
)
</script>

<style scoped>
.contact-wrap {
  background: #ffffff;
  padding: 0 32rpx 32rpx;
  display: flex;
  flex-direction: column;
  gap: 16rpx;
}

.business-card-frame {
  position: relative;
  width: 100%;
  border-radius: 16rpx;
  background: #fbfcfe;
  box-shadow: 0 4rpx 12rpx rgba(0, 0, 0, 0.08), 0 2rpx 4rpx rgba(0, 0, 0, 0.04);
  overflow: hidden;
}

.business-card-canvas {
  display: block;
}

.business-card-cover-mask {
  position: absolute;
  left: 0;
  right: 0;
  top: 0;
  bottom: 0;
  z-index: 5;
  box-sizing: border-box;
  padding: 24rpx;
  background: rgba(248, 250, 253, 0.9);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}

.cover-title-row {
  max-width: 88%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.cover-mask-icon {
  width: 46rpx;
  height: 46rpx;
  margin-right: 10rpx;
}

.cover-mask-title {
  color: #172033;
  font-size: 30rpx;
  line-height: 34rpx;
  font-weight: 700;
  text-align: center;
  white-space: normal;
}

.cover-mask-desc {
  max-width: 88%;
  margin-top: 20rpx;
  color: #333;
  font-size: 28rpx;
  line-height: 32rpx;
  font-weight: 600;
  text-align: center;
  white-space: normal;
}

</style>
