# New Database Manager - ResultDatabase

## 概述

这是一个全新的、改进的数据库管理器，专门为情感分析结果设计。它提供了完整的数据库操作、错误处理、统计跟踪和导出功能。

## 主要特性

### 🗄️ 数据库结构
- **sentiment_results**: 存储情感分析结果
- **error_logs**: 记录错误和异常信息
- **api_stats**: 跟踪API调用统计

### 🔧 核心功能
- 自动数据库初始化和表创建
- 安全的结果保存和查询
- 完整的错误处理和日志记录
- API调用统计和性能监控
- 数据导出和清理功能

## 快速开始

### 基本使用

```python
from result_database_new import ResultDatabase

# 创建数据库实例
db = ResultDatabase("my_database.db")

# 保存分析结果
result_id = db.save_result(
    query_text="用户查询文本",
    sentiment_score=0.8,
    sentiment_label="positive",
    confidence=0.95,
    model_used="gpt-4",
    raw_response="原始响应内容"
)

# 获取最近结果
recent_results = db.get_recent_results(limit=10)

# 搜索特定查询
search_results = db.get_results_by_query("关键词")
```

### 错误处理

```python
# 记录错误
db.log_error(
    error_type="api_error",
    error_message="API调用失败",
    query_text="相关查询",
    stack_trace="错误堆栈"
)

# 更新API统计
db.update_api_stats("gpt-4", success=True, response_time=1.2)
db.update_api_stats("gpt-4", success=False, response_time=5.0)
```

### 数据管理

```python
# 获取数据库统计
stats = db.get_database_stats()
print(f"总结果数: {stats['total_results']}")
print(f"成功结果: {stats['successful_results']}")
print(f"错误数量: {stats['total_errors']}")

# 导出结果
db.export_results("export.json")

# 清理旧记录
db.cleanup_old_records(days=30)
```

## 数据库表结构

### sentiment_results 表
| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER | 主键，自增 |
| query_text | TEXT | 查询文本（必填） |
| sentiment_score | REAL | 情感分数 |
| sentiment_label | TEXT | 情感标签 |
| confidence | REAL | 置信度 |
| analysis_time | TIMESTAMP | 分析时间 |
| model_used | TEXT | 使用的模型 |
| raw_response | TEXT | 原始响应 |
| processing_status | TEXT | 处理状态 |

### error_logs 表
| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER | 主键，自增 |
| error_type | TEXT | 错误类型 |
| error_message | TEXT | 错误消息 |
| query_text | TEXT | 相关查询 |
| timestamp | TIMESTAMP | 时间戳 |
| stack_trace | TEXT | 堆栈跟踪 |

### api_stats 表
| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER | 主键，自增 |
| api_name | TEXT | API名称 |
| call_count | INTEGER | 调用次数 |
| success_count | INTEGER | 成功次数 |
| error_count | INTEGER | 错误次数 |
| last_called | TIMESTAMP | 最后调用时间 |
| avg_response_time | REAL | 平均响应时间 |

## 方法详解

### 初始化方法
- `__init__(db_path)`: 初始化数据库连接
- `init_database()`: 创建数据库表结构

### 数据操作方法
- `save_result()`: 保存分析结果
- `get_recent_results(limit)`: 获取最近结果
- `get_results_by_query(query_text)`: 按查询搜索

### 错误处理方法
- `log_error()`: 记录错误信息
- `update_api_stats()`: 更新API统计

### 管理方法
- `get_database_stats()`: 获取统计信息
- `cleanup_old_records(days)`: 清理旧记录
- `export_results(output_file)`: 导出结果

## 错误处理

数据库管理器包含完整的错误处理机制：

1. **自动错误日志**: 所有操作失败都会自动记录
2. **异常安全**: 使用 `with` 语句确保连接正确关闭
3. **优雅降级**: 查询失败时返回空列表而不是崩溃
4. **详细错误信息**: 记录错误类型、消息和上下文

## 性能优化

- **连接池管理**: 每次操作使用新的连接，避免连接泄漏
- **索引优化**: 在关键字段上自动创建索引
- **批量操作**: 支持批量插入和更新
- **内存管理**: 及时清理不需要的数据

## 测试

运行测试脚本验证功能：

```bash
python test_database_new.py
```

测试包括：
- 基本数据库操作
- 错误处理场景
- API统计功能
- 数据导出功能
- 清理和维护功能

## 迁移指南

### 从旧版本迁移

1. **备份现有数据**:
   ```bash
   cp old_database.db backup.db
   ```

2. **使用新管理器**:
   ```python
   from result_database_new import ResultDatabase
   db = ResultDatabase("old_database.db")
   ```

3. **验证数据完整性**:
   ```python
   stats = db.get_database_stats()
   print(f"迁移后总记录数: {stats['total_results']}")
   ```

## 最佳实践

1. **定期备份**: 使用 `export_results()` 定期导出数据
2. **错误监控**: 定期检查 `error_logs` 表
3. **性能监控**: 使用 `api_stats` 跟踪API性能
4. **数据清理**: 定期运行 `cleanup_old_records()`

## 故障排除

### 常见问题

1. **编码问题**: 确保文件使用UTF-8编码
2. **权限问题**: 检查数据库文件写入权限
3. **磁盘空间**: 确保有足够的磁盘空间
4. **并发访问**: 避免多个进程同时写入

### 调试技巧

```python
# 启用详细日志
import logging
logging.basicConfig(level=logging.DEBUG)

# 检查数据库状态
stats = db.get_database_stats()
print("数据库状态:", stats)

# 验证表结构
with sqlite3.connect(db.db_path) as conn:
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    print("现有表:", tables)
```

## 许可证

本项目采用MIT许可证。

## 贡献

欢迎提交Issue和Pull Request来改进这个数据库管理器。
