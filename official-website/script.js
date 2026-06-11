gsap.registerPlugin(ScrollTrigger);

// ==================== 初始化 ====================
document.addEventListener('DOMContentLoaded', () => {
    initSections();
    initMetrics();
    initPathAnimation();
    initEngineStack();
    initFlowSteps();
    initTableRows();
    initNavigation();
    initFormHandling();
});

// ==================== 区块渐入 ====================
function initSections() {
    const sections = document.querySelectorAll('.section');

    sections.forEach((section, index) => {
        gsap.to(section, {
            opacity: 1,
            y: 0,
            duration: 0.6,
            ease: "power2.out",
            scrollTrigger: {
                trigger: section,
                start: "top 80%",
                once: true
            },
            delay: index * 0.1
        });
    });
}

// ==================== 指标数字递增 ====================
function initMetrics() {
    const valueElements = document.querySelectorAll('.value-num');

    valueElements.forEach(el => {
        const target = parseFloat(el.dataset.value);

        ScrollTrigger.create({
            trigger: el,
            start: "top 85%",
            once: true,
            onEnter: () => {
                gsap.to(el, {
                    textContent: target,
                    duration: 1.5,
                    ease: "power2.out",
                    snap: { textContent: target < 10 ? 0.1 : 1 },
                    onUpdate: function() {
                        const current = parseFloat(this.targets()[0].textContent);
                        if (target < 10) {
                            el.textContent = current.toFixed(1);
                        } else {
                            el.textContent = Math.floor(current).toLocaleString('zh-CN');
                        }
                    }
                });
            }
        });
    });
}

// ==================== 路径动画 ====================
function initPathAnimation() {
    const pathDemo = document.querySelector('.path-demo');
    if (!pathDemo) return;

    const tl = gsap.timeline({
        scrollTrigger: {
            trigger: pathDemo,
            start: "top 70%",
            once: true
        }
    });

    // 节点依次出现
    tl.from('.path-node', {
        scale: 0.8,
        opacity: 0,
        duration: 0.5,
        stagger: 0.3,
        ease: "back.out(1.5)"
    });

    // 桥梁线条绘制
    tl.from('.bridge-line', {
        scaleX: 0,
        transformOrigin: "left center",
        duration: 0.6,
        ease: "power2.inOut"
    }, "-=0.2");

    // 桥梁信息出现
    tl.from('.bridge-info', {
        opacity: 0,
        y: -10,
        duration: 0.4
    }, "-=0.2");

    // 元数据淡入
    tl.from('.path-meta span', {
        opacity: 0,
        y: 10,
        duration: 0.3,
        stagger: 0.1
    }, "-=0.2");

    // 持续的脉冲动画
    gsap.to('.node-avatar', {
        scale: 1.05,
        duration: 2,
        repeat: -1,
        yoyo: true,
        ease: "sine.inOut",
        stagger: {
            each: 0.5,
            repeat: -1
        }
    });
}

// ==================== 引擎层级动画 ====================
function initEngineStack() {
    const layers = document.querySelectorAll('.engine-layer');

    layers.forEach((layer, index) => {
        gsap.to(layer, {
            opacity: 1,
            x: 0,
            duration: 0.6,
            ease: "power2.out",
            scrollTrigger: {
                trigger: layer,
                start: "top 75%",
                once: true
            },
            delay: index * 0.15
        });

        // 悬停效果
        layer.addEventListener('mouseenter', () => {
            gsap.to(layer, {
                x: 8,
                duration: 0.3,
                ease: "power2.out"
            });

            gsap.to(layer.querySelector('.layer-index'), {
                scale: 1.1,
                borderColor: 'var(--accent)',
                duration: 0.3
            });
        });

        layer.addEventListener('mouseleave', () => {
            gsap.to(layer, {
                x: 0,
                duration: 0.3,
                ease: "power2.out"
            });

            gsap.to(layer.querySelector('.layer-index'), {
                scale: 1,
                borderColor: 'var(--line-strong)',
                duration: 0.3
            });
        });
    });
}

// ==================== 流程步骤动画 ====================
function initFlowSteps() {
    const steps = document.querySelectorAll('.flow-step');

    steps.forEach((step, index) => {
        gsap.to(step, {
            opacity: 1,
            y: 0,
            duration: 0.6,
            ease: "power2.out",
            scrollTrigger: {
                trigger: step,
                start: "top 75%",
                once: true
            },
            delay: index * 0.2
        });
    });

    // 箭头动画
    const arrows = document.querySelectorAll('.flow-arrow');
    arrows.forEach((arrow, index) => {
        gsap.from(arrow, {
            opacity: 0,
            x: -20,
            duration: 0.5,
            scrollTrigger: {
                trigger: arrow,
                start: "top 75%",
                once: true
            },
            delay: (index + 1) * 0.2
        });
    });
}

// ==================== 表格行动画 ====================
function initTableRows() {
    const rows = document.querySelectorAll('.table-row');

    rows.forEach((row, index) => {
        gsap.to(row, {
            opacity: 1,
            x: 0,
            duration: 0.5,
            ease: "power2.out",
            scrollTrigger: {
                trigger: row,
                start: "top 80%",
                once: true
            },
            delay: index * 0.1
        });
    });
}

// ==================== 导航交互 ====================
function initNavigation() {
    const navItems = document.querySelectorAll('.nav-item');
    const sections = document.querySelectorAll('.section');

    // 点击导航平滑滚动
    navItems.forEach(item => {
        item.addEventListener('click', (e) => {
            e.preventDefault();

            const targetId = item.getAttribute('href').substring(1);
            const targetSection = document.getElementById(targetId);

            if (targetSection) {
                const offsetTop = targetSection.offsetTop - 60;

                gsap.to(window, {
                    scrollTo: { y: offsetTop, autoKill: false },
                    duration: 0.8,
                    ease: "power2.inOut"
                });

                // 更新激活状态
                navItems.forEach(nav => nav.classList.remove('active'));
                item.classList.add('active');
            }
        });
    });

    // 滚动时更新导航状态
    ScrollTrigger.create({
        trigger: document.body,
        start: "top top",
        end: "bottom bottom",
        onUpdate: (self) => {
            const scrollPos = window.scrollY + 100;

            sections.forEach((section, index) => {
                const sectionTop = section.offsetTop;
                const sectionBottom = sectionTop + section.offsetHeight;

                if (scrollPos >= sectionTop && scrollPos < sectionBottom) {
                    navItems.forEach(nav => nav.classList.remove('active'));
                    navItems[index].classList.add('active');
                }
            });
        }
    });
}

// ==================== 表单处理 ====================
function initFormHandling() {
    const form = document.querySelector('.access-form');
    if (!form) return;

    form.addEventListener('submit', (e) => {
        e.preventDefault();

        const button = form.querySelector('button');
        const originalText = button.textContent;

        // 提交动画
        gsap.to(button, {
            scale: 0.95,
            duration: 0.1,
            yoyo: true,
            repeat: 1
        });

        button.textContent = '提交中...';
        button.disabled = true;

        // 模拟提交
        setTimeout(() => {
            button.textContent = '提交成功';
            button.style.background = 'var(--success)';

            gsap.from(button, {
                scale: 1.05,
                duration: 0.3,
                ease: "back.out(2)"
            });

            setTimeout(() => {
                button.textContent = originalText;
                button.style.background = '';
                button.disabled = false;
                form.reset();
            }, 2000);
        }, 1200);
    });
}

// ==================== 路径线条动画效果 ====================
function animateBridgeLine() {
    const bridgeLine = document.querySelector('.bridge-line');
    if (!bridgeLine) return;

    // 创建流动效果
    gsap.to(bridgeLine, {
        backgroundPosition: "200% 0",
        duration: 2,
        repeat: -1,
        ease: "none"
    });
}

// ==================== 悬停增强 ====================
document.querySelectorAll('.metric-card').forEach(card => {
    card.addEventListener('mouseenter', () => {
        gsap.to(card, {
            y: -4,
            boxShadow: "0 4px 12px rgba(0, 0, 0, 0.08)",
            duration: 0.3,
            ease: "power2.out"
        });
    });

    card.addEventListener('mouseleave', () => {
        gsap.to(card, {
            y: 0,
            boxShadow: "none",
            duration: 0.3,
            ease: "power2.out"
        });
    });
});

// ==================== 响应式处理 ====================
const mm = gsap.matchMedia();

mm.add("(prefers-reduced-motion: reduce)", () => {
    // 为偏好减少动画的用户禁用复杂动画
    gsap.globalTimeline.timeScale(3);
});

mm.add("(max-width: 1024px)", () => {
    // 移动端调整
    ScrollTrigger.refresh();
});

// ==================== 页面加载完成 ====================
window.addEventListener('load', () => {
    ScrollTrigger.refresh();
    animateBridgeLine();
});

// ==================== 性能优化 ====================
// 节流滚动事件
let ticking = false;
window.addEventListener('scroll', () => {
    if (!ticking) {
        window.requestAnimationFrame(() => {
            ticking = false;
        });
        ticking = true;
    }
}, { passive: true });
