# 舆情分析系统 - 数据库管理

## 概述

本系统将CSV格式的舆情数据存储到SQLite数据库中，提供完整的数据库管理接口和Web界面，支持数据查询、统计分析和字段配置管理。

## 功能特性

### 1. 数据存储
- 自动创建SQLite数据库和表结构
- 支持CSV数据批量导入
- 智能字段映射和数据类型处理
- 错误处理和日志记录

### 2. 数据查询
- 支持关键词搜索
- 多字段过滤
- 分页显示
- 排序功能
- 字段选择

### 3. 字段配置
- 字段显示/隐藏控制
- 搜索和过滤权限设置
- 显示顺序调整
- 字段类型配置

### 4. 数据统计
- 总记录数统计
- 情感等级分布
- 行业分布统计
- 公司分布统计

## 系统架构

```
舆情数据CSV → 数据导入脚本 → SQLite数据库 → 数据库API → Web界面
```

### 核心组件

1. **DatabaseManager** (`database.py`)
   - 数据库连接和初始化
   - 数据导入和查询
   - 字段配置管理
   - 统计信息生成

2. **数据库API** (`database_api.py`)
   - RESTful API接口
   - 数据查询端点
   - 字段配置管理
   - 统计信息接口

3. **Web管理界面** (`templates/database.html`)
   - 数据导入界面
   - 字段配置管理
   - 数据查询和显示
   - 统计信息展示

## 安装和配置

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 准备数据文件

确保CSV文件路径正确：
```
C:\Users\anyut\Desktop\建投需求\舆情解析\舆情数据.csv
```

### 3. 数据库字段映射

系统会自动识别以下字段：
- `标题` / `title` → 新闻标题
- `内容` / `content` → 新闻内容
- `来源` / `source` → 新闻来源
- `发布时间` / `publish_time` → 发布时间
- `公司名称` / `company_name` → 相关公司
- `行业` / `industry` → 所属行业
- `情感等级` / `sentiment_level` → 情感分析结果
- `风险标签` / `risk_tags` → 风险标签
- `分析原因` / `analysis_reason` → 分析原因

## 使用方法

### 1. 快速启动

运行启动脚本：
```bash
python start_database.py
```

脚本会：
- 检查依赖和环境
- 询问是否导入CSV数据
- 询问是否启动Web服务

### 2. 手动数据导入

```bash
python import_csv_data.py
```

### 3. 启动Web服务

```bash
python main.py
```

### 4. 访问管理界面

- 主页：http://localhost:8000
- 数据库管理：http://localhost:8000/database
- 配置页面：http://localhost:8000/config

## API接口

### 数据查询
```
GET /api/database/data
参数：
- fields: 查询字段（逗号分隔）
- filters: 过滤条件（JSON格式）
- search: 搜索关键词
- page: 页码
- page_size: 每页大小
- sort_by: 排序字段
- sort_order: 排序方向
```

### 字段配置
```
GET /api/database/fields - 获取字段配置
PUT /api/database/fields/{field_name} - 更新字段配置
```

### 统计信息
```
GET /api/database/statistics - 获取数据统计
```

### 数据导入
```
POST /api/database/import - 导入CSV数据
```

## 数据库结构

### sentiment_data 表
```sql
CREATE TABLE sentiment_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT,                    -- 标题
    content TEXT,                  -- 内容
    source TEXT,                   -- 来源
    publish_time TEXT,             -- 发布时间
    company_name TEXT,             -- 公司名称
    industry TEXT,                 -- 行业
    sentiment_level TEXT,          -- 情感等级
    risk_tags TEXT,                -- 风险标签
    analysis_reason TEXT,          -- 分析原因
    created_at TIMESTAMP,          -- 创建时间
    updated_at TIMESTAMP           -- 更新时间
);
```

### field_config 表
```sql
CREATE TABLE field_config (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    field_name TEXT UNIQUE,        -- 字段名
    display_name TEXT,             -- 显示名称
    is_visible BOOLEAN,            -- 是否可见
    is_searchable BOOLEAN,         -- 是否可搜索
    is_filterable BOOLEAN,         -- 是否可过滤
    display_order INTEGER,         -- 显示顺序
    field_type TEXT,               -- 字段类型
    created_at TIMESTAMP           -- 创建时间
);
```

## 配置选项

### 字段配置属性
- **is_visible**: 控制字段是否在表格中显示
- **is_searchable**: 控制字段是否参与关键词搜索
- **is_filterable**: 控制字段是否支持过滤
- **display_order**: 控制字段在表格中的显示顺序
- **field_type**: 字段类型（text, datetime, number等）

### 查询参数
- **page_size**: 每页显示记录数（1-1000）
- **sort_by**: 排序字段
- **sort_order**: 排序方向（ASC/DESC）

## 性能优化

### 1. 批量导入
- 支持大文件分块处理
- 可配置批处理大小（默认1000条）
- 事务提交优化

### 2. 查询优化
- 分页查询减少内存占用
- 字段选择减少数据传输
- 索引优化（建议在常用查询字段上创建索引）

### 3. 缓存策略
- 统计信息缓存
- 字段配置缓存
- 查询结果缓存

## 故障排除

### 常见问题

1. **CSV文件路径错误**
   - 检查文件路径是否正确
   - 确保文件编码为UTF-8

2. **数据库权限问题**
   - 确保data目录有写权限
   - 检查SQLite数据库文件权限

3. **内存不足**
   - 减少批处理大小
   - 使用分页查询
   - 增加系统内存

4. **API接口错误**
   - 检查服务是否正常启动
   - 查看错误日志
   - 验证API参数格式

### 日志查看

系统会记录详细的日志信息，包括：
- 数据导入过程
- 查询执行情况
- 错误和异常信息
- 性能统计

## 扩展功能

### 1. 数据导出
- 支持多种格式导出（CSV, Excel, JSON）
- 自定义导出字段
- 批量导出功能

### 2. 数据分析
- 趋势分析
- 相关性分析
- 可视化图表

### 3. 数据同步
- 定时数据更新
- 增量数据同步
- 多数据源支持

## 技术支持

如遇到问题，请：
1. 查看系统日志
2. 检查配置文件
3. 验证数据格式
4. 联系技术支持

## 更新日志

### v1.0.0
- 初始版本发布
- 支持CSV数据导入
- 基础数据库管理功能
- Web管理界面
- RESTful API接口
