# KB Engine · 知识库引擎

一套基于「策略即数据」理念的多策略个人知识库引擎。引擎只管流程，规则写在 `strategies/` 的 markdown 模板里，每个领域的实际目录由 `config.json` 决定，文件搬运交给 Python 脚本，LLM 负责理解意图与编译内容。

> 核心思想：**策略是数据（模板），不是代码（逻辑）。** 新增一种知识类型，只需加一个策略模板 + 在索引里注册一行，无需改引擎代码。

---

## 安装说明

### 1. 环境要求

| 依赖 | 版本 | 说明 |
|---|---|---|
| Python | 3.8+ | 脚本基于标准库（`argparse` / `pathlib` / `hashlib` / `subprocess` 等） |
| PyYAML | 任意较新版本 | **仅**「清理灵感库」命令（`clean_inbox.py`）需要；其余命令纯标准库 |
| Git | 可选 | 用于 wiki 层版本管理与变更记录（`migrate` / `seal` 会调用 `git`） |

安装 PyYAML（如只需基础命令可跳过，用到时再装）：

```bash
pip install pyyaml
# 或在隔离环境：python -m venv .venv && .venv/bin/pip install pyyaml
```

### 2. 获取代码

```bash
git clone https://github.com/shouyuandong/kb-engine.git
cd kb-engine
```

（或直接复制整个 `kb-engine/` 目录到本地任意位置。）

### 3. 作为 Skill 安装（供 WorkBuddy / Claude Code 等 agent 调用）

本目录本身就是一个符合 skill 格式的包（`SKILL.md` 为入口）。放到 skill 目录即可被 agent 识别：

- **用户级**（所有项目可用）：
  ```
  ~/.workbuddy/skills/kb-engine/
  ```
- **项目级**（仅当前项目可用）：
  ```
  <你的项目>/.workbuddy/skills/kb-engine/
  ```

把整个 `kb-engine/` 目录拷贝到上述位置即可，**无需额外构建步骤**。

> 说明：agent 通过自然语言指令（如「帮我把这条笔记归档」）触发 `SKILL.md` 里定义的 `/kb` 命令，再由 LLM 调用 `scripts/` 下的 Python 脚本执行。

### 4. 初始化你的第一个知识库领域

选定一个**知识库根目录**（存放所有领域，下文记为 `<KB_ROOT>`），例如 `~/kb` 或项目内的 `demo-kb/`。

注册领域到策略索引 `config/strategy-index.yml`（`domains:` 下加一行 `领域名: 策略字母`）：

```yaml
domains:
  育儿: A        # 持续积累型
  工作: E        # 周期运营型
  # 交易: C      # 时效腐烂型（取消注释即启用）
```

然后运行初始化（生成 `config.json` + 创建目录结构）：

```bash
# 直接用脚本（推荐，参数明确）
python scripts/init_domain.py --domain 育儿 --strategy A --yes --base-dir <KB_ROOT>

# 只预览将要创建的目录与编译规则、不落盘：
python scripts/init_domain.py --domain 育儿 --strategy A --dry-run --base-dir <KB_ROOT>
```

- `--yes`：直接执行（agent 调用即视为已授权）
- `--dry-run`：只打印计划，不创建任何文件

初始化后 `<KB_ROOT>/育儿/` 下会出现带 `00-` 数字前缀的目录与 `config.json`。

### 5. 中文 Windows 注意事项

脚本已内置 UTF-8 输出重绑，在 GBK 终端（中文 Windows 默认）也能正常运行，无需手动设置环境变量。如仍遇到编码问题，可在运行前执行：

```bash
set PYTHONIOENCODING=utf-8
```

---

## 快速开始

```bash
# 1) 初始化一个「持续积累」领域
python scripts/init_domain.py --domain 读书 --strategy A --yes --base-dir ~/kb

# 2) 把一篇笔记丢进 00-原始资料/，然后触发编译（增量检测变更）
python scripts/compile.py --domain 读书 --base-dir ~/kb
#   → 脚本检测变更、解析编译规则、检查写权限，打印路径供 LLM 生成知识卡片草稿

# 3) 健康检查（lint）
python scripts/lint.py --all --base-dir ~/kb
```

在 agent 对话中，等价地用自然语言即可：

```
/kb init 读书          # 或「初始化一个读书知识库」
/kb build 某笔记.md     # 或「帮我处理这条笔记」
/kb maintain            # 或「做一下知识库维护」
/kb migrate 读书        # 或「读书领域的目录结构要调整，帮我迁移」
```

---

## 命令速查

| 命令 | 对应脚本 | 作用 | 常用参数 |
|---|---|---|---|
| `/kb init [domain]` | `scripts/init_domain.py` | 初始化新领域（生成 `config.json` + 目录） | `--strategy A-E` `--yes` `--dry-run` `--base-dir` `--season-transition` |
| `/kb build [file]` | `scripts/compile.py` | 增量检测 raw 变更，解析编译规则与路径 | `--file`（指定单文件）`--base-dir` |
| `/kb migrate [domain]` | `scripts/migrate.py` | diff 新旧 `config.json`，批量搬家 + 更新链接 + git 提交 | `--dry-run` `--base-dir` |
| `/kb maintain` | `scripts/lint.py` 等 | lint 健康检查 / 清理灵感库 / 检测更新 / 归档 | `--all` `--base-dir` |

辅助脚本：`archive.py`（归档）、`seal.py`（封存主题）、`check_updates.py`（检测更新）、`clean_inbox.py`（清理灵感库，需 PyYAML）、`generate_report.py`（生成报告）、`incremental_check.py`（md5 增量，被 `compile.py` 调用）。

---

## 目录结构

```
kb-engine/
├── SKILL.md                    ← 引擎总纲（agent 入口）
├── README.md                   ← 本文档
├── strategies/                 ← 策略模板（A~E 五套规则定义）
├── templates/                  ← 产出模板（知识卡片等填空用）
├── rules/                      ← 公共规则（跨策略共享，如 lint / 换季 / 增量编译）
├── config/
│   ├── strategy-index.yml      ← 领域 → 策略 映射（注册入口）
│   └── directory-config-template.json
├── scripts/                    ← Python 脚本（核心逻辑，被 agent 调用）
└── lib/                        ← 共享模块（config_loader / file_ops / git_ops / strategy_router）
```

> 注意：`demo-kb/`（演示数据）与 `.workbuddy/`（记忆）已在 `.gitignore` 中排除，不属于发布内容。

---

## 常见问题

**Q：运行 `clean_inbox.py` 报 `ModuleNotFoundError: yaml`？**
A：安装 PyYAML：`pip install pyyaml`。这是唯一依赖第三方库的命令。

**Q：命令调用要确认吗？**
A：不需要。`input()` 二次确认已全部移除——agent 调用命令即视为已授权。破坏性动作（如 `migrate` 搬家）默认执行，可加 `--dry-run` 预览。

**Q：目录名前面的 `00-` 是什么？**
A：数字前缀仅用于文件管理器排序，是物理目录名（`path`）。LLM 与脚本内部统一用**逻辑名**（如「知识卡片」）引用，`config.json` 负责映射，所以加前缀不影响任何编译/链接逻辑。

**Q：改目录结构后链接会断吗？**
A：用 `/kb migrate` 迁移，脚本会批量更新所有 wikilink 并提交 git，不会断链。
