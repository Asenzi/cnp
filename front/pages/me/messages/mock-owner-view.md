# 圈主视角 - 消息通知卡片 Mock

## 场景1：待处理的付费申请

```javascript
{
  id: "req_001",
  perspective: "owner",
  displayName: "张三",
  circleName: "产品经理交流圈",
  avatar: "https://cos.cnptec.site/static/avatar/user1.png",
  timeText: "5分钟前",
  message: "我是一名有3年经验的产品经理，希望能加入这个圈子学习交流",
  status: "pending",
  paymentStatus: "paid",
  amount: 99,
  read: false
}
```

**显示效果：**
- 头像：张三的头像（80rpx圆形）
- 主要信息：
  - 姓名：张三（粗体 32rpx）
  - 圈子：产品经理交流圈（灰色 26rpx）
  - 时间：5分钟前（右上角，灰色 24rpx）
- 留言区：淡蓝色背景，斜体引用样式
  - "我是一名有3年经验的产品经理，希望能加入这个圈子学习交流"
- 底部操作：
  - 左按钮：拒绝（灰色背景）
  - 右按钮：通过（蓝色渐变背景）

---

## 场景2：待处理的免费申请

```javascript
{
  id: "req_002",
  perspective: "owner",
  displayName: "李四",
  circleName: "深圳技术交流群",
  avatar: "https://cos.cnptec.site/static/avatar/user2.png",
  timeText: "1小时前",
  message: "",  // 无留言
  status: "pending",
  paymentStatus: "paid",  // 免费圈子也是paid状态
  amount: 0,
  read: false
}
```

**显示效果：**
- 头像：李四的头像
- 主要信息：
  - 姓名：李四
  - 圈子：深圳技术交流群
  - 时间：1小时前
- 无留言区（直接显示操作按钮）
- 底部操作：
  - 左按钮：拒绝
  - 右按钮：通过

---

## 场景3：已通过的申请

```javascript
{
  id: "req_003",
  perspective: "owner",
  displayName: "王五",
  circleName: "设计师联盟",
  avatar: "https://cos.cnptec.site/static/avatar/user3.png",
  timeText: "昨天",
  message: "我从事UI设计5年，想和大家交流学习",
  status: "approved",
  paymentStatus: "paid",
  amount: 199,
  statusText: "已通过",
  statusClass: "status-approved",
  read: true
}
```

**显示效果：**
- 卡片整体：透明度 0.6（已读状态）
- 头像：王五的头像
- 主要信息：
  - 姓名：王五
  - 圈子：设计师联盟
  - 时间：昨天
- 留言区：显示留言
- 底部状态：
  - 右下角绿色胶囊标签："已通过"

---

## 场景4：已拒绝的申请（有退款）

```javascript
{
  id: "req_004",
  perspective: "owner",
  displayName: "赵六",
  circleName: "创业者俱乐部",
  avatar: "https://cos.cnptec.site/static/avatar/user4.png",
  timeText: "2天前",
  message: "",
  status: "rejected",
  paymentStatus: "refunded",
  amount: 299,
  refundStatus: "success",
  statusText: "已拒绝 · 费用已退回",
  statusClass: "status-rejected",
  read: true
}
```

**显示效果：**
- 卡片整体：透明度 0.6（已读状态）
- 头像：赵六的头像
- 主要信息：
  - 姓名：赵六
  - 圈子：创业者俱乐部
  - 时间：2天前
- 无留言
- 底部状态：
  - 右下角红色胶囊标签："已拒绝 · 费用已退回"

---

## 场景5：待支付的申请

```javascript
{
  id: "req_005",
  perspective: "owner",
  displayName: "孙七",
  circleName: "前端开发者社区",
  avatar: "https://cos.cnptec.site/static/avatar/user5.png",
  timeText: "3小时前",
  message: "我是前端开发者，想加入学习",
  status: "pending",
  paymentStatus: "pending",
  amount: 99,
  statusText: "待完成支付",
  statusClass: "status-pending",
  read: false
}
```

**显示效果：**
- 头像：孙七的头像
- 主要信息：
  - 姓名：孙七
  - 圈子：前端开发者社区
  - 时间：3小时前
- 留言区：显示留言
- 底部状态：
  - 右下角灰色胶囊标签："待完成支付"
  - 无操作按钮（因为 paymentStatus 不是 "paid"）

---

## 视觉总结

### 卡片状态对比：

| 状态 | 卡片透明度 | 底部显示 | 可操作 |
|------|-----------|---------|--------|
| 待处理（已付费） | 1.0 | 拒绝/通过按钮 | ✓ |
| 待处理（未付费） | 1.0 | "待完成支付"标签 | ✗ |
| 已通过 | 0.6 | "已通过"绿色标签 | ✗ |
| 已拒绝 | 0.6 | "已拒绝"红色标签 | ✗ |

### 操作按钮样式：
- **拒绝按钮**：灰色背景 #f1f5f9，灰色文字 #64748b
- **通过按钮**：蓝色渐变背景，白色文字，带阴影

### 状态标签样式：
- **已通过**：浅绿色背景，深绿色文字
- **已拒绝**：浅红色背景，深红色文字
- **待支付**：浅灰色背景，灰色文字
