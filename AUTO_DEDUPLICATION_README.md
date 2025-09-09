# 自动去重系统说明文档

## 概述

本系统已集成智能自动去重功能，在数据导出前自动检测并移除重复数据，确保导出的数据质量。

## 🚀 主要特性

### 1. 智能重复检测
- **双重检测机制**：同时基于 `original_id` 和内容相似度检测重复
- **可调节相似度阈值**：默认 85%，可根据需要调整（0.1-1.0）
- **高效算法**：使用 MD5 哈希预筛选 + 序列匹配精确计算

### 2. 自动集成导出
- **默认启用**：所有导出操作默认自动去重
- **透明处理**：用户无需额外操作，系统自动处理
- **详细日志**：完整记录去重过程和统计信息

### 3. 灵活配置选项
- **可选启用/禁用**：支持关闭自动去重功能
- **相似度阈值调节**：根据业务需求调整检测精度
- **保留策略**：智能保留最优质的数据记录

## 📋 功能详情

### 重复检测逻辑

1. **原始ID重复检测**
   - 检测相同 `original_id` 的记录
   - 相似度认定为 100%
   - 保留第一条记录，移除后续重复

2. **内容相似度检测**
   - 清理HTML标签和多余空白
   - 计算文本序列相似度
   - 超过阈值的记录标记为重复

3. **智能去重策略**
   - 优先保留数据完整性更好的记录
   - 保留最早的原始记录
   - 移除后续的重复项

### 导出API集成

#### GET 导出 API
```http
GET /api/results/export/json?auto_deduplicate=true&similarity_threshold=0.85
```

#### POST 导出 API
```json
{
  "format": "json",
  "auto_deduplicate": true,
  "similarity_threshold": 0.85,
  "options": {
    "original": true,
    "sentiment": true,
    "tags": true,
    "companies": true
  }
}
```

### 数据库去重 API
```http
POST /api/results/database/auto-deduplicate?similarity_threshold=0.85
```

## 🔧 配置参数

### ExportRequest 模型
```python
class ExportRequest(BaseModel):
    format: str = "csv"                    # 导出格式
    options: Dict[str, bool] = {}          # 导出选项
    auto_deduplicate: bool = True          # 自动去重（默认启用）
    similarity_threshold: float = 0.85     # 相似度阈值
```

### 相似度阈值说明
- **0.9-1.0**：严格模式，只检测几乎完全相同的内容
- **0.8-0.9**：标准模式，检测高度相似的内容（推荐）
- **0.6-0.8**：宽松模式，检测中等相似的内容
- **0.1-0.6**：极宽松模式，可能产生误判

## 📊 使用示例

### 1. 基本导出（自动去重）
```python
import requests

response = requests.get("http://localhost:8000/api/results/export/json")
# 自动启用去重，使用默认阈值 0.85
```

### 2. 自定义相似度阈值
```python
response = requests.get(
    "http://localhost:8000/api/results/export/json",
    params={
        'auto_deduplicate': True,
        'similarity_threshold': 0.90  # 更严格的检测
    }
)
```

### 3. 禁用自动去重
```python
response = requests.get(
    "http://localhost:8000/api/results/export/json",
    params={'auto_deduplicate': False}
)
```

### 4. POST API 使用
```python
export_request = {
    "format": "json",
    "auto_deduplicate": True,
    "similarity_threshold": 0.85,
    "options": {
        "original": True,
        "sentiment": True,
        "tags": True,
        "companies": True
    }
}

response = requests.post(
    "http://localhost:8000/api/results/export",
    json=export_request
)
```

## 🔍 去重效果监控

### 日志信息
系统会记录详细的去重过程：
```
[INFO] 导出前数据量: 100 条
[INFO] 🔄 开始自动去重处理，相似度阈值: 0.85
[INFO] ✅ 去重完成: 100 → 85 条 (移除 15 条重复)
[INFO] 去重率: 15.00%, 处理时间: 0.23s
[INFO] JSON导出成功，共导出 85 条记录
```

### 导出文件命名
启用去重的导出文件会包含标识：
```
sentiment_analysis_results_deduplicated_20250826_143022.json
```

### 统计信息
去重结果包含详细统计：
```json
{
  "original_count": 100,
  "final_count": 85,
  "removed_count": 15,
  "deduplication_rate": 0.15,
  "processing_time_seconds": 0.23,
  "duplicate_groups": 8
}
```

## 🧪 测试验证

### 运行完整性测试
```bash
python test_auto_deduplication.py
```

测试覆盖：
1. ✅ 模块导入测试
2. ✅ 去重逻辑测试
3. ✅ 相似度计算测试
4. ✅ GET导出API测试
5. ✅ POST导出API测试
6. ✅ 数据库去重API测试

### 测试报告
测试完成后会生成详细报告：
```
test_reports/auto_dedup_test_report_20250826_143022.json
```

## 🔧 故障排除

### 常见问题

1. **去重效果不明显**
   - 检查相似度阈值设置
   - 确认数据中确实存在重复
   - 查看日志中的详细统计信息

2. **去重过于严格**
   - 降低相似度阈值（如从0.85改为0.75）
   - 检查内容清理逻辑是否合适

3. **性能问题**
   - 大数据量时去重可能较慢
   - 考虑分批处理或异步处理
   - 监控处理时间日志

4. **API错误**
   - 检查服务器是否正常运行
   - 确认auto_deduplicator模块正确安装
   - 查看详细错误日志

### 日志级别
- `INFO`：正常处理信息
- `WARNING`：去重失败但使用原始数据
- `ERROR`：严重错误，可能影响功能

## 📈 性能优化

### 处理大数据量
- 系统已优化处理大量数据
- 使用哈希预筛选提高效率
- 内存使用经过优化

### 建议配置
- **小数据集（<1000条）**：阈值0.85，全量处理
- **中数据集（1000-10000条）**：阈值0.80，监控处理时间
- **大数据集（>10000条）**：考虑分批处理或数据库级去重

## 🔄 版本更新

### v1.0 特性
- ✅ 基础自动去重功能
- ✅ 导出API集成
- ✅ 相似度阈值配置
- ✅ 详细统计和日志
- ✅ 前端界面支持
- ✅ 完整性测试套件

### 未来计划
- 🔲 异步去重处理
- 🔲 更多相似度算法选择
- 🔲 批量去重优化
- 🔲 去重规则自定义

---

## 📞 技术支持

如遇到问题或需要技术支持，请：
1. 查看日志文件中的详细错误信息
2. 运行测试脚本验证系统状态
3. 检查配置参数是否正确设置

**注意**：自动去重功能默认启用，确保数据质量。如有特殊需求需要保留重复数据，请设置 `auto_deduplicate=false`。

