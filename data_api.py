#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
数据API接口
提供数据查询、计数和保存功能
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Optional, Any
from pydantic import BaseModel
from database_manager import UnifiedDatabaseManager
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# 创建API路由器
router = APIRouter(tags=["数据"])

# 数据模型
class DataCountRequest(BaseModel):
    time_field: str
    start_time: str
    end_time: str

class DataQueryRequest(BaseModel):
    time_field: str
    start_time: str
    end_time: str
    limit: int = 1000

class ResultsSaveRequest(BaseModel):
    results: List[Dict[str, Any]]
    database: str = "default"

# 依赖注入
def get_db_manager():
    """获取统一数据库管理器实例"""
    return UnifiedDatabaseManager()

@router.post("/count")
async def get_data_count(
    request: DataCountRequest,
    db_manager: UnifiedDatabaseManager = Depends(get_db_manager)
):
    """根据时间范围查询数据量"""
    try:
        # 获取舆情数据库
        sentiment_db = db_manager.get_sentiment_database()
        
        # 构建时间过滤条件 - 使用统一的时间范围处理
        filters = {
            request.time_field: {
                "start": request.start_time,
                "end": request.end_time
            }
        }
        
        # 查询数据量 - 使用统一的查询方法
        result = sentiment_db.get_data_count(filters=filters)
        
        if result['success']:
            return {
                "success": True,
                "total": result['total'],
                "time_range": f"{request.start_time} 至 {request.end_time}",
                "field": request.time_field
            }
        else:
            raise HTTPException(status_code=500, detail=result['message'])
            
    except Exception as e:
        logger.error(f"查询数据量失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"查询数据量失败: {str(e)}")

@router.post("/query")
async def query_data(
    request: DataQueryRequest,
    db_manager: UnifiedDatabaseManager = Depends(get_db_manager)
):
    """根据时间范围查询数据"""
    try:
        # 获取舆情数据库
        sentiment_db = db_manager.get_sentiment_database()
        
        # 构建时间过滤条件
        filters = {
            request.time_field: {
                "start": request.start_time,
                "end": request.end_time
            }
        }
        
        # 查询数据
        result = sentiment_db.get_data(
            fields=['id', 'title', 'content', 'source', 'publish_time', 'company_name', 'industry'],
            filters=filters,
            page=1,
            page_size=request.limit,
            sort_by=request.time_field,
            sort_order='DESC'
        )
        
        if result['success']:
            return {
                "success": True,
                "data": result['data'],
                "total": result['total'],
                "time_range": f"{request.start_time} 至 {request.end_time}"
            }
        else:
            raise HTTPException(status_code=500, detail=result['message'])
            
    except Exception as e:
        logger.error(f"查询数据失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"查询数据失败: {str(e)}")

@router.post("/results/save")
async def save_analysis_results(
    request: ResultsSaveRequest,
    db_manager: UnifiedDatabaseManager = Depends(get_db_manager)
):
    """保存分析结果到结果数据库"""
    try:
        # 获取结果数据库
        result_db = db_manager.get_result_database()
        
        # 保存结果
        saved_count = 0
        for result_data in request.results:
            try:
                # 准备保存的数据
                save_data = {
                    'original_id': result_data.get('original_id'),
                    'title': result_data.get('title', ''),
                    'content': result_data.get('content', ''),
                    'source': result_data.get('source', ''),
                    'publish_time': result_data.get('publish_time', ''),
                    'sentiment_level': result_data.get('sentiment_level', ''),
                    'sentiment_reason': result_data.get('sentiment_reason', ''),
                    'tags': result_data.get('tags', ''),
                    'companies': result_data.get('companies', ''),
                    'processing_time': result_data.get('processing_time', 0),
                    'processed_at': result_data.get('processed_at', ''),
                    'analysis_status': result_data.get('analysis_status', 'completed')
                }
                
                # 保存到结果数据库
                save_result = result_db.save_analysis_result(save_data)
                if save_result['success']:
                    saved_count += 1
                else:
                    logger.warning(f"保存结果失败: {save_result['message']}")
                    
            except Exception as e:
                logger.error(f"保存单条结果失败: {str(e)}")
                continue
        
        return {
            "success": True,
            "message": f"成功保存 {saved_count} 条分析结果",
            "saved_count": saved_count,
            "total_count": len(request.results)
        }
        
    except Exception as e:
        logger.error(f"保存分析结果失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"保存分析结果失败: {str(e)}")

@router.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "data_api"
    }
