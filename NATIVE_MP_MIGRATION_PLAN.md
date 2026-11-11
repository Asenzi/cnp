# uni-app → 原生微信小程序 迁移评估与方案

调研对象：`front/`（uni-app / Vue 3）
生成时间：2026-10-11

---

## 一、现状盘点

| 项 | 结论 |
| --- | --- |
| 框架 | uni-app（HBuilderX 工程，**无 package.json**），Vue 3 + `<script setup>`（130 个 .vue 中 127 个） |
| 代码量 | 53,339 行：pages 50,043 / api 1,736 / utils 1,206 / components 354 |
| 页面 | `pages.json` 注册 47 个页面；实际 43 个页面级 .vue + 87 个业务组件 |
| 后端接口 | 12 个 api 模块、约 130 个接口，统一前缀 `/api/v1/...` |
| 入口 | 4 个 tab：人脉 / 资源 / 圈子 / 我的 |
| 三方依赖 | **无 UI 库、无 pinia/vuex、无 scss**；仅 `@dcloudio/uni-app`（48 处）+ `vue`（81 处） |
| 组件引用 | 全部显式 `import`（script setup 自动注册），不依赖 easycom |
| 编译产物 | `unpackage/dist` 为空，没有可直接复用的 mp-weixin 产物 |
| 小程序 appid | `wxd801f2e147f4abb1`（manifest.json / mp-weixin） |

关键结论：**没有 UI 库绑架，是本项目能干净迁原生的最大前提。**

### 全局能力清单（App.vue + utils）

- `App.vue`：onLaunch 初始化地图 key、连接 WebSocket、定位同步；onShow 按 5 分钟节流再次同步；onHide 断开 WS
- `utils/request.js`（351 行）：baseUrl 多级探测（storage override → 构建环境变量 → 环境默认）、token 注入、`code === 0` 判定、debug 记录
- `utils/realtime.js`（179 行）：`uni.connectSocket` + 20s 心跳 + 指数退避重连 + 订阅分发
- `utils/location-sync.js`（140 行）：定位上报
- `utils/profile-share-image.js`（325 行）+ `utils/share-image.js`（82 行）：canvas 生成分享图
- `components/ImageCropper`（354 行）：图片裁剪
- `utils/wechat-auth.js`、`payment-session.js`、`circle-interest.js`、`industry-options.js`

---

## 二、成本分层

### A. 可直接平移（改动极小，约 3,300 行）

| 文件 | 说明 |
| --- | --- |
| `api/*.js`（12 个，1,736 行） | 只依赖 `request()`，本身无 uni 调用，几乎 0 改动 |
| `utils/request.js`（351 行） | 仅 4 处 `uni.*`（getStorageSync / setStorageSync / request / getSystemInfoSync），直接换 `wx.*` |
| `utils/realtime.js`（179 行） | 仅 `uni.connectSocket` → `wx.connectSocket`，其余是纯逻辑（心跳、退避、订阅） |
| `utils/industry-options.js`、`circle-interest.js`、`payment-session.js`、`pages/tab/discover/modules/city-query.js` | 纯常量/纯函数，原样拷贝 |
| `pages/tab/discover/modules/location.js`（152 行） | 少量 `uni.getLocation` / `uni.getStorageSync` 替换 |

### B. 需机械改写（量大，约 4.7 万行）

1. **文件拆分**：130 个 .vue → 约 520 个原生文件（wxml / wxss / js / json）
2. **响应式**：`ref` / `reactive` / `computed` / `watch` → `data` + `setData` + 手写派生逻辑
3. **模板指令**：`v-if/v-for/:class/:style/@click/v-model/slot` → `wx:if/wx:for/wx:key/bindtap/data-*/bindinput/slot`
4. **组件通信**：`props` / `emits` → `properties` / `triggerEvent`（87 个组件）
5. **样式**：Vue `scoped` → 组件样式隔离 + 独立 wxss；`:class` 数组/对象语法需改写成字符串拼接
6. **生命周期**：`onLoad/onShow/onReachBottom/onPullDownRefresh/onShareAppMessage`（来自 `@dcloudio/uni-app`，48 处）→ 原生同名钩子，改造成本低

### C. 必须重写（高成本，需设计）

| 项 | 原因 |
| --- | --- |
| canvas 分享图（407 行） | 现用 `uni.createCanvasContext`（旧接口），原生建议改 **Canvas 2D** + `SelectorQuery`，两套绘图 API 差异大 |
| 全局状态 | 现无 store，靠 `getStorageSync` + `getOpenerEventChannel` + WS 订阅；原生需自建 `getApp().globalData` + 轻量 eventBus |
| 大页面 | discover 1,812 行、resource-detail 1,571、publish 1,376、following 1,336、card 1,291 —— 建议借迁移机会拆组件 |
| `profile-share-image.js` | 依赖 canvas 测量文本、圆角头像裁剪，原生需按 2d 接口重实现 |

---

## 三、uni API → wx API 映射

按项目内实际调用频次排序：

| uni API | 频次 | 原生对应 | 备注 |
| --- | --- | ---: | --- | --- |
| `uni.navigateTo` | 178 | `wx.navigateTo` | url 完全一致 |
| `uni.getStorageSync` | 152 | `wx.getStorageSync` | 一致 |
| `uni.showToast` | 127 | `wx.showToast` | 一致 |
| `uni.removeStorageSync` | 119 | `wx.removeStorageSync` | 一致 |
| `uni.setStorageSync` | 63 | `wx.setStorageSync` | 一致 |
| `uni.navigateBack` | 36 | `wx.navigateBack` | 一致 |
| `uni.showModal` | 34 | `wx.showModal` | 一致 |
| `uni.getSystemInfoSync` | 28 | `wx.getWindowInfo` / `getDeviceInfo` | 官方已废弃旧接口，建议顺手升级 |
| `uni.stopPullDownRefresh` | 25 | `wx.stopPullDownRefresh` | 一致 |
| `uni.hideLoading` / `showLoading` | 30 | 同名 | 一致 |
| `uni.switchTab` | 15 | `wx.switchTab` | 一致 |
| `uni.getMenuButtonBoundingClientRect` | 14 | `wx.getMenuButtonBoundingClientRect` | 一致，用于自定义导航栏 |
| `uni.getOpenerEventChannel` | 11 | `this.getOpenerEventChannel()` | **原生支持**，改动小 |
| `uni.showShareMenu` | 9 | `wx.showShareMenu` | 需配合 `onShareAppMessage` |
| `uni.setNavigationBarTitle` | 8 | `wx.setNavigationBarTitle` | 一致 |
| `uni.uploadFile` | 7 | `wx.uploadFile` | 一致 |
| `uni.showActionSheet` | 7 | `wx.showActionSheet` | 一致 |
| `uni.redirectTo` / `reLaunch` | 9 | 同名 | 一致 |
| `uni.chooseImage` | 7 | `wx.chooseMedia` | 官方推荐升级 |
| `uni.setClipboardData` | 6 | `wx.setClipboardData` | 一致 |
| `uni.getImageInfo` | 5 | `wx.getImageInfo` | 一致 |
| `uni.previewImage` | 4 | `wx.previewImage` | 一致 |
| `uni.createCanvasContext` | 4 | `wx.createCanvasContext` 或 Canvas 2D | 建议改 2D |
| `uni.chooseLocation` / `openLocation` | 5 | 同名 | 需在 app.json 声明 `requiredPrivateInfos` |
| `uni.requestVirtualPayment` | 3 | `wx.requestVirtualPayment` | **需类目资质** |
| `uni.connectSocket` | 3 | `wx.connectSocket` | 一致 |
| `uni.chooseMessageFile` | 3 | `wx.chooseMessageFile` | 一致 |
| `uni.canvasToTempFilePath` | 3 | `wx.canvasToTempFilePath` | 2D 模式下参数不同 |
| `uni.getSetting` / `authorize` / `openSetting` | 7 | 同名 | 一致 |
| `uni.requestPayment` | 1 | `wx.requestPayment` | 一致 |
| `uni.compressImage` | 2 | `wx.compressImage` | 一致 |
| `uni.createSelectorQuery` | 2 | `wx.createSelectorQuery` | 一致 |
| `uni.downloadFile` / `openDocument` | 3 | 同名 | 一致 |
| `uni.login` | 1 | `wx.login` | 一致 |

结论：**99% 的 API 有 1:1 对应**，真正的成本不在 API 迁移，而在 5 万行视图层与响应式逻辑的改写。

---

## 四、目标工程结构建议

```
miniprogram/
├── app.js                  原 App.vue 逻辑：启动初始化、WS 生命周期、定位节流
├── app.json                47 页面注册 + tabBar + requiredPrivateInfos + permission
├── app.wxss                原 App.vue <style> + uni.scss 变量（改为 CSS 变量）
├── project.config.json     appid: wxd801f2e147f4abb1
├── sitemap.json
├── pages/
│   ├── tab/                discover(人脉) resources(资源) circles(圈子) me(我的)
│   ├── me/                 editInfo my-circles following followers interests income
│   │                       points member-center card settings security auth ...
│   ├── circles/            create edit manage members detail filter
│   ├── resources/          detail publish manage venue-detail
│   ├── messages/           chat friend-apply system-notice
│   ├── auth/login/
│   ├── legal/              user-agreement privacy-policy
│   └── common/webview/
├── components/             87 个业务组件，每个 4 件套（wxml/wxss/js/json）
├── services/               原 api/*.js，12 个模块整体迁入
├── utils/
│   ├── request.js          baseUrl 探测 + token 注入（换 wx.request）
│   ├── realtime.js         WebSocket + 心跳 + 重连 + 订阅
│   ├── location.js         定位同步（原 location-sync.js + discover/modules/location.js）
│   ├── auth.js             原 wechat-auth.js
│   ├── share-image.js      canvas 2D 重写
│   └── event-bus.js        新增：补 uni 无全局状态管理的空缺
├── store/                  globalData + 轻量订阅（用户信息、未读数、位置）
└── assets/                 原 static/：tabBar 图标 8 个、fonts、icon、me-icons
```

---

## 五、建议的分阶段路线

| 阶段 | 内容 | 说明 |
| --- | --- | --- |
| P0 骨架 | app.json 全量页面注册、tabBar、request.js、globalData、eventBus、登录态守卫 | 跑通"空壳能编译、能切 tab" |
| P1 基础能力 | login 页、我的 tab、api 全量迁入、user/profile 相关二级页 | 验证接口链路与鉴权 |
| P2 人脉 tab | discover（1,812 行，最重）+ 城市选择 + 定位 + 筛选面板 | 建议借机拆组件 |
| P3 资源 / 圈子 tab | resources、circles 及其 详情/发布/管理/成员 | 与 P2 可并行 |
| P4 高级能力 | IM + WebSocket、支付（含虚拟支付）、canvas 分享图、图片裁剪、认证/实名 | 风险集中区，放最后 |

---

## 六、风险与决策点

1. **5 万行一次性重写的周期风险** —— 强烈建议分阶段，且新旧共存期间保持后端接口不变（后端已稳定，可直接复用）。
2. **大页面** —— discover / resource-detail / publish / following / card 均超 1,300 行，直接翻译会产出超 1,500 行的 .js/.wxml，建议先拆组件再迁移。
3. **`computed` / `watch` 消失** —— 原生没有响应式派生，业务里大量"筛选后的列表""合并后的展示字段"需要在 `setData` 前手工重算，这是最容易出 bug 的地方。
4. **隐私合规** —— `__usePrivacyCheck__` + `requiredPrivateInfos: [getLocation, chooseLocation]` 必须搬到 `app.json`，并在小程序后台配置《用户隐私保护指引》；原生对隐私接口的拦截比 uni 更严格。
5. **虚拟支付** —— `wx.requestVirtualPayment` 需特定类目资质，若资质未就绪需保留兜底路径。
6. **appid 复用** —— 沿用 `wxd801f2e147f4abb1` 会影响已发布版本的用户，需确认是原 appid 迭代还是换新 appid 重开。
7. **工程形态** —— 纯原生（无构建、微信开发者工具直接打开）上手最快；若团队习惯 TS + Sass + npm 包，可引入构建链（如 gulp / miniprogram-build），但会增加维护成本。

---

## 七、推荐策略：骨架一次到位 + 页面分批（不建议一次性重写）

### 为什么说"一次性重写太复杂"

复杂度**不是**由 5.3 万行这个数字带来的，而是三个结构性因素叠加：

1. **没有中间可运行态** —— 一次性重写意味着必须全部写完才能编译运行。中途无法在开发者工具里逐页验证，也无法和旧版 uni 包做界面对比，错误会集中到最后爆发。
2. **响应式必须手工重写** —— 原生没有 `computed` / `watch`。业务里大量"筛选后的列表""合并后的展示字段""依赖多个输入的派生状态"，都要改成在 `setData` 前手工重算。这类 bug 不会报错，只会静默显示错数据，是最难排查的部分。
3. **超大页面翻译必然丢细节** —— discover（1,812 行）、resource-detail（1,571）、publish（1,376）、following（1,336）、card（1,291）。1,800 行逐行翻译，遗漏是概率问题不是态度问题。

### 折中方案：三层拆分

| 层 | 做法 | 理由 |
| --- | --- | --- |
| **骨架层（一次做完）** | app.json 全量注册 47 页 + tabBar + request.js + api 12 模块 + globalData/eventBus + 登录守卫 | 这层约 2,000 行，其中 api + request 几乎是直搬。做完立刻得到一个"能编译、能切 tab、能登录"的壳，后续每加一页都能立刻验证 |
| **页面层（分批）** | 按 P1→P4 顺序，每批做完就能跑、能和旧版对比 | 每批都有可运行产出，风险被切成 5 份 |
| **重构层（后置）** | 大页面拆组件、统一样式，等跑通之后再做 | 避免"边翻译边重构"，两种复杂度叠加 |

### 关键动作：先做一个垂直切片

在正式分批前，先完整打通**一条最窄的链路**（建议：登录 → 人脉 tab 列表 → 某个卡片详情），目的是把迁移模式固定下来：

- 组件怎么拆（properties / triggerEvent / slot 的写法约定）
- 数据怎么流（`setData` 粒度、派生字段在哪算）
- 样式怎么引（组件样式隔离开关 `styleIsolation`、全局 wxss 边界）
- 错误怎么处理（request reject 后的统一 toast / 登录态失效跳转）

模式定下来之后，剩下的页面就是"套模板"，速度会快很多，也不容易各页写法不一致。

### 每批的验收标准

- 该批页面在开发者工具中可正常编译、跳转、下拉刷新 / 上拉加载
- 关键接口与旧版 uni 包抓包对比，请求参数与响应处理一致
- 真机跑一遍该批页面，确认无 `setData` 性能告警

---

## 八、冗余代码清单与工作量修正

原始统计 53,339 行中有 **18,676 行（35%）确认为冗余**，实际有效代码约 **34,663 行**。

### A. 死文件（不参与编译，但严重干扰阅读与判断）

| 类别 | 数量 | 行数 |
| --- | --- | --- |
| `*.vue.backup` 备份文件 | 16 个 | 12,652 |
| `pages/me/card - 副本/` 整个目录 | 10 个 .vue | 2,034 |
| 小计 | | **14,686** |

注意：`pages/me/wallet/index.vue.backup` 对应的 `wallet` 目录已不存在，说明历史上迭代过一轮"钱包"实现。

### B. 无人引用的死页面（已注册但全项目 0 处跳转，或未注册）

| 页面 | 行数 | 状态 |
| --- | --- | --- |
| `pages/me/interests/index`（我的收藏） | 893 | 已注册，0 引用 |
| `pages/tab/messages/index` | 551 | 已注册，0 引用 |
| `pages/me/settings/index`（系统设置） | 424 | 已注册，0 引用 |
| `pages/me/security/password/index`（修改密码） | 400 | 已注册，0 引用 |
| `pages/debug/index` | 381 | 调试页，0 引用 |
| `pages/debug/location-test` | 262 | 调试页，0 引用 |
| `pages/resources/detail-design/index`（详情页设计） | 221 | 设计稿页，0 引用 |
| `pages/circles/filter/index` | 30 | 已注册，0 引用 |
| `pages/me/edit-info/index` | 627 | **未注册**（与 `editInfo` 重复） |
| `pages/resources/address-editor/index` | 149 | **未注册** |
| `pages/index/index` | 52 | **未注册**（模板残留） |
| 小计 | | **3,990** |

### C. 需要澄清的歧义（同一个功能存在两份实现，必须先确定哪份是现行版）

| 歧义 | A 版本 | B 版本 | 影响 |
| --- | --- | --- | --- |
| 消息页 | `pages/me/messages`（736 行，1 处引用） | `pages/tab/messages`（551 行，**0 引用**） | 以 `me/messages` 为准？ |
| 编辑资料 | `pages/me/editInfo`（1,137 行，已注册） | `pages/me/edit-info`（627 行，未注册） | 以 `editInfo` 为准？ |
| 个人名片 | `pages/me/card`（1,291 行） | `pages/me/card - 副本`（585 行） | 副本是新版还是旧版？ |
| 圈子列表组件 | `tab/circles/components/` 下 6 个 `Discover*` 命名组件（906 行） | 同目录 4 个 `MyCircle*` 组件 | 命名错位，历史遗留 |

### D. 重复逻辑（不是死文件，但应在重写时收敛）

- `formatTime` 定义 3 处、`formatCount` 定义 3 处、`parseJsonSafe` 定义 2 处，另有十余个 `normalizeXxx` 分散在各页面
- 分页加载 / 下拉刷新 / 空状态 / 加载中 是每个列表页各自写一遍的模板代码
- **原生小程序可用 `Behavior` 优雅收敛这些重复**（uni-app 的 mixins 一一对应），这是迁移原生的额外收益

### 修正后的工作量

| 口径 | 行数 |
| --- | --- |
| 原始统计 | 53,339 |
| 减去死文件与死页面 | −18,676 |
| **有效代码** | **34,663** |
| 其中可直搬（api + utils） | 约 3,000 |
| 其中需重写的视图层 | 约 31,700 |

**策略建议调整：从"照搬迁移"改为"按功能清单重写"。** 既然冗余达 35%，逐行翻译等于把冗余再抄一遍。正确做法是先产出一版"真正要上线的功能清单"，确认哪些页面保留、哪些砍掉、歧义处用哪份，再按清单重写。

---

## 九、迁移前需要拍板的问题

1. 迁移方式：整体一次性重写，还是按 P0→P4 分阶段推进？（建议分批）
2. 工程形态：纯原生零构建，还是 TypeScript + Sass 构建链？
3. 起点：先做 P0 骨架（空壳 + request + tabBar + 登录），还是直接开工某个 tab？
4. 视觉：完全沿用现有 UI（照搬 wxml/wxss），还是借重写机会统一设计语言？
5. appid：沿用现有 `wxd801f2e147f4abb1`，还是申请新 appid？
6. **（新增）功能范围**：上表 B 的 11 个死页面中，`settings` / `interests` / `password` 是"忘了做入口"还是"已废弃"？确认后才能定最终页面清单。
7. **（新增）歧义裁定**：消息页、编辑资料、个人名片各以哪一份为基准？

---

## 十、页面保留 / 砍掉清单（待标注）

统计口径：行数 = 对应 .vue 行数；引用 = 该页面路径在 `pages/` 下的出现次数。

> 重要说明：`pages/tab/me/index.vue` 的设置跳转用硬编码 `urlMap`（仅 account-security / profile-card / help / about 四个 key），其余设置项走 `showToast` 占位。因此下表"引用 0"的判定已回看跳转源确认，不是 grep 漏判。

### A. 建议保留（入口明确）

| 模块 | 页面 | 行数 | 引用 |
| --- | --- | --- | --- |
| tab | `tab/discover`（人脉库） | 1,812 | tab |
| tab | `tab/resources`（资源） | 1,068 | tab |
| tab | `tab/circles`（圈子） | 1,190 | tab |
| tab | `tab/me`（我的） | 850 | tab |
| tab | `tab/discover/city`（选择城市） | 603 | — |
| 认证 | `auth/login` | 630 | 36 |
| 圈子 | `circles/create` / `detail` / `edit` / `manage` / `members` | 369 / 719 / 341 / 711 / 133 | 3 / 9 / 1 / 1 / 1 |
| 资源 | `resources/detail` / `publish` / `manage` / `venue-detail` | 1,571 / 1,376 / 485 / 766 | 9 / 3 / 1 / 1 |
| 消息 | `messages/chat` / `friend-apply` / `system-notice` | 1,242 / 415 / 241 | 2 / 1 / 1 |
| 我的 | `me/card`（名片） | 1,291 | 15 |
| 我的 | `me/following` / `followers` | 1,336 / 744 | 1 / 1 |
| 我的 | `me/member-center`（会员中心） | 1,210 | 2 |
| 我的 | `me/income`（钱包） | 957 | 1 |
| 我的 | `me/messages` | 736 | 1 |
| 我的 | `me/editInfo` | 1,137 | 4 |
| 我的 | `me/help-feedback` / `about` | 835 / 551 | 3 / 2 |
| 我的 | `me/circle-owner/apply` / `salon-owner/apply` / `city-partner/apply` | 841 / 98 / 98 | 3 / 1 / 1 |
| 我的 | `me/auth/index` / `realname` / `enterprise` / `submit` / `result` | 500 / 687 / 632 / 644 / 324 | 2 / 7 / 3 / 2 / 3 |
| 我的 | `me/security` / `security/phone` | 389 / 409 | 2 / 1 |
| 我的 | `me/privacy` / `privacy/blocked` | 561 / 436 | 1 / 1 |
| 我的 | `me/my-circles` / `points/records` | 396 / 185 | 1 / 1 |
| 公共 | `common/webview` / `cropper` | 21 / 633 | 1 / 2 |
| 法务 | `legal/user-agreement` / `privacy-policy` | 314 / 479 | 1 / 1 |

### B. 建议砍掉（依据充分）

| 页面 | 行数 | 理由 |
| --- | --- | --- |
| `debug/index` | 381 | 调试页，0 引用 |
| `debug/location-test` | 262 | 调试页，0 引用 |
| `resources/detail-design` | 221 | 设计稿页，0 引用 |
| `tab/messages` | 551 | 0 引用，已被 `me/messages` 取代 |
| `circles/filter` | 30 | 0 引用，空壳 |
| `me/edit-info` | 627 | 未注册，与 `editInfo` 重复 |
| `resources/address-editor` | 149 | 未注册 |
| `pages/index` | 52 | 未注册，uni-app 模板残留 |
| `.vue.backup` ×16 | 12,652 | 备份文件 |
| `me/card - 副本/` | 2,034 | 副本目录 |
| **小计** | **17,909** | |

### C. 待你裁定（页面写好了但没接入口，可能是半成品）

| 页面 | 行数 | 现状 | 选择 |
| --- | --- | --- | --- |
| `me/interests`（我的收藏） | 893 | 0 入口；注意 `following` 页标题也写着"我的收藏"，两者功能疑似重叠 | 补入口 / 砍掉 / 与 following 合并 |
| `me/points`（获取积分） | 942 | 0 入口，但子页 `points/records` 有 1 处引用 | 补入口 / 砍掉 |
| `me/settings`（系统设置） | 424 | 0 入口（设置列表只映射 4 个 key） | 补入口 / 砍掉 |
| `me/security/password`（修改密码） | 400 | 0 入口，`security` 页未跳转过来 | 补入口 / 砍掉 |

**这 4 个页面合计 2,659 行。** 若判定为废弃，有效代码可进一步降到约 32,000 行。

### 标注方式

在 A 表上划掉不需要的、C 表每行填"补入口 / 砍掉"，确认后即可定稿最终页面清单，P0 骨架按此清单注册 `app.json`。

---

## 十一、未使用资产完整清单（脚本全量扫描）

扫描方式：Python 脚本遍历 front 全部 .vue，对每个组件名 / 页面路径统计其在**其他文件**中的出现次数（排除 `.backup` 与副本目录）。脚本见 `.workbuddy/tmp_scan_unused.py`。

### A. 孤儿组件：15 个，2,543 行

| 组件 | 行数 | 归属 | 说明 |
| --- | --- | --- | --- |
| `pages/tab/me/components/MeTopLogged.vue` | 380 | 我的 | **该组 5 个组件页面完全未引用** |
| `pages/tab/me/components/MeTopGuest.vue` | 278 | 我的 | 同上 |
| `pages/tab/me/components/MeServiceGrid.vue` | 109 | 我的 | 同上 |
| `pages/tab/me/components/MeSettingList.vue` | 87 | 我的 | 同上 |
| `pages/tab/me/components/MeMemberCenterCard.vue` | 123 | 我的 | 同上 |
| `components/ImageCropper/ImageCropper.vue` | 355 | 公共 | 0 引用；`pages/cropper` 自己用 canvas 实现了裁剪 |
| `pages/tab/circles/components/DiscoverHeader.vue` | 213 | 圈子 | 命名错位：Discover* 组件放在 circles 目录 |
| `pages/tab/circles/components/DiscoverHero.vue` | 89 | 圈子 | 同上 |
| `pages/tab/circles/components/DiscoverMasonry.vue` | 51 | 圈子 | 同上 |
| `pages/tab/circles/components/MyCircleCard.vue` | 249 | 圈子 | 页面未引用 |
| `pages/tab/resources/components/ResourceCard.vue` | 174 | 资源 | 页面未引用 |
| `pages/circles/detail/components/CircleResourceCard.vue` | 209 | 圈子详情 | 页面未引用 |
| `pages/circles/detail/components/CircleNoticeCard.vue` | 89 | 圈子详情 | 页面未引用 |
| `pages/circles/create/components/CreateRulesCard.vue` | 58 | 创建圈子 | 页面未引用 |
| `pages/me/card/components/ProfileBottomActions.vue` | 79 | 名片 | 页面未引用（但它被 `ProfileSymbol` 反向依赖） |

**一个重要推论**：`tab/me`、`tab/resources`、`tab/circles` 三个 tab 页面**完全没有引用自己 components 目录下的组件**。这说明这三个 tab 页历史上被整体重写过一次——组件被内联进页面，旧组件没删。这也解释了为什么 discover 单页能到 1,812 行。

对迁移的含义：不必迁移这些孤儿组件；且 `tab/circles/components/` 下的 `Discover*`（906 行）原本可能是 discover 页的组件，重写时可参考其结构来拆分大页面。

### B. 未使用页面：12 个，4,932 行

**已注册但 0 引用（9 个，4,104 行）**

| 页面 | 行数 |
| --- | --- |
| `me/points`（获取积分） | 942 |
| `me/interests`（我的收藏） | 893 |
| `tab/messages` | 551 |
| `me/settings`（系统设置） | 424 |
| `me/security/password`（修改密码） | 400 |
| `debug/index` | 381 |
| `debug/location-test` | 262 |
| `resources/detail-design` | 221 |
| `circles/filter` | 30 |

**未注册（3 个，828 行）**

| 页面 | 行数 |
| --- | --- |
| `me/edit-info` | 627 |
| `resources/address-editor` | 149 |
| `pages/index` | 52 |

### C. 未使用的静态资源：20 个，约 1.04 MB

- **`static/fonts/MaterialSymbolsOutlined.ttf` —— 943 KB，全项目 0 引用**（小程序主包上限 2 MB，这一项就占掉近一半）
- `static/icon/` 未使用 14 个：about、activity、card、chage-pws、chat-he、income、introduction、like、recharge、spending、ulike、wallet、wechat-call、wechat-link（合计 96 KB）
- `static/me-icons/` 未使用 5 个：arrow-back-ios-dark、badge-primary、corporate-primary、logout-gray.svg、payments-green

### D. 低复用组件：37 个仅被 1 处引用

不是死代码，但说明组件化程度低。体量最大的几个：`ProfileContactSection`（742 行）、`NetworkMemberCard`（449）、`ProfileSymbol`（303）、`ChatMessageBubble`（273）、`FriendApplyRequestCard`（245）。迁移时可考虑直接内联，减少组件数量。

### 修正后的冗余总量

| 类别 | 行数 |
| --- | --- |
| `.backup` 备份文件 | 12,652 |
| `card - 副本` 目录 | 2,034 |
| 孤儿组件 | 2,543 |
| 未使用页面 | 4,932 |
| **合计冗余** | **22,161（41.6%）** |
| **有效代码** | **约 31,178** |

若 C 组 4 个待裁定页面（2,659 行）也砍掉，有效代码约 28,500 行。

---

## 十二、进度记录

### P0 骨架（已完成）

`miniprogram/`：app.json 全量注册 + 4 项 tabBar + `request.js` 重写 baseUrl 探测 +
`services/` 12 个模块直搬 + `store.js` / `event-bus.js` + 8 个 tabBar 图标。48 个文件。

### P1 垂直切片（已完成）

**决策**：视觉沿用现有 UI；接口真接口优先 + 本地兜底。

打通链路：登录 → 人脉列表 → 名片详情。

| 产物 | 对应 front | 说明 |
| --- | --- | --- |
| `pages/auth/login/` | `pages/auth/login/index.vue`（630 行） | 视觉 1:1，含协议勾选、邀请码、审核未通过弹窗 |
| `pages/discover/` | `pages/tab/discover/index.vue`（1,812 行） | 分页状态机抽成 Behavior，页面代码约 300 行 |
| `pages/card/` | `pages/me/card/index.vue`（1,291 行 + 7 组件） | 英雄区 / 统计 / 简介 / 圈子 / 底部操作 |
| `components/` 5 个 | TopSearchFilterHeader、NetworkMemberCard、NetworkEndHint、空状态、骨架屏 | 样式照搬 |
| `behaviors/paginated-list.js` | 无对应（新增） | 后续所有列表页复用 |
| `utils/profile.js` `profile-detail.js` | 散落在页面里的映射逻辑 | 收敛成纯函数 |
| `utils/mock.js` `fallback.js` | 无对应（新增） | 后端不可达时保证流程可跑通 |
| `utils/` 另外 7 个 | `front/utils/*` 直搬 | realtime / wechat-auth / location / location-sync 等 |

**P1 钉死的模式**已写入 `NATIVE_MP_PATTERNS.md`，后续页面照此执行。

**P1 临时方案**（后续替换，数据层已对齐）：筛选面板用 `wx.showActionSheet` 闭环。

**自检结果**：JSON 全通过 / 四件套齐全 / 组件引用全解析 / 跳转路径全注册 /
39 个 JS 全过 `node --check` / 分页状态机 19 项冒烟全过。

**过程中修掉的一个真实缺陷**：`listSkeleton` 原先只看 `!hasAny`，空结果会永远卡在骨架屏；
已加 `!listLoaded` 条件。

### 下一步（P2）

候选：人脉模块其余页面（following / interested）、圈子 tab、资源 tab。
建议每个 tab 各自成批，每批跑完第十二章的自检。
