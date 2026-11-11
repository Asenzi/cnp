const channels = new Map()

function getChannel(name) {
  if (!channels.has(name)) {
    channels.set(name, new Set())
  }
  return channels.get(name)
}

export function on(name, handler) {
  if (typeof handler !== 'function') {
    return () => {}
  }
  getChannel(name).add(handler)
  return () => off(name, handler)
}

export function off(name, handler) {
  const channel = channels.get(name)
  if (channel) {
    channel.delete(handler)
  }
}

export function emit(name, payload) {
  const channel = channels.get(name)
  if (!channel) {
    return
  }
  Array.from(channel).forEach((handler) => {
    try {
      handler(payload)
    } catch (error) {
      // 单个订阅者出错不影响其他订阅者
    }
  })
}

export function once(name, handler) {
  const wrapped = (payload) => {
    off(name, wrapped)
    handler(payload)
  }
  return on(name, wrapped)
}

export default { on, off, emit, once }
