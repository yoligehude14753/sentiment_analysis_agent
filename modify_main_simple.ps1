# 读取文件内容
 = Get-Content main.py

# 创建新内容数组
 = @()

# 复制前32行
for ( = 0;  -lt 32; ++) {
     += []
}

# 添加新的导入
 += ""
 += "from unified_data_source_manager import UnifiedDataSourceManager, QueryParams"
 += "from data_source_config_api import router as data_source_config_router, get_data_source_manager"

# 复制剩余行
for ( = 32;  -lt .Length; ++) {
     += []
}

# 写回文件
 | Out-File main.py -Encoding UTF8
