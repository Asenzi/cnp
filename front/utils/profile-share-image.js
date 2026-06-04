/**
 * 生成个人名片分享图 - 紧凑版
 */

// 下载网络图片到本地
function downloadImage(url) {
  return new Promise((resolve, reject) => {
    if (!url || !url.startsWith('http')) {
      resolve('')
      return
    }

    uni.downloadFile({
      url: url,
      success: (res) => {
        if (res.statusCode === 200) {
          resolve(res.tempFilePath)
        } else {
          resolve('')
        }
      },
      fail: () => {
        resolve('')
      }
    })
  })
}

// 绘制圆角矩形
function drawRoundRect(ctx, x, y, width, height, radius) {
  ctx.beginPath()
  ctx.moveTo(x + radius, y)
  ctx.lineTo(x + width - radius, y)
  ctx.arc(x + width - radius, y + radius, radius, 1.5 * Math.PI, 2 * Math.PI)
  ctx.lineTo(x + width, y + height - radius)
  ctx.arc(x + width - radius, y + height - radius, radius, 0, 0.5 * Math.PI)
  ctx.lineTo(x + radius, y + height)
  ctx.arc(x + radius, y + height - radius, radius, 0.5 * Math.PI, Math.PI)
  ctx.lineTo(x, y + radius)
  ctx.arc(x + radius, y + radius, radius, Math.PI, 1.5 * Math.PI)
  ctx.closePath()
}

// 绘制圆形头像
function drawCircleAvatar(ctx, imagePath, x, y, radius) {
  ctx.save()
  ctx.beginPath()
  ctx.arc(x + radius, y + radius, radius, 0, 2 * Math.PI)
  ctx.clip()
  ctx.drawImage(imagePath, x, y, radius * 2, radius * 2)
  ctx.restore()
}

// 文字截断
function truncateText(ctx, text, maxWidth) {
  if (!text) return ''

  let width = ctx.measureText(text).width
  if (width <= maxWidth) return text

  let truncated = text
  while (width > maxWidth && truncated.length > 0) {
    truncated = truncated.substring(0, truncated.length - 1)
    width = ctx.measureText(truncated + '...').width
  }

  return truncated + '...'
}

// 文字换行
function wrapText(ctx, text, maxWidth, maxLines = 2) {
  if (!text) return []

  const lines = []
  let currentLine = ''

  for (let i = 0; i < text.length; i++) {
    const testLine = currentLine + text[i]
    const metrics = ctx.measureText(testLine)

    if (metrics.width > maxWidth && currentLine) {
      lines.push(currentLine)
      if (lines.length >= maxLines) {
        break
      }
      currentLine = text[i]
    } else {
      currentLine = testLine
    }
  }

  if (currentLine && lines.length < maxLines) {
    lines.push(currentLine)
  }

  // 如果超出行数，最后一行加省略号
  if (lines.length === maxLines && currentLine !== text) {
    lines[lines.length - 1] = lines[lines.length - 1].substring(0, lines[lines.length - 1].length - 2) + '...'
  }

  return lines
}

/**
 * 生成个人名片分享图
 * @param {Object} userData - 用户数据
 */
export async function generateProfileShareImage(userData) {
  return new Promise(async (resolve, reject) => {
    try {
      const ctx = uni.createCanvasContext('shareCanvas')

      const canvasWidth = 750
      const canvasHeight = 900
      const padding = 40

      // 1. 绘制白色背景
      ctx.fillStyle = '#ffffff'
      ctx.fillRect(0, 0, canvasWidth, canvasHeight)

      // 2. 绘制顶部蓝色条
      ctx.fillStyle = '#2563eb'
      ctx.fillRect(0, 0, canvasWidth, 8)

      // 3. 绘制头像和基本信息区域
      const topPadding = 50
      const avatarSize = 140
      const avatarX = padding + 10
      const avatarY = topPadding

      // 下载并绘制头像
      let localAvatarPath = ''
      if (userData.avatarUrl) {
        localAvatarPath = await downloadImage(userData.avatarUrl)
      }

      // 获取图片实际尺寸
      let imgWidth = avatarSize
      let imgHeight = avatarSize

      if (localAvatarPath) {
        try {
          const imgInfo = await new Promise((resolve, reject) => {
            uni.getImageInfo({
              src: localAvatarPath,
              success: resolve,
              fail: reject
            })
          })
          imgWidth = imgInfo.width
          imgHeight = imgInfo.height
        } catch (err) {
          console.log('获取图片信息失败，使用默认尺寸')
        }
      }

      if (localAvatarPath) {
        ctx.save()

        // 创建圆形裁剪区域
        const centerX = avatarX + avatarSize / 2
        const centerY = avatarY + avatarSize / 2
        const radius = avatarSize / 2

        ctx.beginPath()
        ctx.arc(centerX, centerY, radius, 0, 2 * Math.PI)
        ctx.closePath()
        ctx.clip()

        // 计算居中裁剪参数
        const scale = Math.max(avatarSize / imgWidth, avatarSize / imgHeight)
        const scaledWidth = imgWidth * scale
        const scaledHeight = imgHeight * scale
        const offsetX = avatarX + (avatarSize - scaledWidth) / 2
        const offsetY = avatarY + (avatarSize - scaledHeight) / 2

        // 绘制头像 - 保持比例，居中裁剪
        ctx.drawImage(localAvatarPath, offsetX, offsetY, scaledWidth, scaledHeight)

        ctx.restore()
      } else {
        // 占位头像
        ctx.fillStyle = '#f3f4f6'
        ctx.beginPath()
        ctx.arc(avatarX + avatarSize / 2, avatarY + avatarSize / 2, avatarSize / 2, 0, 2 * Math.PI)
        ctx.fill()
      }

      // 4. 右侧基本信息
      const infoX = avatarX + avatarSize + 35
      const infoWidth = canvasWidth - infoX - padding
      let infoY = avatarY + 40

      // 昵称
      ctx.fillStyle = '#111827'
      ctx.font = 'bold 46px sans-serif'
      ctx.textAlign = 'left'
      const displayName = truncateText(ctx, userData.nickname || '用户', infoWidth)
      ctx.fillText(displayName, infoX, infoY)
      infoY += 48

      // 认证标识
      if (userData.isVerified) {
        ctx.fillStyle = '#10b981'
        ctx.font = '28px sans-serif'
        ctx.fillText('✓ 已认证', infoX, infoY)
        infoY += 45
      } else {
        infoY += 15
      }

      // 行业标签
      if (userData.industry) {
        ctx.font = 'bold 28px sans-serif'
        const tagWidth = ctx.measureText(userData.industry).width + 32

        ctx.fillStyle = '#eff6ff'
        drawRoundRect(ctx, infoX, infoY - 30, tagWidth, 42, 6)
        ctx.fill()

        ctx.fillStyle = '#2563eb'
        ctx.fillText(userData.industry, infoX + 16, infoY)
      }

      // 5. 职业信息区域
      let jobY = avatarY + avatarSize + 40

      // 分隔线
      ctx.strokeStyle = '#f3f4f6'
      ctx.lineWidth = 2
      ctx.beginPath()
      ctx.moveTo(padding, jobY)
      ctx.lineTo(canvasWidth - padding, jobY)
      ctx.stroke()

      jobY += 50

      // 公司
      if (userData.company) {
        ctx.fillStyle = '#111827'
        ctx.font = 'bold 36px sans-serif'
        const displayCompany = truncateText(ctx, userData.company, canvasWidth - padding * 2)
        ctx.fillText(displayCompany, padding, jobY)
        jobY += 55
      }

      // 职位
      if (userData.jobTitle) {
        ctx.fillStyle = '#6b7280'
        ctx.font = '32px sans-serif'
        const displayJob = truncateText(ctx, userData.jobTitle, canvasWidth - padding * 2)
        ctx.fillText(displayJob, padding, jobY)
        jobY += 55
      }

      // 6. 个人简介区域
      if (userData.bio) {
        // 分隔线
        jobY += 40
        ctx.strokeStyle = '#f3f4f6'
        ctx.lineWidth = 2
        ctx.beginPath()
        ctx.moveTo(padding, jobY)
        ctx.lineTo(canvasWidth - padding, jobY)
        ctx.stroke()

        jobY += 45

        ctx.fillStyle = '#6b7280'
        ctx.font = '30px sans-serif'
        const bioLines = wrapText(ctx, userData.bio, canvasWidth - padding * 2, 3)

        for (let i = 0; i < bioLines.length; i++) {
          ctx.fillText(bioLines[i], padding, jobY)
          jobY += 44
        }
      }

      // 7. 底部提示区域
      const bottomY = canvasHeight - 120

      // 底部背景
      ctx.fillStyle = '#f9fafb'
      ctx.fillRect(0, bottomY, canvasWidth, 120)

      // 分隔线
      ctx.strokeStyle = '#e5e7eb'
      ctx.lineWidth = 2
      ctx.beginPath()
      ctx.moveTo(0, bottomY)
      ctx.lineTo(canvasWidth, bottomY)
      ctx.stroke()

      ctx.fillStyle = '#6b7280'
      ctx.font = '28px sans-serif'
      ctx.textAlign = 'center'
      ctx.fillText('长按识别小程序码', canvasWidth / 2, bottomY + 45)

      ctx.fillStyle = '#2563eb'
      ctx.font = 'bold 32px sans-serif'
      ctx.fillText('查看完整个人名片', canvasWidth / 2, bottomY + 85)

      // 8. 绘制完成，导出图片
      ctx.draw(false, () => {
        setTimeout(() => {
          uni.canvasToTempFilePath({
            canvasId: 'shareCanvas',
            destWidth: canvasWidth * 2,
            destHeight: canvasHeight * 2,
            success: (res) => {
              resolve(res.tempFilePath)
            },
            fail: (err) => {
              console.error('生成分享图失败:', err)
              reject(err)
            }
          })
        }, 500)
      })
    } catch (err) {
      console.error('生成分享图异常:', err)
      reject(err)
    }
  })
}
