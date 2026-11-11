Component({
  properties: {
    item: {
      type: Object,
      value: {}
    }
  },

  data: {
    displayCover: '',
    coverBroken: false
  },

  observers: {
    // 封面地址变化或加载失败时，重算真正展示的 src
    'item.coverImage, coverBroken': function (coverImage, coverBroken) {
      this.setData({
        displayCover: coverBroken ? '' : String(coverImage || '')
      })
    }
  },

  methods: {
    onCoverError() {
      this.setData({ coverBroken: true })
    },

    onTap() {
      this.triggerEvent('detail', { item: this.data.item })
    }
  }
})
