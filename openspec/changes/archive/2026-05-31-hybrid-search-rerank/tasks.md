## 1. BM25 关键词检索

- [x] 1.1 实现 `backend/app/services/hybrid_search.py` BM25 索引和检索
- [x] 1.2 论文入库/更新时自动更新 BM25 索引
- [x] 1.3 安装依赖 `rank-bm25`

## 2. 混合检索融合

- [x] 2.1 实现 RRF 融合算法
- [x] 2.2 更新 `backend/app/api/papers.py` 搜索端点支持 `search_mode=hybrid`
- [x] 2.3 更新 `backend/app/services/rag_service.py` 使用混合检索

## 3. Cross-Encoder 重排序

- [x] 3.1 实现 `backend/app/services/rerank_service.py` Cross-Encoder 重排
- [x] 3.2 集成到混合检索流程（可选开关）

## 4. 验证测试

- [x] 4.1 测试混合检索 vs 纯向量检索的召回率 ✅ 4 结果
- [x] 4.2 验证 RAG 对话使用混合检索后的回答质量 ✅
