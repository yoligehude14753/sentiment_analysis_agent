"""
数据库API数据源管理器
支持通过数据库API接口获取数据
"""

import aiohttp
import asyncio
import json
import logging
from typing import Dict, Any, List, Optional
from pydantic import BaseModel
from datetime import datetime

logger = logging.getLogger(__name__)

class DatabaseAPIConfig(BaseModel):
    """数据库API配置模型"""
    api_url: str  # 数据库API的基础URL
    endpoint: str = "/api/database/data"  # 数据查询端点
    count_endpoint: str = "/api/database/count"  # 数据统计端点
    headers: Dict[str, str] = {}  # HTTP请求头
    auth_type: str = "none"  # 认证类型: none, basic, bearer, api_key
    auth_config: Dict[str, str] = {}  # 认证配置
    query_params: Dict[str, Any] = {}  # 默认查询参数
    field_mapping: Dict[str, str] = {}  # 字段映射
    pagination_config: Dict[str, Any] = {
        "page_param": "page",
        "page_size_param": "page_size",
        "default_page_size": 50,
        "max_page_size": 1000
    }
    timeout: int = 30

class DatabaseAPIDataSourceManager:
    """数据库API数据源管理器"""
    
    def __init__(self):
        self.config: Optional[DatabaseAPIConfig] = None
        self.session: Optional[aiohttp.ClientSession] = None
        
    def configure_database_api(self, config: DatabaseAPIConfig):
        """配置数据库API连接"""
        self.config = config
        logger.info(f"数据库API配置完成: {config.api_url}")
        
    async def __aenter__(self):
        """异步上下文管理器入口"""
        if not self.session:
            timeout = aiohttp.ClientTimeout(total=self.config.timeout if self.config else 30)
            self.session = aiohttp.ClientSession(timeout=timeout)
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        if self.session:
            await self.session.close()
            self.session = None
    
    def _build_headers(self) -> Dict[str, str]:
        """构建请求头"""
        headers = self.config.headers.copy() if self.config else {}
        
        # 添加认证头
        if self.config and self.config.auth_type == "bearer":
            token = self.config.auth_config.get("token", "")
            if token:
                headers["Authorization"] = f"Bearer {token}"
        elif self.config and self.config.auth_type == "api_key":
            api_key = self.config.auth_config.get("api_key", "")
            key_name = self.config.auth_config.get("key_name", "X-API-Key")
            if api_key:
                headers[key_name] = api_key
                
        return headers
    
    def _build_auth(self) -> Optional[aiohttp.BasicAuth]:
        """构建基本认证"""
        if self.config and self.config.auth_type == "basic":
            username = self.config.auth_config.get("username", "")
            password = self.config.auth_config.get("password", "")
            if username and password:
                return aiohttp.BasicAuth(username, password)
        return None
    
    async def test_connection(self) -> Dict[str, Any]:
        """测试数据库API连接"""
        if not self.config:
            return {
                "success": False,
                "error": "数据库API未配置",
                "message": "请先配置数据库API连接"
            }
        
        try:
            async with self:
                # 测试数据统计接口
                count_url = f"{self.config.api_url.rstrip('/')}{self.config.count_endpoint}"
                headers = self._build_headers()
                auth = self._build_auth()
                
                async with self.session.get(
                    count_url,
                    headers=headers,
                    auth=auth,
                    params={"time_field": "publish_time", "start_time": "2024-01-01", "end_time": "2024-12-31"}
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return {
                            "success": True,
                            "message": "数据库API连接成功",
                            "total_records": data.get("total", 0),
                            "sample_data": []
                        }
                    else:
                        error_text = await response.text()
                        return {
                            "success": False,
                            "error": f"HTTP {response.status}",
                            "message": f"数据库API连接失败: {error_text}"
                        }
                        
        except Exception as e:
            logger.error(f"测试数据库API连接失败: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "message": f"数据库API连接测试失败: {str(e)}"
            }
    
    async def get_data(self, query_params: Dict[str, Any] = None) -> Dict[str, Any]:
        """从数据库API获取数据"""
        if not self.config:
            return {
                "success": False,
                "error": "数据库API未配置",
                "data": [],
                "total": 0
            }
        
        try:
            async with self:
                # 构建查询参数
                params = self.config.query_params.copy()
                if query_params:
                    params.update(query_params)
                
                # 构建请求URL
                url = f"{self.config.api_url.rstrip('/')}{self.config.endpoint}"
                headers = self._build_headers()
                auth = self._build_auth()
                
                # 发送请求
                async with self.session.get(
                    url,
                    headers=headers,
                    auth=auth,
                    params=params
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        # 应用字段映射
                        if self.config.field_mapping and data.get("data"):
                            mapped_data = []
                            for item in data["data"]:
                                mapped_item = {}
                                for api_field, internal_field in self.config.field_mapping.items():
                                    if api_field in item:
                                        mapped_item[internal_field] = item[api_field]
                                mapped_data.append(mapped_item)
                            data["data"] = mapped_data
                        
                        return {
                            "success": True,
                            "data": data.get("data", []),
                            "total": data.get("total", 0),
                            "page": data.get("page", 1),
                            "page_size": data.get("page_size", 50)
                        }
                    else:
                        error_text = await response.text()
                        return {
                            "success": False,
                            "error": f"HTTP {response.status}",
                            "message": f"获取数据失败: {error_text}",
                            "data": [],
                            "total": 0
                        }
                        
        except Exception as e:
            logger.error(f"从数据库API获取数据失败: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "message": f"获取数据失败: {str(e)}",
                "data": [],
                "total": 0
            }
    
    async def get_available_fields(self) -> Dict[str, Any]:
        """获取数据库API可用的字段"""
        if not self.config:
            return {
                "success": False,
                "error": "数据库API未配置",
                "fields": []
            }
        
        try:
            async with self:
                # 获取少量数据来分析字段结构
                url = f"{self.config.api_url.rstrip('/')}{self.config.endpoint}"
                headers = self._build_headers()
                auth = self._build_auth()
                
                params = {
                    "page": 1,
                    "page_size": 1
                }
                
                async with self.session.get(
                    url,
                    headers=headers,
                    auth=auth,
                    params=params
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get("data") and len(data["data"]) > 0:
                            sample_item = data["data"][0]
                            fields = list(sample_item.keys())
                            return {
                                "success": True,
                                "fields": fields,
                                "sample_data": sample_item
                            }
                        else:
                            return {
                                "success": True,
                                "fields": [],
                                "message": "数据库中没有数据"
                            }
                    else:
                        error_text = await response.text()
                        return {
                            "success": False,
                            "error": f"HTTP {response.status}",
                            "message": f"获取字段信息失败: {error_text}",
                            "fields": []
                        }
                        
        except Exception as e:
            logger.error(f"获取数据库API字段信息失败: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "message": f"获取字段信息失败: {str(e)}",
                "fields": []
            }
