# AI Radar 每日 AI 情报站

AI Radar 是一个面向 AI 开发者、产品经理和内容创作者的中英文 AI 动态速览站。它从公开 RSS 获取标题、短摘要、来源、原始发布时间和原文链接；页面按北京时间提供今日、最近 7 天、来源、语言和关键词筛选。

## 功能

- 真实 RSS 采集：爱范儿、钛媒体、Google AI、OpenAI News。
- 增量合并：RSS 只返回最近窗口，旧快照不会被覆盖。
- 确定性去重：规范化 URL、guid、同来源标题指纹。
- 可信日期：区分发布时间和采集时间；无法判断时显示“发布时间未知”。
- 容错：单源失败不影响其他来源；所有来源失败时保留旧数据。
- 今日速览：按北京时间当天和来源多样性最多选 6 条。
- 搜索与筛选：关键词、来源、语言、今天、最近 7 天、未知时间。
- GitHub Actions：每 30 分钟自动触发一次，也支持手动运行；主分支更新会触发一次发布作为兜底。

## 本地运行

需要 Python 3.12+、Node.js 22+。

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-dev.txt
python -m collector.healthcheck --real
python -m collector.update --output data/snapshot.json --bootstrap bootstrap/snapshot.json
```

启动网站：

```bash
cd web
npm ci
npm run dev
```

打开终端提示的本地地址即可。构建：

```bash
npm run build
```

## 测试

```bash
python -m pytest -q
```

真实源烟雾测试：

```bash
python -m collector.healthcheck --real
python -m collector.smoke_test --real
```

离线 fixture 测试不会把模拟数据当作真实资讯。真实源的当前可用性单独记录在 `verification/`。

## 数据来源和边界

当前启用来源：

| 来源 | 类型 | 语言 | RSS |
|---|---|---|---|
| 爱范儿 | 第三方科技媒体 | 中文 | https://www.ifanr.com/feed |
| 钛媒体 | 第三方科技媒体 | 中文 | https://www.tmtpost.com/rss |
| Google AI | 官方 / 研究发布 | English | https://blog.google/technology/ai/rss/ |
| OpenAI News | 官方发布 | English | https://openai.com/news/rss.xml |

独立来源按不同 `publisher_id` 和内容发布主体判断。页面只展示来源 RSS 实际提供的标题和短摘要，不抓全文、不绕过登录或付费墙、不重新托管原站图片。使用时应遵守各来源当前 RSS 条款；TechCrunch 等来源对 RSS 使用有明确归属和原文链接要求，可见其 RSS 条款页面。

## 日期口径

- 存储使用 UTC，页面使用 `Asia/Shanghai`（北京时间）。
- “今天”是北京时间当天 00:00 至当前时间。
- “最近 7 天”是今天及之前 6 个北京时间自然日。
- 原始时间无法可靠解析时显示“发布时间未知”，不会用采集时间冒充发布时间。
- 文章按发布时间或首次发现时间保留 30 天；RSS 暂时不再返回不代表文章被删除。

## 更新方式

- 本地：`python -m collector.update --output data/snapshot.json --bootstrap bootstrap/snapshot.json`
- GitHub Actions：Actions → `publish-ai-radar` → Run workflow。
- 首次部署：在手动运行表单中将 `bootstrap` 设为 `true`；首次成功发布后，后续定时任务只读取线上快照，读取失败会停止发布而不会回退覆盖旧页面。
- 如果使用自定义 Pages 域名，可在仓库 Variables 中设置 `PAGES_BASE_URL`；如果站点部署在非根路径，再设置对应的 `PAGES_BASE_PATH`（例如 `/ai-radar`）。
- 定时：每 30 分钟触发一次（GitHub Actions 使用 UTC，表达式为 `7,37 * * * *`，刻意错开整点高峰）。实际启动可能延迟，不保证精确到分钟；并发运行由 workflow 锁串行处理。
- 兜底发布：`main` 分支更新也会触发发布，避免工作流调整后必须等待下一次定时窗口。
- 页面刷新：页面上的“刷新数据”会立即重新读取最新已发布快照，并把“同步状态”更新为本次页面读取时间；文章内容只有在 GitHub Actions 采集并发布后才会变化。它不会在浏览器中直接启动 RSS 采集，需要立即采集时请在 GitHub Actions 中手动运行 `publish-ai-radar`。
- GitHub Pages 工作流从当前已部署的 `data/snapshot.json` 读取旧状态，合并新 RSS 后重新构建；运行数据不提交 Git，不使用数据库或 Release Asset。

首次部署时才允许使用 `bootstrap/snapshot.json`。后续线上快照读取失败会停止本次发布，避免用空数据覆盖线上内容。

## 已知限制

- RSS 可能临时失效、限流或改变字段；页面会显示具体来源状态。
- GitHub Actions 和 GitHub Pages 存在调度与构建延迟。
- 当前只保留 30 天数据，不提供长期归档、账号、评论、全文、自动翻译或 AI 生成摘要。
- 宽泛中文来源使用可解释的相关性过滤，低置信条目会在运行统计中记录。

## 开源技术

- Astro：静态内容站点构建。
- feedparser：RSS / Atom 解析。
- python-dateutil：日期解析和时区处理。
- pytest：离线和异常场景测试。
- GitHub Actions / GitHub Pages：定时更新与静态部署。

## 成本

默认不需要付费 API。公开仓库使用 GitHub Actions 和 GitHub Pages 的免费能力；实际额度和来源条款以平台当前规则为准。

## 在线演示

部署完成后访问：[AI Radar 在线站点](https://xingchenCY.github.io/ai-radar/)

更多决策、验证结果和未完成事项见 `DEVELOPMENT.md`、`VERIFICATION.md`。
