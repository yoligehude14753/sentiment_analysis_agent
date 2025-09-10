"""
API数据源管理器
支持通过API获取数据，提供字段映射和查询参数配置功能
"""

import requests
import json
import logging
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
import asyncio
import aiohttp
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class APIConfig:
    """API配置类"""
    url: str
    headers: Dict[str, str] = None
    auth_type: str = "none"  # none, api_key, oauth, bearer
    auth_config: Dict[str, str] = None
    query_params: Dict[str, Any] = None
    field_mapping: Dict[str, str] = None
    pagination_config: Dict[str, Any] = None
    timeout: int = 30

@dataclass
class QueryParams:
    """查询参数配置"""
    time_field: str = "publish_time"
    start_time: str = None
    end_time: str = None
    page: int = 1
    page_size: int = 100
    custom_params: Dict[str, Any] = None

class APIDataSourceManager:
    """API数据源管理器"""
    
    def __init__(self):
        self.api_config: Optional[APIConfig] = None
        self.session: Optional[aiohttp.ClientSession] = None
        
    async def __aenter__(self):
        """异步上下文管理器入口"""
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        if self.session:
            await self.session.close()
    
    def configure_api(self, config: APIConfig):
        """配置API连接"""
        self.api_config = config
        logger.info(f"API配置已更新: {config.url}")
    
    def get_nested_value(self, data: Dict[str, Any], key_path: str) -> Any:
        """获取嵌套字段值，支持点号分隔的路径"""
        try:
            keys = key_path.split('.')
            value = data
            for key in keys:
                if isinstance(value, dict) and key in value:
                    value = value[key]
                else:
                    return None
            return value
        except Exception as e:
            logger.warning(f"获取嵌套字段失败 {key_path}: {e}")
            return None
    
    def apply_field_mapping(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """应用字段映射"""
        if not self.api_config or not self.api_config.field_mapping:
            return data
        
        mapped_data = []
        for item in data:
            mapped_item = {}
            for system_field, api_field in self.api_config.field_mapping.items():
                value = self.get_nested_value(item, api_field)
                if value is not None:
                    mapped_item[system_field] = value
            mapped_data.append(mapped_item)
        
        return mapped_data
    
    def build_query_params(self, query_params: QueryParams) -> Dict[str, Any]:
        """构建查询参数"""
        params = {}
        
        # 基础查询参数
        if self.api_config and self.api_config.query_params:
            params.update(self.api_config.query_params)
        
        # 时间范围参数
        if query_params.start_time and query_params.end_time:
            time_field = query_params.time_field
            params[time_field] = {
                "start": query_params.start_time,
                "end": query_params.end_time
            }
        
        # 分页参数
        if self.api_config and self.api_config.pagination_config:
            page_config = self.api_config.pagination_config
            page_param = page_config.get('page_param', 'page')
            size_param = page_config.get('size_param', 'page_size')
            params[page_param] = query_params.page
            params[size_param] = query_params.page_size
        
        # 自定义参数
        if query_params.custom_params:
            params.update(query_params.custom_params)
        
        return params
    
    async def get_data(self, query_params: QueryParams) -> Dict[str, Any]:
        """从API获取数据"""
        if not self.api_config:
            return {
                'success': False,
                'error': 'API未配置',
                'message': '请先配置API连接'
            }
        
        try:
            # 构建请求参数
            params = self.build_query_params(query_params)
            
            # 构建请求头
            headers = {}
            if self.api_config.headers:
                headers.update(self.api_config.headers)
            
            # 添加认证信息
            if self.api_config.auth_type == "api_key" and self.api_config.auth_config:
                auth_config = self.api_config.auth_config
                if auth_config.get('header_name'):
                    headers[auth_config['header_name']] = auth_config.get('api_key', '')
            elif self.api_config.auth_type == "bearer" and self.api_config.auth_config:
                token = self.api_config.auth_config.get('token', '')
                headers['Authorization'] = f"Bearer {token}"
            
            # 发送请求
            timeout = aiohttp.ClientTimeout(total=self.api_config.timeout)
            async with self.session.get(
                self.api_config.url,
                params=params,
                headers=headers,
                timeout=timeout
            ) as response:
                
                if response.status != 200:
                    return {
                        'success': False,
                        'error': f'API请求失败: HTTP {response.status}',
                        'message': f'API返回状态码: {response.status}'
                    }
                
                # 解析响应
                try:
                    data = await response.json()
                except Exception as e:
                    return {
                        'success': False,
                        'error': f'响应解析失败: {str(e)}',
                        'message': 'API返回的数据不是有效的JSON格式'
                    }
                
                # 处理分页数据
                if isinstance(data, dict):
                    # 检查是否有分页信息
                    items = data.get('data', data.get('items', data.get('results', [])))
                    total = data.get('total', data.get('count', len(items)))
                else:
                    items = data if isinstance(data, list) else []
                    total = len(items)
                
                # 应用字段映射
                mapped_items = self.apply_field_mapping(items)
                
                return {
                    'success': True,
                    'data': mapped_items,
                    'total': total,
                    'page': query_params.page,
                    'page_size': query_params.page_size,
                    'total_pages': (total + query_params.page_size - 1) // query_params.page_size
                }
                
        except asyncio.TimeoutError:
            return {
                'success': False,
                'error': '请求超时',
                'message': f'API请求超时（{self.api_config.timeout}秒）'
            }
        except Exception as e:
            logger.error(f"API请求失败: {str(e)}")
            return {
                'success': False,
                'error': f'API请求失败: {str(e)}',
                'message': f'连接API时发生错误: {str(e)}'
            }
    
    async def test_connection(self) -> Dict[str, Any]:
        """测试API连接"""
        if not self.api_config:
            return {
                'success': False,
                'error': 'API未配置',
                'message': '请先配置API连接'
            }
        
        try:
            # 使用最小查询参数测试连接
            test_params = QueryParams(
                page=1,
                page_size=1
            )
            
            result = await self.get_data(test_params)
            
            if result['success']:
                return {
                    'success': True,
                    'message': 'API连接测试成功',
                    'sample_data': result['data'][:1] if result['data'] else []
                }
            else:
                return result
                
        except Exception as e:
            return {
                'success': False,
                'error': f'连接测试失败: {str(e)}',
                'message': f'测试API连接时发生错误: {str(e)}'
            }
    
    def get_config(self) -> Optional[Dict[str, Any]]:
        """获取当前API配置"""
        if not self.api_config:
            return None
        
        # 隐藏敏感信息
        config_dict = {
            'url': self.api_config.url,
            'headers': self.api_config.headers or {},
            'auth_type': self.api_config.auth_type,
            'query_params': self.api_config.query_params or {},
            'field_mapping': self.api_config.field_mapping or {},
            'pagination_config': self.api_config.pagination_config or {},
            'timeout': self.api_config.timeout
        }
        
        # 隐藏认证信息
        if self.api_config.auth_config:
            config_dict['auth_config'] = {
                k: '***' if 'key' in k.lower() or 'token' in k.lower() else v
                for k, v in self.api_config.auth_config.items()
            }
        
        return config_dict
