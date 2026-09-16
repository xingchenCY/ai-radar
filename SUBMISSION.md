# AI Radar 提交信息

姓名：待填写（当前 GitHub 账号：`xingchenCY`）

实际投入时间：约 8 小时。记录为：需求和来源验证 45 分钟，采集器和数据合并 110 分钟，前端页面和筛选 150 分钟，自动化部署 55 分钟，测试、修复和文档 120 分钟。

演示地址：[https://xingchency.github.io/ai-radar/](https://xingchency.github.io/ai-radar/)

源码地址：[https://github.com/xingchenCY/ai-radar](https://github.com/xingchenCY/ai-radar)

已验证：4 个真实 RSS 来源、重复导入幂等、URL/guid/标题指纹去重、单源失败隔离、全源失败保留旧数据、缺失日期、搜索筛选、移动端页面、GitHub Actions 手动触发、真实 `schedule` 运行和 GitHub Pages 部署。

未完成或未验证事项：GitHub Actions 的定时任务不能保证严格每 30 分钟准点，虽然已经出现成功的 `schedule` 运行；真实源长期持续故障下的线上保留旧数据演练尚未执行。页面刷新只读取最新已发布快照，不直接启动采集任务。

主要交付文件：

- `README.md`：本地运行、部署、来源、更新方式、限制和成本。
- `DEVELOPMENT.md`：实际投入时间、开发工具、关键决策和问题定位。
- `VERIFICATION.md`：真实源、fixture、自动任务和 Pages 的验证记录。
- `.github/workflows/publish.yml`：定时、手动和主分支兜底发布配置。
