# 数据库架构说明

## 概述

本系统采用双数据库架构，确保数据源和分析结果的清晰分离，避免数据冲突和混淆。

## 数据库结构

### 1. 舆情数据库 (Sentiment Database)
- **文件路径**: `data/sentiment_analysis.db`
- **用途**: 测试数据库，存储原始舆情数据
- **功能**: 作为分析任务的数据源
- **管理类**: `DatabaseManager` (在 `database.py` 中)
- **表结构**: 
  - `sentiment_data`: 原始舆情数据
  - `field_config`: 字段配置

### 2. 分析结果数据库 (Analysis Results Database)
- **文件路径**: `data/analysis_results.db`
- **用途**: 结果数据库，存储系统分析完成的结果数据
- **功能**: 存储分析任务的输出结果
- **管理类**: `ResultDatabaseManager` (在 `result_database.py` 中)
- **表结构**:
  - `analysis_tasks`: 分析任务记录
  - `analysis_results`: 分析结果
  - `tag_analysis_details`: 标签分析详情
  - `company_analysis_details`: 企业识别详情

## 统一管理

### 统一数据库管理器
- **文件**: `database_manager.py`
- **类**: `UnifiedDatabaseManager`
- **功能**: 
  - 统一管理两个数据库
  - 提供配置管理
  - 避免数据库冲突
  - 支持数据库备份和清理

### 配置管理
- **配置文件**: `config/database_config.json`
- **API接口**: `database_config_api.py`
- **功能**: 
  - 查询数据库状态
  - 获取数据库配置
  - 监控数据库健康状态

## 数据流向

```
原始数据 → 舆情数据库 → 分析处理 → 分析结果数据库
   ↓              ↓              ↓              ↓
CSV导入    数据查询和筛选    Agent分析    结果存储和查询
```

## 避免冲突的措施

### 1. 文件路径分离
- 舆情数据库: `data/sentiment_analysis.db`
- 结果数据库: `data/analysis_results.db`
- 完全不同的文件，无路径冲突

### 2. 管理类分离
- `DatabaseManager`: 专门管理舆情数据
- `ResultDatabaseManager`: 专门管理分析结果
- 职责明确，无功能重叠

### 3. 统一接口
- `UnifiedDatabaseManager`: 提供统一的管理接口
- 避免直接操作底层数据库管理器
- 确保配置的一致性

### 4. 配置隔离
- 每个数据库有独立的配置
- 支持不同的数据库类型
- 配置变更不影响其他数据库

## 使用方式

### 获取数据库管理器
```python
from database_manager import UnifiedDatabaseManager

# 获取统一管理器
db_manager = UnifiedDatabaseManager()

# 获取舆情数据库
sentiment_db = db_manager.get_sentiment_database()

# 获取结果数据库
result_db = db_manager.get_result_database()
```

### 查询数据库状态
```python
# 获取所有数据库状态
status = db_manager.get_database_status()

# 获取数据库配置
configs = db_manager.get_database_configs()
```

### 数据操作
```python
# 舆情数据库操作
sentiment_data = sentiment_db.get_records(limit=100)

# 结果数据库操作
analysis_results = result_db.get_analysis_results(task_id=1)
```

## 扩展性

### 支持多种数据库类型
- SQLite (默认)
- MySQL
- PostgreSQL
- MongoDB

### 配置灵活性
- 支持自定义数据库路径
- 支持远程数据库连接
- 支持数据库集群

## 注意事项

1. **不要直接修改数据库文件**: 使用提供的API接口
2. **备份重要数据**: 定期备份两个数据库
3. **监控数据库大小**: 避免数据库文件过大
4. **权限管理**: 确保数据库文件有正确的读写权限

## 故障排除

### 常见问题
1. **数据库文件不存在**: 检查 `data/` 目录权限
2. **连接失败**: 验证数据库配置
3. **数据不一致**: 使用统一管理器接口

### 调试方法
1. 查看日志文件
2. 使用API接口检查状态
3. 验证配置文件格式
