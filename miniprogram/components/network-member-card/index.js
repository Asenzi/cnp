/**
 * 人脉卡片
 * 对应 uni 版 pages/tab/discover/components/NetworkMemberCard.vue
 *
 * 事件：view（点击整卡）/ verify（点击去认证）
 * 注意：uni 版的关注按钮在源码里已被注释，这里沿用「只展示、点击进详情」的现行视觉
 */

const BADGE_CERTIFICATION = 'https://cos.cnptec.site/static/icon/certification.png'
const BADGE_MEMBER = 'https://cos.cnptec.site/static/icon/mennber1.png'
const BADGE_CIRCLE_OWNER = 'https://cos.cnptec.site/static/icon/leader.png?v=20260623'
const DEFAULT_AVATAR_URL = 'https://cos.cnptec.site/static/logo.png'

Component({
  properties: {
    member: {
      type: Object,
      value: {}
    }
  },

  data: {
    displayAvatarUrl: DEFAULT_AVATAR_URL,
    badgeCertification: BADGE_CERTIFICATION,
    badgeMember: BADGE_MEMBER,
    badgeCircleOwner: BADGE_CIRCLE_OWNER,
    hasTags: false
  },

  observers: {
    'member': function (member) {
      const normalized = String((member && member.avatar) || '').trim()
      const lower = normalized.toLowerCase()
      const isInvalid = !normalized || ['null', 'undefined', 'none'].indexOf(lower) >= 0
        || lower.indexOf('/static/logo.png') >= 0
      const tags = (member && member.circleTags) || []

      this.setData({
        displayAvatarUrl: isInvalid ? DEFAULT_AVATAR_URL : normalized,
        hasTags: tags.length > 0
      })
    }
  },

  methods: {
    onTap() {
      this.triggerEvent('view', { member: this.data.member })
    },

    onTapVerify() {
      this.triggerEvent('verify', { member: this.data.member })
    }
  }
})
