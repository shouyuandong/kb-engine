# 增量编译触发规则

## 核心原理

Karpathy LLM Wiki 的核心是增量编译——新 raw 进来，只重编受影响的部分。LLM 怎么知道哪些文件受影响了？**算 raw 文件的 md5，和上次比对，没变的跳过。**

## md5 vs git

| | md5 | git |
|--|-----|-----|
| 回答的问题 | "这个文件变没变？" | "这个文件每次变成了什么？" |
| 信息量 | 布尔值（变/没变） | 完整历史链 |
| 用在哪 | raw 层（增量触发） | wiki 层（版本管理） |

两者不是替代关系，各管一摊。

## 执行逻辑

```python
# 伪代码
for f in raw_files:
    current_md5 = md5sum(f)
    if current_md5 != last_hash[f]:
        changed_files.append(f)
    last_hash[f] = current_md5

# 只编译 changed_files，跳过未变的
```

## md5 哈希记录

- 存储位置：`{领域}/.cache/md5_hashes.json`
- 格式：`{"文件路径": "md5值"}`
- 每次编译后更新

## 不靠谱的用途

让 LLM 算 md5 来"检测自己有没有篡改已审核内容"——这不靠谱，因为 LLM 要篡改就能连 md5 记录一起改。已审核内容的保护应该从权限上隔离（`_目录配置.json` 的 `writable` 字段），而不是事后校验。

---

> **适用范围**：所有策略的 raw → wiki 编译流程
> **依赖脚本**：`scripts/incremental_check.py`
