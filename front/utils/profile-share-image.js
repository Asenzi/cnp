// 微信会话分享卡片使用 5:4 横图，保证头像和文字完整显示。
const CANVAS_WIDTH = 750
const CANVAS_HEIGHT = 600

function getCanvasNode(canvasId) {
  return new Promise((resolve, reject) => {
    uni.createSelectorQuery().select(`#${canvasId}`).fields({node:true, size:true}).exec(result => {
      const canvas = result?.[0]?.node
      if (!canvas || typeof canvas.getContext !== 'function') {
        reject(new Error('分享画布尚未就绪，请重新进入页面'))
        return
      }
      canvas.width = CANVAS_WIDTH * 2
      canvas.height = CANVAS_HEIGHT * 2
      resolve(canvas)
    })
  })
}

function loadCanvasImage(canvas, src, required = false) {
  if (!src) return required ? Promise.reject(new Error('分享素材路径为空')) : Promise.resolve(null)
  return new Promise((resolve, reject) => {
    const load = path => {
      const image = canvas.createImage()
      image.onload = () => resolve({path:image, width:image.width, height:image.height})
      image.onerror = () => required ? reject(new Error(`分享素材加载失败：${src}`)) : resolve(null)
      image.src = path.startsWith('static/') ? `/${path}` : path
    }
    if (/^https?:\/\//i.test(src)) {
      uni.getImageInfo({src, success:info => load(info.path), fail:() => required ? reject(new Error('分享图片下载失败')) : resolve(null)})
    } else {
      load(src)
    }
  })
}

function roundRect(ctx, x, y, width, height, radius) {
  ctx.beginPath()
  ctx.moveTo(x + radius, y)
  ctx.lineTo(x + width - radius, y)
  ctx.arc(x + width - radius, y + radius, radius, -Math.PI / 2, 0)
  ctx.lineTo(x + width, y + height - radius)
  ctx.arc(x + width - radius, y + height - radius, radius, 0, Math.PI / 2)
  ctx.lineTo(x + radius, y + height)
  ctx.arc(x + radius, y + height - radius, radius, Math.PI / 2, Math.PI)
  ctx.lineTo(x, y + radius)
  ctx.arc(x + radius, y + radius, radius, Math.PI, Math.PI * 1.5)
  ctx.closePath()
}

function truncateText(ctx, value, maxWidth) {
  const text = String(value || '').trim()
  if (ctx.measureText(text).width <= maxWidth) return text
  const characters = Array.from(text)
  while (characters.length && ctx.measureText(`${characters.join('')}…`).width > maxWidth) {
    characters.pop()
  }
  return `${characters.join('')}…`
}

function wrapText(ctx, value, maxWidth, maxLines) {
  const characters = Array.from(String(value || '').replace(/\s+/g, ' ').trim())
  const lines = []
  let line = ''
  for (let index = 0; index < characters.length; index += 1) {
    const nextLine = line + characters[index]
    if (ctx.measureText(nextLine).width > maxWidth && line) {
      if (lines.length === maxLines - 1) {
        lines.push(truncateText(ctx, line + characters.slice(index).join(''), maxWidth))
        return lines
      }
      lines.push(line)
      line = characters[index]
    } else {
      line = nextLine
    }
  }
  if (line) lines.push(line)
  return lines
}

export async function generateProfileShareImage(userData, options = {}) {
  const canvasId = options.canvasId || 'shareCanvas'
  const canvas = await getCanvasNode(canvasId)
  const assetNames = ['brand', 'accent', 'growth', 'company', 'job', 'verified-label', 'owner-label', 'quote']
  const [avatar, memberIcon, ...assetImages] = await Promise.all([
    loadCanvasImage(canvas, userData.avatarUrl),
    userData.isMember === true ? loadCanvasImage(canvas, '/static/icon/mennber1.png', true) : Promise.resolve(null),
    ...assetNames.map((name) => loadCanvasImage(canvas, `/static/profile-share/${name}.png`, true))
  ])
  const assets = Object.fromEntries(assetNames.map((name, index) => [name, assetImages[index]]))
  const ctx = canvas.getContext('2d')
  ctx.scale(2, 2)
  ctx.fillStyle = '#f7fbff'
  ctx.fillRect(0, 0, CANVAS_WIDTH, CANVAS_HEIGHT)
  ctx.fillStyle = '#ffffff'
  roundRect(ctx, 20, 20, 710, 560, 18)
  ctx.fill()
  ctx.strokeStyle = '#dceaff'
  ctx.lineWidth = 1
  ctx.stroke()
  ctx.save()
  roundRect(ctx, 21, 21, 708, 558, 17)
  ctx.clip()

  if (assets.accent) ctx.drawImage(assets.accent.path, 442, 24, 287, 237.5)
  if (assets.brand) ctx.drawImage(assets.brand.path, 48, 39, 78, 60)
  ctx.strokeStyle = '#c4ddff'
  ctx.beginPath()
  ctx.moveTo(143, 46)
  ctx.lineTo(143, 84)
  ctx.stroke()
  ctx.textAlign = 'left'
  ctx.textBaseline = 'alphabetic'
  ctx.fillStyle = '#0b172d'
  ctx.font = 'bold 36px sans-serif'
  ctx.fillText('圈脉链', 164, 78)
  ctx.fillStyle = '#7e8ca8'
  ctx.font = '19px sans-serif'
  ctx.fillText('连接人脉 · 汇聚资源 · 成就更多可能', 164, 108)

  const avatarX = 52
  const avatarY = 146
  const avatarSize = 158
  ctx.fillStyle = '#ffffff'
  ctx.beginPath()
  ctx.arc(131, 225, 85, 0, 2 * Math.PI)
  ctx.fill()
  ctx.strokeStyle = '#d8eaff'
  ctx.lineWidth = 1.5
  ctx.stroke()
  ctx.save()
  ctx.beginPath()
  ctx.arc(131, 225, 79, 0, 2 * Math.PI)
  ctx.clip()
  if (avatar && avatar.width > 0 && avatar.height > 0) {
    const scale = Math.max(avatarSize / avatar.width, avatarSize / avatar.height)
    const width = avatar.width * scale
    const height = avatar.height * scale
    ctx.drawImage(avatar.path, avatarX + (avatarSize - width) / 2, avatarY + (avatarSize - height) / 2, width, height)
  } else {
    ctx.fillStyle = '#eaf3ff'
    ctx.fillRect(avatarX, avatarY, avatarSize, avatarSize)
    ctx.fillStyle = '#1684f5'
    ctx.font = 'bold 56px sans-serif'
    ctx.textAlign = 'center'
    ctx.fillText(Array.from(String(userData.nickname || '友'))[0], 131, 245)
  }
  ctx.restore()

  ctx.fillStyle = '#0b172d'
  ctx.font = 'bold 46px sans-serif'
  const nameLines = wrapText(ctx, userData.nickname || '未命名用户', 290, 2)
  nameLines.forEach((line, index) => {
    ctx.fillText(line, 246, (nameLines.length > 1 ? 166 : 203) + index * 53)
  })
  let badgeX = 246
  const badgeY = 259
  const badgeHeight = 40
  if (userData.isVerified === true && assets['verified-label']) {
    ctx.drawImage(assets['verified-label'].path, badgeX, badgeY, 121, badgeHeight)
    badgeX += 129
  }
  if (userData.isMember === true) {
    ctx.fillStyle = '#edf3ff'
    roundRect(ctx, badgeX, badgeY, 102, badgeHeight, 18)
    ctx.fill()
    if (memberIcon) ctx.drawImage(memberIcon.path, badgeX + 8, badgeY + 7, 26, 26)
    ctx.fillStyle = '#477cff'
    ctx.font = '25px sans-serif'
    ctx.fillText('会员', badgeX + 39, badgeY + 30)
    badgeX += 110
  }
  if (userData.isCircleOwner === true && assets['owner-label']) {
    ctx.drawImage(assets['owner-label'].path, badgeX, badgeY, 101, badgeHeight)
  }

  ctx.strokeStyle = '#deebfc'
  ctx.lineWidth = 1
  ctx.beginPath()
  ctx.moveTo(50, 333)
  ctx.lineTo(700, 333)
  ctx.stroke()
  ctx.beginPath()
  ctx.moveTo(467, 353)
  ctx.lineTo(467, 418)
  ctx.stroke()
  if (assets.company) ctx.drawImage(assets.company.path, 50, 354, 53, 53)
  if (assets.job) ctx.drawImage(assets.job.path, 490, 354, 53, 53)
  ctx.fillStyle = '#7e8ca8'
  ctx.font = '22px sans-serif'
  ctx.fillText('所在公司', 122, 373)
  ctx.fillText('职位', 560, 373)
  ctx.fillStyle = '#0b172d'
  ctx.font = 'bold 27px sans-serif'
  ctx.fillText(truncateText(ctx, userData.company || '暂未填写', 325), 122, 409)
  ctx.fillText(truncateText(ctx, userData.jobTitle || '暂未填写', 140), 560, 409)

  const quoteBackground = ctx.createLinearGradient(44, 450, 706, 566)
  quoteBackground.addColorStop(0, '#f0f8ff')
  quoteBackground.addColorStop(1, '#e9f4ff')
  ctx.fillStyle = quoteBackground
  roundRect(ctx, 44, 450, 662, 116, 12)
  ctx.fill()
  ctx.save()
  roundRect(ctx, 44, 450, 662, 116, 12)
  ctx.clip()
  if (assets.growth) ctx.drawImage(assets.growth.path, 442, 459, 264, 107)
  ctx.restore()
  if (assets.quote) ctx.drawImage(assets.quote.path, 64, 468, 33, 29)
  ctx.fillStyle = '#102e63'
  ctx.font = 'bold 27px sans-serif'
  const bio = '找人脉、找资源、找商机、商务社交就上圈脉链。'
  wrapText(ctx, bio, 460, 2).forEach((line, index) => {
    ctx.fillText(line, 118, 498 + index * 40)
  })
  ctx.restore()

  return new Promise((resolve, reject) => {
    uni.canvasToTempFilePath({
        canvas,
        x: 0,
        y: 0,
        width: CANVAS_WIDTH * 2,
        height: CANVAS_HEIGHT * 2,
        destWidth: CANVAS_WIDTH * 2,
        destHeight: CANVAS_HEIGHT * 2,
        fileType: 'png',
        success: (result) => resolve(result.tempFilePath),
        fail: reject
      })
  })
}
