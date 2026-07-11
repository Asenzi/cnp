# 项目 API 完整清单与队列需求分析

## 📊 API 总览

**总计：** 122 个 API 接口

---

## 📋 按模块分类

### 1. 认证模块 (Auth) - 11 个
| 方法 | 路径 | 说明 | 需要队列 |
|------|------|------|---------|
| POST | `/auth/sms-code` | 发送短信验证码 | ⚠️ 可选 |
| POST | `/auth/login` | 手机+验证码登录 | ❌ |
| POST | `/auth/password-login` | 手机+密码登录 | ❌ |
| POST | `/auth/wechat-miniapp-login` | 微信小程序登录 | ❌ |
| GET | `/auth/wechat-bind-status` | 查询微信绑定状态 | ❌ |
| POST | `/auth/wechat-bind` | 绑定微信 | ❌ |
| POST | `/auth/phone-bind-code` | 发送绑定手机验证码 | ⚠️ 可选 |
| POST | `/auth/phone-bind` | 绑定/更换手机号 | ❌ |
| POST | `/auth/password-change-code` | 发送修改密码验证码 | ⚠️ 可选 |
| POST | `/auth/password-change` | 修改密码 | ❌ |

**队列建议：** 发送短信验证码可以异步（3个接口），但不是高优先级

---

### 2. 用户模块 (User) - 13 个
| 方法 | 路径 | 说明 | 需要队列 |
|------|------|------|---------|
| GET | `/user/ping` | 健康检查 | ❌ |
| GET | `/user/me` | 获取当前用户信息 | ❌ |
| PATCH | `/user/me` | 更新用户信息 | ❌ |
| GET | `/user/profiles/{id}` | 查看用户公开资料 | ❌ |
| POST | `/user/profiles/{id}/contact-unlock` | 解锁联系方式 | ❌ |
| GET | `/user/profiles/{id}/miniapp-code` | 获取小程序码 | ❌ |
| GET | `/user/me/privacy` | 获取隐私设置 | ❌ |
| PATCH | `/user/me/privacy` | 更新隐私设置 | ❌ |
| GET | `/user/me/blocked-users` | 查看黑名单 | ❌ |
| POST | `/user/me/blocked-users` | 添加黑名单 | ❌ |
| DELETE | `/user/me/blocked-users/{id}` | 移除黑名单 | ❌ |
| POST | `/user/me/avatar` | 上传头像 | ❌ |
| POST | `/user/me/card-file` | 上传名片附件 | ❌ |

**队列建议：** 全部不需要

---

### 3. 实名认证模块 (Verification) - 11 个
| 方法 | 路径 | 说明 | 需要队列 |
|------|------|------|---------|
| GET | `/verification/me` | 获取认证概览 | ❌ |
| GET | `/verification/real-name/detail` | 获取实名认证详情 | ❌ |
| GET | `/verification/real-name/files/{side}` | 预览身份证照片 | ❌ |
| POST | `/verification/real-name/id-card-file` | 上传身份证照片 | ❌ |
| POST | `/verification/enterprise/license-file` | 上传营业执照 | ❌ |
| POST | `/verification/real-name/submit` | 提交实名认证 | ❌ |
| POST | `/verification/real-name/tencent/start` | 开始腾讯云实名认证 | ❌ |
| POST | `/verification/real-name/tencent/finish` | 完成腾讯云实名认证 | ❌ |
| POST | `/verification/enterprise/submit` | 提交企业认证 | ❌ |
| POST | `/verification/business-card/submit` | 提交名片认证 | ❌ |

**队列建议：** 全部不需要（审核通知在管理端）

---

### 4. 圈子模块 (Circle) - 16 个
| 方法 | 路径 | 说明 | 需要队列 |
|------|------|------|---------|
| POST | `/circles/cover-file` | 上传圈子封面 | ❌ |
| POST | `/circles` | 创建圈子 | ❌ |
| PATCH | `/circles/{code}` | 更新圈子信息 | ❌ |
| GET | `/circles/me` | 我加入的圈子 | ❌ |
| GET | `/circles/discover` | 发现圈子 | ❌ |
| GET | `/circles/user/{id}` | 用户加入的圈子 | ❌ |
| GET | `/circles/interests` | 我感兴趣的圈子 | ❌ |
| POST | `/circles/{code}/interest/toggle` | 标记圈子感兴趣 | ❌ |
| GET | `/circles/join-requests` | 圈子加入申请列表 | ❌ |
| POST | `/circles/join-requests/{id}/review` | 审核圈子加入申请 | ✅ **已优化** |
| GET | `/circles/{code}` | 圈子详情 | ❌ |
| GET | `/circles/{code}/posts` | 圈子资源列表 | ❌ |
| GET | `/circles/{code}/members` | 圈子成员列表 | ❌ |
| GET | `/circles/{code}/post-syncs/pending` | 待审核的资源同步 | ❌ |
| POST | `/circles/{code}/post-syncs/{id}/review` | 审核资源同步 | ⚠️ 可选 |

**队列建议：**
- ✅ 圈子加入审核（已优化）
- ⚠️ 资源同步审核（可选）

---

### 5. 人脉模块 (Network) - 6 个
| 方法 | 路径 | 说明 | 需要队列 |
|------|------|------|---------|
| GET | `/network/ping` | 健康检查 | ❌ |
| GET | `/network/recommendations` | 获取人脉推荐 | ❌ |
| GET | `/network/filters` | 获取筛选项 | ❌ |
| POST | `/network/impressions/batch` | 上报曝光 | ❌ |
| POST | `/network/feedback` | 上报行为反馈 | ❌ |
| GET | `/network/interests` | 感兴趣的人脉 | ❌ |
| POST | `/network/interest/toggle` | 标记感兴趣 | ❌ |

**队列建议：** 全部不需要

---

### 6. 资源模块 (Post) - 20 个
| 方法 | 路径 | 说明 | 需要队列 |
|------|------|------|---------|
| GET | `/post/ping` | 健康检查 | ❌ |
| GET | `/post/filters` | 获取筛选项 | ❌ |
| POST | `/post/impressions/batch` | 上报曝光 | ❌ |
| POST | `/post/feedback` | 上报行为反馈 | ❌ |
| GET | `/post/feed` | 资源列表 | ❌ |
| GET | `/post/mine` | 我的资源 | ❌ |
| GET | `/post/user/{id}/feed` | 用户资源动态 | ❌ |
| GET | `/post/interests` | 感兴趣的资源 | ❌ |
| POST | `/post` | 发布资源 | ❌ |
| PUT | `/post/{code}` | 编辑资源 | ❌ |
| GET | `/post/{code}` | 资源详情 | ❌ |
| POST | `/post/{code}/view` | 浏览计数 | ❌ |
| POST | `/post/{code}/like` | 点赞 | ❌ |
| DELETE | `/post/{code}/like` | 取消点赞 | ❌ |
| POST | `/post/{code}/interest/toggle` | 标记感兴趣 | ❌ |
| POST | `/post/{code}/status` | 上下架资源 | ❌ |
| POST | `/post/{code}/pin` | 置顶资源 | ❌ |
| DELETE | `/post/{code}` | 删除资源 | ❌ |
| POST | `/post/assets/upload` | 上传资源图片 | ❌ |

**队列建议：** 全部不需要

---

### 7. 即时通讯模块 (IM) - 13 个
| 方法 | 路径 | 说明 | 需要队列 |
|------|------|------|---------|
| GET | `/im/ping` | 健康检查 | ❌ |
| GET | `/im/overview` | IM 概览 | ❌ |
| GET | `/im/conversations` | 会话列表 | ❌ |
| GET | `/im/conversations/{id}/messages` | 会话消息 | ❌ |
| POST | `/im/conversations/{id}/messages` | 发送消息 | ❌ |
| POST | `/im/conversations/{id}/messages/{mid}/revoke` | 撤回消息 | ❌ |
| POST | `/im/conversations/{id}/read` | 标记已读 | ❌ |
| GET | `/im/presence/{id}` | 在线状态 | ❌ |
| GET | `/im/friend-requests` | 好友申请列表 | ❌ |
| POST | `/im/friend-requests` | 发送好友申请 | ✅ **已优化** |
| POST | `/im/friend-requests/{id}/accept` | 接受好友申请 | ✅ **已优化** |
| POST | `/im/friend-requests/{id}/ignore` | 忽略好友申请 | ❌ |
| GET | `/im/system-notices` | 系统通知 | ❌ |
| POST | `/im/assets/upload` | 上传 IM 文件 | ❌ |

**队列建议：**
- ✅ 发送好友申请（已优化）
- ✅ 接受好友申请（已优化）

---

### 8. 支付模块 (Payment) - 10 个
| 方法 | 路径 | 说明 | 需要队列 |
|------|------|------|---------|
| GET | `/payment/ping` | 健康检查 | ❌ |
| GET | `/payment/member/center` | 会员中心 | ❌ |
| POST | `/payment/member/subscribe` | 订阅会员 | ❌ |
| POST | `/payment/member/orders/{no}/confirm` | 确认会员订单 | ❌ |
| GET | `/payment/member/orders/{no}` | 查询会员订单 | ❌ |
| GET | `/payment/member/orders` | 会员订单列表 | ❌ |
| POST | `/payment/wallet/recharge` | 创建充值订单 | ❌ |
| POST | `/payment/wallet/recharge/{no}/confirm` | 确认充值订单 | ❌ |
| GET | `/payment/wallet/recharge/orders` | 充值订单列表 | ❌ |
| GET | `/payment/wallet/recharge/{no}` | 查询充值订单 | ❌ |
| POST | `/payment/wechat/notify` | 微信支付回调 | ⚠️ 建议 |

**队列建议：**
- ⚠️ 微信支付回调（建议添加，处理成功后发通知）

---

### 9. 积分模块 (Points) - 4 个
| 方法 | 路径 | 说明 | 需要队列 |
|------|------|------|---------|
| GET | `/points/ping` | 健康检查 | ❌ |
| GET | `/points/center` | 积分中心 | ❌ |
| GET | `/points/records` | 积分记录 | ❌ |
| POST | `/points/check-in` | 每日签到 | ❌ |

**队列建议：** 全部不需要

---

### 10. 反馈模块 (Feedback) - 2 个
| 方法 | 路径 | 说明 | 需要队列 |
|------|------|------|---------|
| POST | `/feedback/assets/upload` | 上传反馈截图 | ❌ |
| POST | `/feedback` | 提交反馈 | ⚠️ 可选 |

**队列建议：**
- ⚠️ 提交反馈（可选，通知管理员）

---

### 11. 管理后台模块 (Admin) - 15 个
| 方法 | 路径 | 说明 | 需要队列 |
|------|------|------|---------|
| GET | `/admin/ping` | 健康检查 | ❌ |
| POST | `/admin/auth/login` | 管理员登录 | ❌ |
| GET | `/admin/auth/profile` | 管理员信息 | ❌ |
| GET | `/admin/dashboard/overview` | 仪表盘概览 | ❌ |
| GET | `/admin/users` | 用户列表 | ❌ |
| POST | `/admin/users/{id}/status` | 启用/禁用用户 | ⚠️ 可选 |
| GET | `/admin/circles` | 圈子列表 | ❌ |
| POST | `/admin/circles/{code}/status` | 更新圈子状态 | ⚠️ 可选 |
| GET | `/admin/posts` | 资源列表 | ❌ |
| POST | `/admin/posts/{code}/status` | 更新资源状态 | ⚠️ 可选 |
| POST | `/admin/posts/{code}/pin` | 置顶资源 | ❌ |
| GET | `/admin/verifications` | 认证申请列表 | ❌ |
| POST | `/admin/verifications/{id}/review` | 审核认证 | ✅ **已优化** |
| GET | `/admin/content-reviews` | 内容审核列表 | ❌ |
| POST | `/admin/content-reviews/{id}/review` | 审核内容 | ⚠️ 可选 |
| GET | `/admin/recharges` | 充值订单列表 | ❌ |
| GET | `/admin/contact-package-config` | 获取联系包配置 | ❌ |
| PUT | `/admin/contact-package-config` | 保存联系包配置 | ❌ |
| GET | `/admin/configs` | 系统配置列表 | ❌ |
| PUT | `/admin/configs/{key}` | 更新系统配置 | ❌ |

**队列建议：**
- ✅ 认证审核（已优化）
- ⚠️ 用户状态变更、圈子状态变更、资源状态变更、内容审核（可选）

---

### 12. 其他模块 - 2 个
| 方法 | 路径 | 说明 | 需要队列 |
|------|------|------|---------|
| GET | `/health` | 健康检查 | ❌ |
| GET | `/event/ping` | 活动模块占位 | ❌ |

---

## 📊 队列需求统计

### ✅ 已优化（4 个）
1. ✅ **实名认证审核** - `POST /admin/verifications/{id}/review`
2. ✅ **发送好友申请** - `POST /im/friend-requests`
3. ✅ **接受好友申请** - `POST /im/friend-requests/{id}/accept`
4. ✅ **圈子加入审核** - `POST /circles/join-requests/{id}/review`

### ⚠️ 建议优化（高优先级，3 个）
5. **微信支付回调** - `POST /payment/wechat/notify`
   - 处理支付结果、发放权益、发送通知
6. **用户状态变更** - `POST /admin/users/{id}/status`
   - 封禁/解禁用户时通知
7. **资源审核** - `POST /admin/posts/{code}/status`
   - 审核通过/拒绝时通知发布者

### ⚠️ 可选优化（中优先级，5 个）
8. **发送短信验证码** - `POST /auth/sms-code` 等 3 个接口
9. **圈子状态变更** - `POST /admin/circles/{code}/status`
10. **内容审核** - `POST /admin/content-reviews/{id}/review`
11. **资源同步审核** - `POST /circles/{code}/post-syncs/{id}/review`
12. **提交反馈** - `POST /feedback`

### ❌ 不需要队列（110 个）
- 所有查询接口（GET）
- 所有快速操作（点赞、标记、计数等）
- 所有数据提交（创建、更新、删除）

---

## 🎯 总结

**队列使用率：** 4/122 = **3.3%** （已优化）

**如果全部优化：** 12/122 = **9.8%**

**结论：**
- ✅ **核心 4 个接口已优化**，覆盖了最重要的用户通知场景
- 📈 **90% 的 API 不需要队列**，当前架构合理
- 🎯 **重点关注审核和支付回调**，这些场景用户最需要及时通知

---

## 💡 优化建议

### 立即优化（最值得做的 3 个）
1. **微信支付回调** - 用户付款成功后立即通知
2. **用户封禁通知** - 账号被封禁时告知原因
3. **资源审核通知** - 发布的内容审核结果

### 可以等等（ROI 较低）
- 短信验证码（本身就很快）
- 反馈通知（管理员可以主动查看）
- 其他审核通知（频率较低）

---

**文档创建时间：** 2026-06-02
