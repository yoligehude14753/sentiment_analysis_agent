#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
数据库API接口
提供舆情数据的查询、统计和字段配置管理功能
"""

from fastapi import APIRouter, HTTPException, Query, Depends
from typing import List, Dict, Optional, Any
from pydantic import BaseModel
from database_manager import UnifiedDatabaseManager
import logging

logger = logging.getLogger(__name__)

# 创建API路由器
router = APIRouter(prefix="/api/database", tags=["数据库"])

# 数据模型
class DataQueryRequest(BaseModel):
    fields: Optional[List[str]] = None
    filters: Optional[Dict[str, Any]] = None
    search: Optional[str] = None
    page: int = 1
    page_size: int = 50
    sort_by: str = 'publish_time'
    sort_order: str = 'DESC'

class DataCountRequest(BaseModel):
    time_field: str
    start_time: str
    end_time: str

class DataCountResponse(BaseModel):
    success: bool
    total: int
    message: Optional[str] = None
    error: Optional[str] = None

class FieldConfigUpdate(BaseModel):
    display_name: str
    is_visible: bool = True
    is_searchable: bool = True
    is_filterable: bool = True
    display_order: int = 0
    field_type: str = 'text'

class DataResponse(BaseModel):
    success: bool
    data: Optional[List[Dict[str, Any]]] = None
    total: Optional[int] = None
    page: Optional[int] = None
    page_size: Optional[int] = None
    total_pages: Optional[int] = None
    message: Optional[str] = None
    error: Optional[str] = None

class FieldConfigResponse(BaseModel):
    success: bool
    fields: Optional[List[Dict[str, Any]]] = None
    message: Optional[str] = None
    error: Optional[str] = None

class StatisticsResponse(BaseModel):
    success: bool
    statistics: Optional[Dict[str, Any]] = None
    message: Optional[str] = None
    error: Optional[str] = None

class TimeRangeResponse(BaseModel):
    success: bool
    earliest_time: Optional[str] = None
    latest_time: Optional[str] = None
    message: Optional[str] = None
    error: Optional[str] = None

# 依赖注入
def get_db_manager():
    """获取统一数据库管理器实例"""
    return UnifiedDatabaseManager()

# API端点
@router.get("/data", response_model=DataResponse)
async def get_data(
    fields: Optional[str] = Query(None, description="查询字段，用逗号分隔"),
    filters: Optional[str] = Query(None, description="过滤条件，JSON格式"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(50, ge=1, le=1000, description="每页大小"),
    sort_by: str = Query('publish_time', description="排序字段"),
    sort_order: str = Query('DESC', description="排序方向"),
    db_manager: UnifiedDatabaseManager = Depends(get_db_manager)
):
    """查询舆情数据"""
    try:
        # 获取舆情数据库
        sentiment_db = db_manager.get_sentiment_database()
        
        # 解析字段列表
        field_list = None
        if fields:
            field_list = [f.strip() for f in fields.split(',')]
        
        # 解析过滤条件
        filter_dict = None
        if filters:
            import json
            try:
                filter_dict = json.loads(filters)
            except json.JSONDecodeError:
                raise HTTPException(status_code=400, detail="过滤条件格式错误")
        
        # 查询数据
        result = sentiment_db.get_data(
            fields=field_list,
            filters=filter_dict,
            search=search,
            page=page,
            page_size=page_size,
            sort_by=sort_by,
            sort_order=sort_order
        )
        
        if result['success']:
            return DataResponse(**result)
        else:
            raise HTTPException(status_code=500, detail=result['message'])
            
    except Exception as e:
        logger.error(f"查询数据失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"查询数据失败: {str(e)}")

@router.get("/fields", response_model=FieldConfigResponse)
async def get_field_config(
    db_manager: UnifiedDatabaseManager = Depends(get_db_manager)
):
    """获取字段配置"""
    try:
        # 获取舆情数据库
        sentiment_db = db_manager.get_sentiment_database()
        result = sentiment_db.get_field_config()
        
        if result['success']:
            return FieldConfigResponse(**result)
        else:
            raise HTTPException(status_code=500, detail=result['message'])
            
    except Exception as e:
        logger.error(f"获取字段配置失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取字段配置失败: {str(e)}")

@router.put("/fields/{field_name}", response_model=FieldConfigResponse)
async def update_field_config(
    field_name: str,
    config: FieldConfigUpdate,
    db_manager: UnifiedDatabaseManager = Depends(get_db_manager)
):
    """更新字段配置"""
    try:
        # 获取舆情数据库
        sentiment_db = db_manager.get_sentiment_database()
        result = sentiment_db.update_field_config(field_name, config.dict())
        
        if result['success']:
            return FieldConfigResponse(**result)
        else:
            raise HTTPException(status_code=400, detail=result['message'])
            
    except Exception as e:
        logger.error(f"更新字段配置失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"更新字段配置失败: {str(e)}")

@router.get("/statistics", response_model=StatisticsResponse)
async def get_statistics(
    db_manager: UnifiedDatabaseManager = Depends(get_db_manager)
):
    """获取数据统计信息"""
    try:
        # 获取舆情数据库
        sentiment_db = db_manager.get_sentiment_database()
        result = sentiment_db.get_statistics()
        
        if result['success']:
            return StatisticsResponse(**result)
        else:
            raise HTTPException(status_code=500, detail=result['message'])
            
    except Exception as e:
        logger.error(f"获取统计信息失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取统计信息失败: {str(e)}")

@router.get("/data-count", response_model=DataCountResponse)
async def get_data_count(
    time_field: str = Query(..., description="时间字段名"),
    start_time: str = Query(..., description="开始时间"),
    end_time: str = Query(..., description="结束时间"),
    db_manager: UnifiedDatabaseManager = Depends(get_db_manager)
):
    """查询指定时间范围内的数据量"""
    try:
        # 获取舆情数据库
        sentiment_db = db_manager.get_sentiment_database()
        
        # 构建时间过滤条件
        filters = {
            time_field: {
                "start": start_time,
                "end": end_time
            }
        }
        
        # 查询数据量
        result = sentiment_db.get_data_count(filters)
        
        if result['success']:
            return DataCountResponse(
                success=True,
                total=result.get('total', 0),
                message=result.get('message', '查询成功')
            )
        else:
            raise HTTPException(status_code=500, detail=result['message'])
            
    except Exception as e:
        logger.error(f"查询数据量失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"查询数据量失败: {str(e)}")

@router.post("/import", response_model=DataResponse)
async def import_csv_data(
    csv_path: str,
    chunk_size: int = Query(1000, ge=100, le=10000, description="批处理大小"),
    db_manager: UnifiedDatabaseManager = Depends(get_db_manager)
):
    """导入CSV数据"""
    try:
        # 获取舆情数据库
        sentiment_db = db_manager.get_sentiment_database()
        result = sentiment_db.import_csv_data(csv_path, chunk_size)
        
        if result['success']:
            return DataResponse(
                success=True,
                message=result['message'],
                total=result.get('total_rows', 0)
            )
        else:
            raise HTTPException(status_code=400, detail=result['message'])
            
    except Exception as e:
        logger.error(f"导入CSV数据失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"导入CSV数据失败: {str(e)}")

@router.get("/time-range", response_model=TimeRangeResponse)
async def get_time_range(
    db_manager: UnifiedDatabaseManager = Depends(get_db_manager)
):
    """获取数据库中的时间范围"""
    try:
        # 获取舆情数据库
        sentiment_db = db_manager.get_sentiment_database()
        result = sentiment_db.get_time_range()
        
        if result['success']:
            return TimeRangeResponse(
                success=True,
                earliest_time=result.get('earliest_time'),
                latest_time=result.get('latest_time'),
                message=result.get('message', '查询成功')
            )
        else:
            raise HTTPException(status_code=500, detail=result['message'])
            
    except Exception as e:
        logger.error(f"获取时间范围失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取时间范围失败: {str(e)}")

@router.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy", "message": "数据库API服务正常"}
