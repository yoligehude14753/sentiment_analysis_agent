# 在第32行后添加新的导入
 = Get-Content main.py
 = @()
for ( = 0;  -lt .Length; ++) {
     += []
    if ( -eq 31) {  # 第32行（索引31）
         += ""
         += "from unified_data_source_manager import UnifiedDataSourceManager, QueryParams"
         += "from data_source_config_api import router as data_source_config_router, get_data_source_manager"
    }
}
 | Out-File main.py -Encoding UTF8
