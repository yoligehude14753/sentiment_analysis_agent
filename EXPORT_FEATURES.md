# 增强导出功能说明

## 概述

本系统在现有的导出功能基础上，增加了自动化和增强导出功能，支持多种格式和选项。

## 功能特性

### 1. 自动导出
- **触发时机**: 在批量解析完成后自动执行
- **执行流程**: 数据解析 → 去重 → 自动导出
- **文件命名**: `auto_export_after_dedup_YYYYMMDD_HHMMSS.json`

### 2. 增强导出
- **支持格式**: JSON、CSV、Excel
- **元数据**: 可选择是否包含导出信息
- **标签过滤**: 支持按风险标签过滤数据
- **文件命名**: `enhanced_export_YYYYMMDD_HHMMSS.[json|csv|xlsx]`

## API接口

### 增强导出接口
```
POST /api/export/enhanced
```

**参数**:
- `export_format`: 导出格式 (json/csv/excel)
- `include_metadata`: 是否包含元数据 (true/false)
- `filter_tags`: 过滤标签，逗号分隔 (可选)

**示例**:
```bash
# JSON格式导出，包含元数据
curl -X POST "http://localhost:8000/api/export/enhanced" \
  -d "export_format=json" \
  -d "include_metadata=true"

# CSV格式导出，不包含元数据
curl -X POST "http://localhost:8000/api/export/enhanced" \
  -d "export_format=csv" \
  -d "include_metadata=false"

# 带标签过滤的JSON导出
curl -X POST "http://localhost:8000/api/export/enhanced" \
  -d "export_format=json" \
  -d "include_metadata=true" \
  -d "filter_tags=同业竞争,关联交易"
```

## 导出格式说明

### JSON格式
- 标准JSON格式，支持中文
- 可选择包含导出元数据
- 文件大小相对较小

### CSV格式
- 标准CSV格式，支持Excel打开
- 不包含元数据
- 适合数据分析工具处理

### Excel格式
- 多工作表Excel文件
- 主工作表包含所有数据
- 元数据工作表包含导出信息

## 自动化流程

### 批量解析后的自动流程
1. **数据解析**: 从舆情数据库获取数据
2. **AI分析**: 情感分析、标签分析、企业识别
3. **数据保存**: 保存到结果数据库
4. **自动去重**: 按original_id去重
5. **自动导出**: 生成导出文件

### 流程特点
- **全自动化**: 无需人工干预
- **实时反馈**: 通过SSE流式返回进度
- **错误处理**: 完善的异常处理机制
- **日志记录**: 详细的操作日志

## 文件结构

```
exports/
├── auto_export_after_dedup_20250101_120000.json
├── enhanced_export_20250101_120000.json
├── enhanced_export_20250101_120000.csv
└── enhanced_export_20250101_120000.xlsx
```

## 使用场景

### 1. 日常运营
- 定期数据备份
- 数据质量检查
- 业务报告生成

### 2. 数据分析
- 风险标签统计
- 情感趋势分析
- 企业关联分析

### 3. 合规审计
- 数据完整性验证
- 处理流程追溯
- 质量报告生成

## 注意事项

### 1. 依赖要求
- CSV导出: 内置csv模块
- Excel导出: 需要pandas和openpyxl
- 数据库: 需要SQLite支持

### 2. 性能考虑
- 大数据量导出可能需要较长时间
- 建议在非高峰期执行
- 可考虑分批导出

### 3. 存储管理
- 导出文件会占用磁盘空间
- 建议定期清理旧文件
- 可配置自动清理策略

## 故障排除

### 常见问题
1. **导出失败**: 检查数据库连接和权限
2. **格式错误**: 确认数据完整性
3. **内存不足**: 减少导出数据量或分批处理

### 日志查看
- 系统日志记录详细错误信息
- 可通过API接口查看导出状态
- 建议启用详细日志记录

## 扩展功能

### 未来计划
- 支持更多导出格式 (PDF、XML等)
- 增加数据压缩功能
- 支持云端存储导出
- 增加导出模板功能

### 自定义开发
- 可扩展新的导出格式
- 支持自定义数据转换
- 可集成第三方导出服务
