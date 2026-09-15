# 验证记录

状态只使用：已验证、未验证、未完成。模拟 fixture 与真实 RSS 始终分开。

| 验证项 | 方法 | 状态 | 证据 |
|---|---|---|---|
| 至少两个不同 publisher 的真实来源 | `healthcheck --real` | 已验证 | `verification/real-source-health-2026-09-15.json`，4/4 来源 HTTP 200 |
| 真实 RSS 增量合并 | `smoke_test --real` | 已验证 | `verification/real-source-smoke-2026-09-15.json`，4 个来源完成解析 |
| 固定输入重复导入，记录数不增长 | pytest | 已验证 | `tests/test_merge_snapshot.py`，当前 25 passed |
| URL 追踪参数、guid、标题指纹去重 | pytest | 已验证 | `tests/test_identity.py`、`tests/test_merge_snapshot.py` |
| 单个来源失败仍继续采集其他来源 | fake response / fixture | 已验证 | `tests/test_failure_recovery.py`；失败源名称写入 source state |
| 429 Retry-After、503 退避、403 不重试 | pytest | 已验证 | `tests/test_failure_recovery.py` |
| 所有来源失败不清空旧数据 | pytest | 已验证 | `tests/test_merge_snapshot.py::test_all_sources_failed_keeps_old_articles` |
| 缺少发布时间、日期置信度修正 | pytest + 页面 | 已验证 | `tests/test_dates.py`、页面文案“发布时间未知” |
| 30 天保留和未知日期按首次发现裁剪 | pytest | 已验证 | `tests/test_merge_snapshot.py::test_retention_uses_first_seen_for_unknown_dates` |
| HTML 摘要安全转换、脚本不执行 | pytest + 页面 | 已验证 | `tests/test_plain_text.py`；摘要推广尾巴会被清洗 |
| 长标题、无摘要、无效 URL | fixture + 页面 | 已验证 | `tests/test_parse_feed.py`、`tests/test_plain_text.py`、响应式 CSS |
| 搜索无结果、组合筛选、清除条件 | 浏览器手工操作 | 已验证 | 本地站点交互核验 |
| 浏览器前进后退恢复筛选 | 浏览器手工操作 | 已验证 | `pushState` / `replaceState` / `popstate` |
| 重试按钮 | 人为阻断快照请求后点击重试 | 已验证 | 进入“读取中”，请求完成后恢复成功或显示错误；按钮防重复点击 |
| 加载更多终止状态 | 浏览器手工操作 | 已验证 | 最后一页按钮保留但禁用并显示“已显示全部资讯” |
| 主题筛选抽样 | 当前快照统计 + 3 条抽样 | 已验证 | 大模型 37、Agent 4、AI 应用 1、开发工具 8、芯片与算力 8、政策与安全 14、研究 7；抽样与关键词一致 |
| 每 30 分钟定时配置 | workflow 静态检查 | 已验证 | `.github/workflows/publish.yml` 使用 `*/30 * * * *` |
| 手动 GitHub Actions 实际运行 | `workflow_dispatch` | 未验证 | 需要绑定用户仓库后运行 |
| GitHub Pages 可访问 | 浏览器 | 未验证 | 当前只有本地 `127.0.0.1`，尚无公开地址 |

## 构建结果

- `python -m pytest -q`：25 passed。
- `cd web && npm run build`：Astro 构建成功。
- 移动端检查：375px 视口无横向溢出；主题和来源标签可横向滚动。

## 运行记录格式

真实运行保留：执行时间、触发方式、来源 URL、HTTP 状态、Content-Type、解析条数、最终状态、旧文章数、新文章数和页面版本。当前探测结果见 `verification/real-source-health-2026-09-15.json`，对应日志见同名 `.log`。

## 已知外部限制

RSS 可能临时失效、限流或改变字段；GitHub Actions 的半小时 cron 可能延迟；Pages 发布可能延迟。外部依赖失败不会被写成代码通过，也不会被伪造成业务数据。

## 最终提交信息

| 项目 | 当前状态 |
|---|---|
| 本地项目目录 | `/Users/wangzihao/Desktop/面试题` |
| GitHub 仓库 | 已验证：`https://github.com/xingchenCY/ai-radar`，公开仓库，`main` 分支 |
| GitHub commit | 已验证：`bfab077`，workflow 修复与 Pages 配置提交 |
| GitHub Pages 地址 | 已验证：`https://xingchency.github.io/ai-radar/`，首页 HTTP 200 |
| `workflow_dispatch` 实际运行记录 | 已验证：运行 `34986704274`，2026-09-15 23:11（北京时间）触发，成功 |
| 每 30 分钟定时任务实际触发记录 | 未验证：已验证 workflow 配置，尚未等待一个真实半小时 cron 周期 |

### 未验证事项

1. 每 30 分钟 cron 在真实 GitHub Actions 环境中的首次自动触发时间。
2. 长期运行中外部 RSS 临时失败后的 Pages 保留旧数据行为。

## 真实首次部署记录

- 首次尝试：运行 `34984429518`，失败原因是未勾选 `bootstrap=true`，线上尚无旧快照，工作流按保护逻辑拒绝发布。
- 第二次尝试：运行 `34984892761`，采集、测试和 Astro 构建成功；因仓库 Pages 尚未启用，`configure-pages` 无法创建 Pages site。
- 修复：在仓库设置中将 Pages Source 切换为 `GitHub Actions`，并保留 workflow 的 `enablement: true` 兼容配置。
- 成功运行：运行 `34986704274`，使用提交 `bfab077`，真实采集、pytest、Astro build、artifact 上传和 Pages deploy 全部成功。
- 线上快照：`https://xingchency.github.io/ai-radar/data/snapshot.json`，HTTP 200，99 条文章，`overall_status=success`，`generated_at=2026-09-15T15:11:13Z`。
