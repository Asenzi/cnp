Component({
  properties: {
    count: {
      type: Number,
      value: 4
    }
  },

  data: {
    items: []
  },

  observers: {
    'count': function (value) {
      const n = Math.max(Number(value || 0), 1)
      const items = []
      for (let i = 0; i < n; i += 1) {
        items.push(i)
      }
      this.setData({ items: items })
    }
  }
})
