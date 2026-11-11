const DEFAULT_AVATAR = 'https://cos.cnptec.site/static/logo.png'

Component({
  properties: {
    member: {
      type: Object,
      value: {}
    }
  },

  data: {
    displayAvatar: DEFAULT_AVATAR
  },

  observers: {
    'member.avatar': function (avatar) {
      this.setData({
        displayAvatar: String(avatar || '').trim() || DEFAULT_AVATAR
      })
    }
  },

  methods: {
    onAvatarError() {
      this.setData({ displayAvatar: DEFAULT_AVATAR })
    },

    onTap() {
      this.triggerEvent('detail', { member: this.data.member })
    }
  }
})
