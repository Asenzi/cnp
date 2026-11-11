# 原生小程序迁移模式手册

P1 垂直切片（登录 → 人脉列表 → 名片详情）定下的写法约定。
**后续所有页面照此执行**，避免各页写法跑偏。

---

## 一、目录约定

```
miniprogram/
├── pages/<模块>/index.{js,json,wxml,wxss}   # 页面扁平命名，不套 tab/ 层级
├── components/<组件名>/index.*              # 公共组件，自带样式隔离
├── behaviors/                               # 复用逻辑（分页等）
├── services/                                # 接口层，从 front/api 直搬
├── utils/                                   # request / store / event-bus / 字段映射
└── assets/                                  # 图标等静态资源
```

命名差异（与 front 对照）：

| front (uni-app) | 原生 |
|---|---|
| `pages/tab/discover/index.vue` | `pages/discover/index.*` |
| `pages/tab/me/` | `pages/mine/` |
| `pages/me/card/` | `pages/card/` |
| `pages/auth/login/` | `pages/auth/login/` |

---

## 二、.vue 拆四件套

| vue 块 | 原生文件 | 说明 |
|---|---|---|
| `<template>` | `.wxml` | 指令改写见第四节 |
| `<script setup>` | `.js` | 用 `Page({})` / `Component({})` |
| `<style scoped>` | `.wxss` | 组件天然隔离；页面样式需人工保证不重名 |
| 页面配置 | `.json` | `navigationStyle` / `usingComponents` |

`onLoad(options)` 对应 uni 的 `onLoad`；`onShow` / `onPullDownRefresh` / `onReachBottom` 同名。
uni 的 `onMounted` → 原生 `onLoad` 或 `onReady`。

---

## 三、响应式消失 —— 最重要的规则

原生没有 `computed` / `watch`。**所有展示用派生字段必须在 `setData` 之前算完**，
且每次影响它们的 `setData` 之后要同步重算。

做法：

1. 字段映射抽成纯函数，放 `utils/profile.js`、`utils/profile-detail.js`
2. 页面上算好再 `setData`，不要指望 wxml 里算
3. 需要联动的一批状态（骨架屏 / 空状态 / 加载中）交给 Behavior 统一重算

错误示范（原生不支持）：

```xml
<view wx:if="{{members.length > 0 && !loading}}">
```

正确做法：在 js 里维护 `listHasAny` / `listEmpty`，wxml 只做布尔判断。

---

## 四、模板指令映射

| uni / vue | 原生 wxml |
|---|---|
| `v-if` / `v-else-if` / `v-else` | `wx:if` / `wx:elif` / `wx:else`（**必须相邻兄弟节点**） |
| `v-for="item in list"` | `wx:for="{{list}}" wx:key="id"`（默认变量名 `item` / `index`） |

> **⚠️ 硬规则：`wx:for` 不得与 `wx:if`/`wx:elif`/`wx:else` 写在同一标签上**（wx:for 会重开作用域，导致 else 配对失败、WXML 编译报 "wx:if not found"）。需要"if 空 else 遍历"时，用 `<block wx:else>` 包住 `wx:for` 的标签。v-else + v-for 同标签在 Vue 里合法，迁移时必须改写。

> **⚠️ 硬规则：原生工程没有 uni-app 注入的 button 重置**。微信默认 button 是 `display:block; margin:auto; padding:0 14px; font-size:18px; line-height:2.55`，放在 flex 行里会把小胶囊按钮撑宽、挤坏兄弟节点（uni 里正常、原生里跑偏的典型陷阱）。对策：`app.wxss` 已加全局 button 重置；**组件内部**因样式隔离不受 app.wxss 影响，小控件一律改用 `view` + `hover-class`，或在组件 wxss 里显式写全 margin/padding/line-height/font-size/white-space。
| `@tap` | `bindtap` |
| `@tap.stop` | `catchtap` |
| `:src="x"` | `src="{{x}}"` |
| `:class="{ 'a': b }"` | `class="{{b ? 'a' : ''}}"` |
| `v-model="kw"` | 拆成 `value="{{kw}}"` + `bindinput` |
| `v-html` | `rich-text` |

**wxml 不支持复杂表达式**：不能写 `Math.max()`、`.filter()`、`.includes()`。
遇到就先在 js 的 `observers` 或普通方法里预计算成 data。

示例（`components/top-search-filter-header`）：

```js
observers: {
  'rightItems, activeRightKeys': function (rightItems, keys) {
    this.setData({
      rightItemsView: (rightItems || []).map((item) =>
        Object.assign({}, item, { _active: keys.indexOf(item.key) >= 0 })
      )
    })
  }
}
```

---

## 五、组件通信

组件用 `properties` 接参，`triggerEvent` 发事件：

```js
// 组件
this.triggerEvent('view', { member: this.data.member })

// 页面 wxml
<network-member-card bind:view="onViewProfile" />

// 页面 js
onViewProfile(event) {
  const member = event.detail.member
}
```

**事件名必须全小写**（`tapright` 而非 `tapRight`），wxml 里 `bind:tapright`。

复杂判断（如「某个 key 是否激活」）不要在 wxml 里做，
用 `observers` 生成一份带标记的视图数组。

---

## 六、列表页统一用 `behaviors/paginated-list.js`

页面只需实现两个方法：

```js
Page({
  behaviors: [paginatedList],

  async fetchList(params) {
    return getNetworkRecommendations(params)   // 返回 { items, next_cursor, has_more, request_id }
  },

  mapListItem(item) {
    return mapMemberCard(item, UI_TEXT)        // 字段映射
  }
})
```

Behavior 提供（页面不要自己 setData 这些字段）：

| 字段 | 含义 |
|---|---|
| `listItems` | 列表数据 |
| `listLoading` / `listLoadingMore` | 首屏 / 加载更多 |
| `listHasMore` / `listCursor` | 分页游标 |
| `listError` | 错误信息 |
| `listHasAny` / `listSkeleton` / `listEmpty` | **派生状态，自动重算** |
| `listRefreshing` | 下拉刷新中 |
| `listLocating` | 定位中（也撑起骨架屏） |

方法：`initList()` / `loadList(reset)` / `refreshList()` / `scheduleReload(delay)`
/ `onListScrollToLower()` / `onListRetry()` / `updateListItem(id, patch)`

> 坑：`listSkeleton` 必须带 `!listLoaded` 条件，否则空结果会永远卡在骨架屏。

---

## 七、接口层

`services/*.js` 从 `front/api/*.js` 直搬（`uni.` → `wx.`），逻辑不改。

页面取数统一套 `withFallback`：

```js
import { withFallback } from '../../utils/fallback'

return withFallback(
  () => getNetworkRecommendations(params),   // 真接口优先
  () => mockRecommendations(params),         // 网络不可达时兜底
  { silent: true }
)
```

规则：

- 请求成功 → 直接返回，不碰 mock
- 网络层失败（statusCode 0 / 5xx / `request:fail`）→ 回落本地数据
- **业务错误（401 等）照常抛出**，不用 mock 掩盖
- `app.globalData.mockEnabled = true` 可强制全量走 mock（演示用）

mock 数据在 `utils/mock.js`，按 index 稳定生成，便于反复比对视觉。

---

## 八、全局状态

front 没有 pinia / vuex，靠 storage + eventChannel。原生补位方案：

- `utils/store.js` —— token / userInfo / 未读数，写 storage 并同步 globalData
- `utils/event-bus.js` —— 跨页通信（登录后刷新列表等）
- 页面间传参优先用 `eventChannel`（原生支持 `this.getOpenerEventChannel()`）

---

## 九、自定义导航

tab 页沿用 `navigationStyle: custom`。尺寸从 `app.globalData.navBar` 取：

```js
const navBar = getApp().globalData.navBar
topPaddingPx = navBar.statusBarHeight + 6
capsuleRowHeightPx = navBar.menuHeight
capsuleAvoidRightInsetPx = navBar.menuRight + navBar.menuWidth - 8   // 搜索框右侧让位
```

详情页（名片等）沿用默认导航栏，不做 custom。

---

## 十、样式

- 组件样式天然隔离，直接搬 uni 的 `<style scoped>` 内容即可
- 页面 `.wxss` 只放页面级布局类，不与组件类名冲突
- uni 版的 `@media (prefers-color-scheme: dark)` 块**先不搬**，等暗色模式统一处理
- `rpx` 保持不变；`env(safe-area-inset-bottom)` 原生同样支持

---

## 十一、P1 已知未覆盖范围

后续批次补齐：

- 筛选面板组件（P1 用 `wx.showActionSheet` 临时闭环，数据层已对齐）
- 名片详情的动态流、联系方式解锁、分享菜单
- 消息会话、认证链、法务页
- 其余 3 个 tab（资源 / 圈子 / 我的）的具体内容
- 暗色模式

---

## 十二、自检脚本

每次改完跑一遍（不改动 front）：

1. JSON 合法性 + 页面四件套齐全
2. `usingComponents` 路径存在，且 wxml 标签都已注册
3. `import` / `require` 相对路径可解析
4. `navigateTo` / `switchTab` 的 url 已在 `app.json` 注册
5. 全部 `.js` 过 `node --check`（复制成 `.mjs` 以按 ESM 解析）
6. 分页状态机冒烟：首屏 / 翻页 / 空结果 / 错误 / 就地更新
