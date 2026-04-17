function stableHash(text) {
  const source = String(text || '')
  let hash = 0
  for (let i = 0; i < source.length; i += 1) {
    hash = (hash << 5) - hash + source.charCodeAt(i)
    hash |= 0
  }
  return Math.abs(hash).toString(36)
}

export function getWechatDeviceId() {
  const sys = uni.getSystemInfoSync()
  const seed = [
    sys.brand || '',
    sys.model || '',
    sys.system || '',
    sys.platform || '',
    sys.language || '',
    sys.version || '',
    sys.SDKVersion || '',
    sys.deviceOrientation || ''
  ].join('|')
  return `wxfp_${stableHash(seed)}`
}

export function getMiniappLoginCode() {
  return new Promise((resolve, reject) => {
    uni.login({
      provider: 'weixin',
      success: (res) => {
        if (res?.code) {
          resolve(res.code)
          return
        }
        reject(new Error('未获取到微信登录凭证'))
      },
      fail: (err) => {
        reject(err)
      }
    })
  })
}
