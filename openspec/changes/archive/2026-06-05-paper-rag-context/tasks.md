## 1. 论文分块服务

- [x] 1.1 创建 `app/services/paper_chunk_service.py`
- [x] 1.2 实现 `chunk_full_text` — 按段落切分，500-1000 字符/chunk
- [x] 1.3 实现 `search_chunks` — BM25 关键词检索 + 关键词降级
- [x] 2.1 重构 `memory_service.py` `build_paper_context`
- [x] 2.2 Metadata 始终包含
- [x] 2.3 降级策略：无全文→摘要，短全文→直接使用
- [x] 3.1 语法验证通过
