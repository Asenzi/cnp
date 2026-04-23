export const serviceList = [
  {
    key: 'auth',
    iconPath: '/static/icon/certification.png',
    label: '实名认证',
    colorClass: 'service-blue',
    url: '/pages/me/auth/realname/index'
  },
  {
    key: 'event',
    iconPath: '/static/icon/activity.png',
    label: '我的活动',
    colorClass: 'service-orange'
  },
  {
    key: 'create_circle',
    iconPath: '/static/icon/create.png',
    label: '创建圈子',
    colorClass: 'service-blue',
    url: '/pages/circles/create/index'
  },
  {
    key: 'card',
    iconPath: '/static/icon/card.png',
    label: '我的名片',
    colorClass: 'service-purple',
    url: '/pages/me/card/index'
  }
]

export const settingList = [
  { key: 'general', iconPath: '/static/me-icons/tune-gray.png', label: '通用设置' },
  { key: 'bind-phone', iconPath: '/static/me-icons/shield-person-primary.png', label: '绑定手机' },
  { key: 'help', iconPath: '/static/me-icons/help-gray.png', label: '帮助与反馈' },
  { key: 'about', iconPath: '/static/me-icons/info-gray.png', label: '关于我们' }
]
