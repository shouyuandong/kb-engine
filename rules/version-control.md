# 版本管理规则

## 核心原则

**raw 层用 md5 做增量触发，wiki 层用 git 做版本管理。** 两者共存，不二选一。

## git 管什么

- **wiki 层的编译产出**：LLM 编译产出的 wiki 文件，进 git 版本控制
- **原因**：wiki 会被 LLM 反复改写，需要能回溯"上次编译出来的是什么样"，改坏了能回滚

## git 不管什么

- **raw 层**：raw 是输入，用 md5 做增量判断即可，不需要 git 的完整历史
- **附件**（ppt/html/pdf）：体积大，建议用 git-lfs 或单独备份

## 提交规则

| 操作 | 提交信息格式 | 频率 |
|------|------------|------|
| 编译 | `[compile] 领域名: 简述` | 每次编译后 |
| 迁移 | `[migrate] 领域名: 旧路径→新路径` | 每次迁移后 |
| 封存 | `[seal] 主题名` | 封存时 |
| 归档 | `[archive] 领域名: N条过期判断` | 归档时 |
| 人工编辑 | `[manual] 简述` | 人手动修改后 |

## 权限隔离

- `config.json` 的 `writable: false` 的目录，LLM 只读不写
- 已审核内容（`verified: true`）的文件，LLM 只读不写
- LLM 只能写 `writable: true` 的目录，且只能写草稿区（`draft_dir`）

## 回滚

```bash
# 查看某次编译前的状态
git log --oneline --grep="compile"
git checkout <commit-hash> -- wiki/

# 回滚整个 wiki 到某个时间点
git checkout <commit-hash> -- wiki/
```

---

> **适用范围**：所有策略的 wiki 层
> **依赖模块**：`lib/git_ops.py`
