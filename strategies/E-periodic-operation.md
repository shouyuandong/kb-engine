# 策略 E：周期运营型

## 适用场景

高频自动流入的工作流水，需要周期性生成报告、追踪指标、提醒风险，同时沉淀可复用经验。是 A+C 的混合：流水层像 C（归档），沉淀层像 A（积累）。

**典型场景**：工作项目管理、团队运营、Bug 处理与经验蒸馏、KPI 追踪

**核心特征**：有节奏的周期产出（日报/周报/月报/年报）+ 实时提醒 + 经验沉淀。自动采集是命脉——手动记录的东西三天就会放弃。

## 六维度定义

| 维度 | 定义 |
|------|------|
| 生命周期 | 持续型，但内部有项目周期（项目结束封存） |
| 内容流入 | 高频自动流入（代码提交、缺陷系统、会议纪要） |
| 核心产出 | 三层：周期报告 + 实时提醒（待办/风险）+ 经验沉淀 |
| 谁写什么 | LLM 编译流水、生成报告、打标签；人定 KPI、审核报告、提炼经验 |
| 时效处理 | 流水按周期归档；经验沉淀不失效 |
| 退出机制 | 项目封存写总结；经验保留 |

## 目录配置（逻辑名）

```json
{
  "directories": {
    "原始流水": { "maintainer": "manual", "writable": false },
    "提交记录": { "maintainer": "auto", "writable": true },
    "缺陷记录": { "maintainer": "auto", "writable": true },
    "会议纪要": { "maintainer": "manual", "writable": false },
    "每日记录": { "maintainer": "manual", "writable": false },
    "周报": { "maintainer": "llm_draft_human_review", "writable": true, "draft_dir": "周报/.草稿" },
    "月报": { "maintainer": "llm_draft_human_review", "writable": true, "draft_dir": "月报/.草稿" },
    "年报": { "maintainer": "llm_draft_human_review", "writable": true, "draft_dir": "年报/.草稿" },
    "项目": { "maintainer": "human", "writable": false },
    "指标": { "maintainer": "llm_draft_human_review", "writable": true, "draft_dir": "指标/.草稿" },
    "经验": { "maintainer": "llm_draft_human_review", "writable": true, "draft_dir": "经验/.草稿" },
    "附件": { "maintainer": "manual", "writable": false },
    "配置": { "maintainer": "manual", "writable": false }
  },
  "compile_rules": [
    { "input": "原始流水", "output": "周报", "rule": "按周编译，生成周报草稿" },
    { "input": "周报", "output": "月报", "rule": "按月汇总周报，生成月报草稿" },
    { "input": "缺陷记录", "output": "经验", "rule": "提炼踩坑模式，进经验草稿区" },
    { "input": "原始流水", "output": "指标", "rule": "按指标定义提取数据，更新追踪表" }
  ]
}
```

## 六个关键设计点

### 1. 数据采集自动化

代码提交和缺陷记录应该是脚本自动拉取，不是手动记录。

```bash
# 自动拉取提交记录
git log --since="1 day ago" --pretty=format:"%h %ad %s" --date=short

# 自动拉取缺陷记录（需配置 API）
curl "http://bug-tracker/api/bug?assigned_to=me&last_change_time=YYYY-MM-DD"
```

### 2. KPI 闭环

KPI 不是静态记录，是动态追踪。形成闭环：目标 → 进展 → 差距 → 风险 → 归因。

### 3. 风险提醒规则化

风险不能靠 LLM 凭空判断。用户在 `{配置}/risk-rules.yml` 定义规则，LLM 执行匹配。

### 4. 报告反向写回

报告生成后，关键结论要写回 wiki：
- 处理的缺陷 → 提炼成 `{经验}` 下的踩坑模式
- 项目进展 → 更新 `{项目}` 的状态
- 指标变化 → 更新 `{指标}` 的追踪表

### 5. 经验沉淀

缺陷处理记录不只是流水，要提炼成可复用的模式。这一层可以和其他系统（如 Bug 蒸馏系统）打通。

### 6. 项目封存

项目结束时封存，写项目总结（交付物/踩坑提炼/指标达成/可复用模式）。经验保留，不随项目封存。

## 时效处理

- 原始流水按周期归档（如月度归档）
- 周报/月报生成后不修改，作为历史快照
- 经验沉淀不失效，持续积累
- 项目封存后只读

## Lint 检查项

- KPI 连续低于目标的
- 项目超期未封存的
- 原始流水是否连续（有无断天）
- 经验区是否有可提炼但未提炼的缺陷记录
- 报告是否按周期生成（有无断周/断月）
- 风险规则是否命中但未提醒

## 产出模板

| 模板 | 用途 |
|------|------|
| `templates/weekly-report.md` | 周报（含附件链接+反向写回标记） |
| `templates/monthly-report.md` | 月报（汇总+指标更新） |
| `templates/yearly-report.md` | 年报（年度经验提炼） |
| `templates/kpi-tracking.md` | KPI 追踪表（目标→进展→差距→趋势） |
| `templates/experience-pattern.md` | 经验模式（触发场景+排查路径+复用记录） |
| `templates/project-summary.md` | 项目总结（封存产出） |
| `templates/inbox-item.md` | 灵感库条目（公共） |
