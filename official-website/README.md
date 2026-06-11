# 圈脉链官网

一个具有动效的现代化人脉社交平台官网，采用深空宇宙主题设计，展现人脉连接的力量。

## 🎨 设计特色

### 核心设计理念
- **深空宇宙主题**：深邃的背景色彩，模拟社交网络的宇宙空间
- **动态粒子网络**：背景中的粒子系统实时响应鼠标交互，象征人脉连接
- **发光边框系统**：卡片采用半透明背景 + 青蓝色发光边框，悬浮时增强效果
- **流畅动画**：滚动视差、渐入动画、卡片悬浮等多种交互动效

### 色彩系统
- **主色**：电光青蓝 (#0EA5E9) - 代表连接和流动
- **辅助色**：能量橙红 (#F97316) - 强调行动召唤
- **背景**：深空渐变 (#0A0E27 → #1E293B)
- **文字**：高对比白色和柔和灰色层次

## 🚀 功能特性

### 交互动效
1. **粒子网络背景**
   - 80个动态粒子节点
   - 鼠标交互产生连接线
   - 距离越近连接越强

2. **滚动视差效果**
   - 英雄区视觉元素随滚动移动
   - 网络球体缩放动画
   - 导航栏背景透明度变化

3. **卡片动画**
   - 3D 悬浮效果（鼠标跟随）
   - 渐入动画（滚动触发）
   - 发光边框增强

4. **统计数字动画**
   - 数字递增动画
   - 滚动到视口时触发

5. **表单交互**
   - 输入框聚焦动画
   - 提交按钮状态反馈
   - 涟漪点击效果

## 📁 文件结构

```
official-website/
├── index.html          # 主页面结构
├── styles.css          # 完整设计系统和样式
├── script.js           # 交互动画逻辑
└── README.md           # 项目文档
```

## 🛠️ 技术栈

- **HTML5**：语义化结构
- **CSS3**：
  - CSS Variables（设计 tokens）
  - Flexbox & Grid 布局
  - 动画和过渡效果
  - 响应式设计
- **原生 JavaScript**：
  - Canvas 粒子系统
  - Intersection Observer API
  - 事件处理和动画

## 📦 使用方法

### 直接打开
1. 下载所有文件到同一目录
2. 双击 `index.html` 在浏览器中打开

### 本地服务器（推荐）
```bash
# 使用 Python
python -m http.server 8000

# 使用 Node.js
npx serve

# 使用 PHP
php -S localhost:8000
```

然后访问 `http://localhost:8000`

## 🎯 页面板块

### 1. 首页英雄区
- 分屏式布局
- 左侧：品牌信息、行动按钮、统计数据
- 右侧：动态网络球体可视化

### 2. 功能介绍
- 时间轴式布局
- 4个核心功能展示
- 交替左右排列

### 3. 关于我们
- 双栏布局
- 左侧：品牌故事和价值观
- 右侧：统计卡片网格

### 4. 联系我们
- 双栏布局
- 左侧：联系方式
- 右侧：交互表单

### 5. 页脚
- 品牌信息
- 导航链接
- 法律信息

## 🎨 设计系统

### Spacing Scale（8px 基准）
- 4px, 8px, 12px, 16px, 24px, 32px, 48px, 64px, 96px, 128px

### Typography Scale
- 12px - 72px 完整字号体系
- 主标题：72px（移动端 48px）
- 次标题：48px（移动端 32px）
- 正文：16px

### Border Radius
- Small: 6px
- Medium: 8px
- Large: 12px
- XLarge: 16px

### Animation Timing
- Fast: 150ms
- Base: 250ms
- Slow: 350ms
- Easing: cubic-bezier(0.16, 1, 0.3, 1)

## 📱 响应式设计

### 断点
- Desktop: > 1024px
- Tablet: 768px - 1024px
- Mobile: < 768px

### 适配策略
- 移动端隐藏导航链接
- 网格布局转为单列
- 字号缩小
- 简化动画效果

## ⚡ 性能优化

1. **Canvas 优化**
   - requestAnimationFrame 动画循环
   - 粒子数量控制（80个）
   - 连接距离限制

2. **滚动优化**
   - 节流函数处理滚动事件
   - Intersection Observer 懒加载动画

3. **CSS 优化**
   - 使用 transform 和 opacity 动画
   - will-change 提示浏览器优化
   - 避免重排和重绘

## 🎭 动画效果列表

### 页面加载
- 整体淡入动画
- 英雄区内容渐入上移

### 滚动触发
- 功能卡片渐入
- 统计卡片渐入
- 数字递增动画

### 鼠标交互
- 粒子网络连接
- 卡片 3D 悬浮
- 按钮涟漪效果
- 导航链接下划线

### 视差效果
- 英雄区视觉元素
- 网络球体缩放

## 🔧 自定义配置

### 修改粒子系统
在 `script.js` 中修改 `ParticleNetwork` 类的参数：
```javascript
this.particleCount = 80;           // 粒子数量
this.connectionDistance = 120;     // 连接距离
this.mouse.radius = 150;           // 鼠标影响半径
```

### 修改色彩
在 `styles.css` 的 `:root` 中修改 CSS 变量：
```css
--brand-primary: #0EA5E9;      /* 主色 */
--brand-secondary: #F97316;     /* 辅助色 */
--space-deep: #0A0E27;          /* 背景色 */
```

### 修改动画速度
```css
--duration-fast: 150ms;
--duration-base: 250ms;
--duration-slow: 350ms;
```

## 🌐 浏览器兼容性

- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

### 需要的特性
- CSS Grid
- CSS Variables
- Canvas API
- Intersection Observer API
- ES6+ JavaScript

## 📝 待优化项

- [ ] 添加移动端汉堡菜单
- [ ] 实现表单后端提交
- [ ] 添加更多微交互
- [ ] 优化移动端性能
- [ ] 添加暗色/亮色主题切换
- [ ] 国际化支持

## 📄 许可证

本项目仅供学习和参考使用。

## 👥 联系方式

- 邮箱：contact@quanmailchain.com
- 电话：400-888-8888
- 地址：北京市朝阳区创新大厦

---

**圈脉链** - 构建你的人脉宇宙 🌌
