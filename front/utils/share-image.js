/**
 * 生成圈子分享图
 */
export async function generateCircleShareImage(circleData) {
  return new Promise((resolve, reject) => {
    const ctx = uni.createCanvasContext('shareCanvas')

    const canvasWidth = 750
    const canvasHeight = 1000
    const padding = 40

    // 1. 绘制白色背景
    ctx.fillStyle = '#ffffff'
    ctx.fillRect(0, 0, canvasWidth, canvasHeight)

    // 2. 绘制圈子封面/logo（左侧）
    const imageSize = 400
    const imageX = padding
    const imageY = padding + 80

    if (circleData.coverUrl) {
      ctx.drawImage(circleData.coverUrl, imageX, imageY, imageSize, imageSize)
    } else {
      // 如果没有图片，绘制占位背景
      ctx.fillStyle = '#f3f4f6'
      ctx.fillRect(imageX, imageY, imageSize, imageSize)
    }

    // 3. 绘制圆角边框
    ctx.strokeStyle = '#2563eb'
    ctx.lineWidth = 6
    ctx.strokeRect(imageX - 3, imageY - 3, imageSize + 6, imageSize + 6)

    // 4. 绘制圈子信息（右侧）
    const infoX = imageX + imageSize + 40
    const infoY = imageY + 40

    // 圈子名称
    ctx.fillStyle = '#111827'
    ctx.font = 'bold 48px sans-serif'
    ctx.fillText(circleData.name || '圈子', infoX, infoY)

    // 成员数
    ctx.fillStyle = '#6b7280'
    ctx.font = '32px sans-serif'
    ctx.fillText(circleData.memberCount || '0 位成员', infoX, infoY + 80)

    // 动态数
    ctx.fillText(circleData.postCount || '0 条动态', infoX, infoY + 140)

    // 圈子类型标签
    ctx.fillStyle = '#2563eb'
    ctx.fillRect(infoX, infoY + 200, 160, 60)
    ctx.fillStyle = '#ffffff'
    ctx.font = 'bold 28px sans-serif'
    ctx.fillText(circleData.type || '免费圈', infoX + 20, infoY + 240)

    // 5. 绘制底部小程序标识
    ctx.fillStyle = '#9ca3af'
    ctx.font = '28px sans-serif'
    ctx.fillText('小程序', padding, canvasHeight - 60)

    // 6. 绘制顶部标题
    ctx.fillStyle = '#111827'
    ctx.font = 'bold 36px sans-serif'
    ctx.fillText('邀请你加入圈子', padding, 60)

    ctx.draw(false, () => {
      setTimeout(() => {
        uni.canvasToTempFilePath({
          canvasId: 'shareCanvas',
          success: (res) => {
            resolve(res.tempFilePath)
          },
          fail: (err) => {
            reject(err)
          }
        })
      }, 500)
    })
  })
}
