## MODIFIED Requirements

### Requirement: 异步 PDF 处理
系统 SHALL 在论文入库后，自动提交异步任务下载 PDF、提取全文，并触发后续论文处理生命周期。

#### Scenario: 自动触发 PDF 下载
- **WHEN** 新论文入库且 `auto_download=true`
- **THEN** 自动向 Celery 提交 PDF 下载任务
- **AND** 下载完成后提交 PDF 解析任务
- **AND** 解析结果（全文文本）写入 Paper.full_text 字段
- **AND** 后台处理生命周期继续补齐结构化解析、视觉证据/OCR、向量和检索索引状态。

#### Scenario: PDF 下载失败处理
- **WHEN** PDF 下载失败（网络错误、文件不存在等）
- **THEN** Paper.pdf_path 保持为 NULL
- **AND** 任务状态记录失败原因
- **AND** 后台处理生命周期保留可恢复状态，等待后续 PDF 可用后继续处理。
