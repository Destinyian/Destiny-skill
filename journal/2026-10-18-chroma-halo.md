# 2026-10-18 - 第一张动效卡：光标墨迹晕

## 请求

读 React Bits Pro 的 Chroma Halo 文档页，按新规则总结成 skill，并给另一个 AI 一份"相同特效"的
自创实现方案（只要方案，不要代码）。

## 怎么看到的

文档站是 JS 渲染的，静态抓取只有导航壳。`curl` 拿不到，`--dump-dom` 也拿不到预览——预览在一个
无 `src` 的同文档 iframe 里。

1. 用 `render-it-or-you-are-guessing/scripts/render-page.js` 真实渲染，拿到 1440×900 截图与正文。
2. 无头 Chromium 在 workspace-write 沙箱下起不来（mojo 命名管道被拒、crashpad 无法启动），
   这一条本身又是一个 `the-probe-lies` 的实例：不是浏览器坏了，是探针被拦了。
3. 用 CDP 枚举 frame：预览是同文档 iframe，画布 1045×600、`webgl2`。
4. 组件代码在动态 chunk `15819`（25 KB），13 个着色器程序、6 个 pass、4 次 Jacobi。

## 它到底是什么

不是"跟着光标的高斯光晕"，是**低分辨率稳定流体**：splat 注入速度与染料，半拉格朗日平流，
散度→压力→减梯度，两个时间常数分别衰减速度与染料，最后 0.25× 上采样 + CSS `blur(8px)` +
multiply/screen 混合。

关键证据是抓帧：快速斜扫后 t0 保留整条路径，t400 只剩笔头，t1200 完全干净。这证明"记忆"是
真的，不是模糊。

## 产出

- 卡片 `the-halo-remembers-the-cursor/`（`kind: effect`，`trigger_family: pointer`，
  surfaces `hover` + `idle`，maturity `draft`），含 `assets/swipe-t0.png`、`swipe-t400.png`。
- 方案（**不入库**，在桌面 `Chroma-Halo-实现方案.md`）：CPU 半拉格朗日路线（不是 WebGL），6 条验收、
  参数表、状态机、陷阱清单。选 CPU 是刻意的——本方案的价值是"别人能照着重做"，而 WebGL 版
  容易滑成"照着原实现再写一遍"。
- 规则侧同步：CONVENTIONS §11 的 effect 行、README 的"第一张动效卡"。

## 验证

- `check`：0 error / 0 warning / 9 skills（新卡一次通过 E17 + E19 + W08–W10）。
- 帧率：Intel Arc iGPU 120 fps（8.3 ms mean / 8.4 ms p95，180 帧）；软件光栅 60 fps（16.8 ms）。
- 这些数字是 vsync-held 的上界，不是成本本身——卡里已写明。

## 没做

- 没有 field-test：这张卡只在一个页面上观察过，成熟度停在 `draft`，等第二个页面用。
- 没有 hub：motion cluster 只有 1 张卡，E16 需要 2+ 子卡。
- 没有把方案写成代码：用户要的是方案，实现交给另一个 AI。
