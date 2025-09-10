"""
统一数据源管理器
支持API数据源和文件上传数据源，提供统一的数据访问接口
"""

import json
import logging
import tempfile
import os
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
import pandas as pd
from dataclasses import dataclass

from api_data_source_manager import APIDataSourceManager, APIConfig, QueryParams

logger = logging.getLogger(__name__)

@dataclass
class FileUploadConfig:
    """文件上传配置"""
    file_path: str
    file_type: str  # csv, json
    field_mapping: Dict[str, str] = None
    encoding: str = "utf-8"

class UnifiedDataSourceManager:
    """统一数据源管理器"""
    
    def __init__(self):
        self.current_source_type = "api"  # api, file
        self.api_manager = APIDataSourceManager()
        self.file_config: Optional[FileUploadConfig] = None
        self.uploaded_data: List[Dict[str, Any]] = []
        
    async def configure_api_source(self, config_data: Dict[str, Any]) -> Dict[str, Any]:
        """配置API数据源"""
        try:
            # 创建API配置
            api_config = APIConfig(
                url=config_data['url'],
                headers=config_data.get('headers', {}),
                auth_type=config_data.get('auth_type', 'none'),
                auth_config=config_data.get('auth_config', {}),
                query_params=config_data.get('query_params', {}),
                field_mapping=config_data.get('field_mapping', {}),
                pagination_config=config_data.get('pagination_config', {}),
                timeout=config_data.get('timeout', 30)
            )
            
            # 配置API管理器
            self.api_manager.configure_api(api_config)
            
            # 测试连接
            async with self.api_manager:
                test_result = await self.api_manager.test_connection()
            
            if test_result['success']:
                self.current_source_type = "api"
                return {
                    'success': True,
                    'message': 'API数据源配置成功',
                    'sample_data': test_result.get('sample_data', [])
                }
            else:
                return test_result
                
        except Exception as e:
            logger.error(f"配置API数据源失败: {str(e)}")
            return {
                'success': False,
                'error': f'配置失败: {str(e)}',
                'message': f'配置API数据源时发生错误: {str(e)}'
            }
    
    def configure_file_source(self, file_path: str, file_type: str, 
                            field_mapping: Dict[str, str] = None, 
                            encoding: str = "utf-8") -> Dict[str, Any]:
        """配置文件数据源"""
        try:
            # 检查文件大小（10MB限制）
            file_size = os.path.getsize(file_path)
            if file_size > 10 * 1024 * 1024:  # 10MB
                return {
                    'success': False,
                    'error': '文件过大',
                    'message': '文件大小不能超过10MB'
                }
            
            # 读取文件数据
            if file_type.lower() == 'csv':
                df = pd.read_csv(file_path, encoding=encoding)
                data = df.to_dict('records')
            elif file_type.lower() == 'json':
                with open(file_path, 'r', encoding=encoding) as f:
                    data = json.load(f)
                if isinstance(data, dict):
                    # 如果是字典，尝试获取数据数组
                    data = data.get('data', data.get('items', data.get('results', [data])))
            else:
                return {
                    'success': False,
                    'error': '不支持的文件格式',
                    'message': f'不支持的文件格式: {file_type}'
                }
            
            # 应用字段映射
            if field_mapping:
                mapped_data = []
                for item in data:
                    mapped_item = {}
                    for system_field, file_field in field_mapping.items():
                        if file_field in item:
                            mapped_item[system_field] = item[file_field]
                    mapped_data.append(mapped_item)
                data = mapped_data
            
            # 保存配置和数据
            self.file_config = FileUploadConfig(
                file_path=file_path,
                file_type=file_type,
                field_mapping=field_mapping,
                encoding=encoding
            )
            self.uploaded_data = data
            self.current_source_type = "file"
            
            return {
                'success': True,
                'message': f'文件数据源配置成功，共加载 {len(data)} 条数据',
                'total_records': len(data)
            }
            
        except Exception as e:
            logger.error(f"配置文件数据源失败: {str(e)}")
            return {
                'success': False,
                'error': f'配置失败: {str(e)}',
                'message': f'配置文件数据源时发生错误: {str(e)}'
            }
    
    async def get_data(self, query_params: QueryParams) -> Dict[str, Any]:
        """获取数据（统一接口）"""
        if self.current_source_type == "api":
            return await self.get_api_data(query_params)
        elif self.current_source_type == "file":
            return self.get_file_data(query_params)
        else:
            return {
                'success': False,
                'error': '未配置数据源',
                'message': '请先配置API数据源或上传数据文件'
            }
    
    async def get_api_data(self, query_params: QueryParams) -> Dict[str, Any]:
        """从API获取数据"""
        async with self.api_manager:
            return await self.api_manager.get_data(query_params)
    
    def get_file_data(self, query_params: QueryParams) -> Dict[str, Any]:
        """从文件获取数据"""
        try:
            if not self.uploaded_data:
                return {
                    'success': False,
                    'error': '无数据',
                    'message': '没有上传的数据文件'
                }
            
            # 应用时间过滤
            filtered_data = self.uploaded_data.copy()
            
            if query_params.start_time and query_params.end_time:
                time_field = query_params.time_field
                filtered_data = [
                    item for item in filtered_data
                    if item.get(time_field) and 
                    query_params.start_time <= item[time_field] <= query_params.end_time
                ]
            
            # 应用分页
            total = len(filtered_data)
            start_idx = (query_params.page - 1) * query_params.page_size
            end_idx = start_idx + query_params.page_size
            paginated_data = filtered_data[start_idx:end_idx]
            
            return {
                'success': True,
                'data': paginated_data,
                'total': total,
                'page': query_params.page,
                'page_size': query_params.page_size,
                'total_pages': (total + query_params.page_size - 1) // query_params.page_size
            }
            
        except Exception as e:
            logger.error(f"获取文件数据失败: {str(e)}")
            return {
                'success': False,
                'error': f'获取数据失败: {str(e)}',
                'message': f'从文件获取数据时发生错误: {str(e)}'
            }
    
    async def get_data_count(self, filters: Dict[str, Any] = None) -> Dict[str, Any]:
        """获取数据总量"""
        if self.current_source_type == "api":
            # 对于API，使用最小查询获取总数
            query_params = QueryParams(page=1, page_size=1)
            if filters and 'publish_time' in filters:
                time_range = filters['publish_time']
                query_params.start_time = time_range.get('start')
                query_params.end_time = time_range.get('end')
            
            result = await self.get_api_data(query_params)
            if result['success']:
                return {
                    'success': True,
                    'total': result['total']
                }
            else:
                return result
                
        elif self.current_source_type == "file":
            # 对于文件，直接返回数据长度
            return {
                'success': True,
                'total': len(self.uploaded_data)
            }
        else:
            return {
                'success': False,
                'error': '未配置数据源',
                'total': 0
            }
    
    def get_current_source_info(self) -> Dict[str, Any]:
        """获取当前数据源信息"""
        if self.current_source_type == "api":
            config = self.api_manager.get_config()
            return {
                'source_type': 'api',
                'config': config,
                'status': 'configured' if config else 'not_configured'
            }
        elif self.current_source_type == "file":
            return {
                'source_type': 'file',
                'config': {
                    'file_path': self.file_config.file_path if self.file_config else None,
                    'file_type': self.file_config.file_type if self.file_config else None,
                    'field_mapping': self.file_config.field_mapping if self.file_config else None,
                    'total_records': len(self.uploaded_data)
                },
                'status': 'configured' if self.uploaded_data else 'not_configured'
            }
        else:
            return {
                'source_type': 'none',
                'config': None,
                'status': 'not_configured'
            }
    
    def switch_source_type(self, source_type: str) -> Dict[str, Any]:
        """切换数据源类型"""
        if source_type in ['api', 'file']:
            self.current_source_type = source_type
            return {
                'success': True,
                'message': f'已切换到 {source_type} 数据源',
                'current_source': source_type
            }
        else:
            return {
                'success': False,
                'error': '无效的数据源类型',
                'message': '数据源类型必须是 api 或 file'
            }
    
    def clear_file_data(self):
        """清除文件数据"""
        self.uploaded_data = []
        self.file_config = None
        if self.current_source_type == "file":
            self.current_source_type = "api"  # 回退到API模式
