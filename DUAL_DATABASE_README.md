# 双数据库架构说明

## 概述

本项目采用双数据库架构，分别存储舆情数据和分析结果数据，实现数据分离和性能优化。

## 数据库结构

### 1. 舆情数据库 (sentiment_analysis.db)

**用途**: 存储原始舆情数据，包括新闻、公告、报告等文本内容

**位置**: `data/sentiment_analysis.db`

**主要表结构**:
- `sentiment_data`: 舆情数据主表
- `field_config`: 字段配置表

**数据特点**:
- 原始文本数据
- 基础情感分析结果
- 风险标签
- 企业信息
- 行业分类

### 2. 结果数据库 (resultdatabase.db)

**用途**: 存储系统分析产生的结果数据，包括深度分析、LLM分析结果等

**位置**: `data/resultdatabase.db`

**主要表结构**:
- `analysis_results`: 分析结果主表
- `sentiment_results`: 情感分析结果表
- `tag_results`: 标签分析结果表
- `company_results`: 企业识别结果表
- `analysis_statistics`: 分析统计表

**数据特点**:
- 分析结果数据
- 置信度评分
- 处理时间统计
- 模型使用记录
- 去重机制（基于文本哈希）

## 架构优势

### 1. 数据分离
- **舆情数据库**: 存储大量原始数据，支持历史查询
- **结果数据库**: 存储分析结果，支持快速检索和统计

### 2. 性能优化
- 分析结果独立存储，避免影响原始数据查询性能
- 结果数据库支持索引优化，提高查询速度
- 支持结果缓存和去重

### 3. 扩展性
- 可以独立扩展每个数据库的存储策略
- 支持不同的备份和清理策略
- 便于后续功能扩展

## 使用方法

### 1. 启动双数据库系统

```bash
python start_dual_database.py
```

### 2. 测试双数据库系统

```bash
python test_dual_database.py
```

### 3. 使用统一数据库管理器

```python
from database_manager import UnifiedDatabaseManager

# 创建统一管理器
unified_db = UnifiedDatabaseManager()

# 获取数据库状态
status = unified_db.get_database_status()

# 获取综合统计
stats = unified_db.get_combined_statistics()

# 备份数据库
backup_result = unified_db.backup_databases()

# 清理旧数据
cleanup_result = unified_db.cleanup_old_data()
```

### 4. 直接使用结果数据库

```python
from result_database import ResultDatabaseManager

# 创建结果数据库管理器
result_db = ResultDatabaseManager()

# 存储分析结果
analysis_id = result_db.store_analysis_result(
    original_text="分析文本",
    analysis_response=analysis_response,
    processing_time_ms=1500,
    llm_model="model_name"
)

# 查询分析结果
result = result_db.get_analysis_result(text_hash)

# 获取统计信息
stats = result_db.get_sentiment_statistics()
```

## 数据流程

```
原始文本 → 舆情数据库 (存储)
    ↓
系统分析 → 结果数据库 (存储分析结果)
    ↓
查询展示 ← 双数据库联合查询
```

## 维护操作

### 1. 数据库备份

```python
# 自动备份
unified_db.backup_databases("data/backup")

# 手动备份
import shutil
shutil.copy2("data/sentiment_analysis.db", "backup/sentiment_backup.db")
shutil.copy2("data/resultdatabase.db", "backup/result_backup.db")
```

### 2. 数据清理

```python
# 清理舆情数据库旧数据（保留90天）
sentiment_cleaned = unified_db.cleanup_old_data(sentiment_days=90)

# 清理结果数据库旧数据（保留30天）
result_cleaned = unified_db.cleanup_old_data(result_days=30)
```

### 3. 数据库监控

```python
# 获取数据库状态
status = unified_db.get_database_status()

# 验证数据库完整性
integrity = unified_db.validate_database_integrity()

# 获取综合统计
stats = unified_db.get_combined_statistics()
```

## 注意事项

1. **数据一致性**: 两个数据库的数据需要保持逻辑一致性
2. **备份策略**: 建议定期备份两个数据库
3. **性能监控**: 定期检查数据库性能和存储空间
4. **错误处理**: 系统会自动处理数据库连接错误和查询异常

## 故障排除

### 常见问题

1. **数据库文件不存在**
   - 检查 `data/` 目录是否存在
   - 运行初始化脚本

2. **表结构错误**
   - 删除数据库文件重新初始化
   - 检查数据库版本兼容性

3. **性能问题**
   - 检查索引是否正确创建
   - 清理旧数据释放空间
   - 优化查询语句

### 日志查看

系统会记录详细的日志信息，包括：
- 数据库操作日志
- 错误和异常信息
- 性能统计信息

查看日志文件或控制台输出来诊断问题。

## 更新日志

- **v1.0**: 初始双数据库架构
- **v1.1**: 添加统一数据库管理器
- **v1.2**: 优化性能和错误处理
- **v1.3**: 添加数据清理和备份功能
