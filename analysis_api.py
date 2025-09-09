#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
分析API接口
提供时间范围查询、数据量统计和最新数据分析功能
"""

from fastapi import APIRouter, HTTPException, Query, Depends
from typing import List, Dict, Optional, Any
from pydantic import BaseModel
from database_manager import UnifiedDatabaseManager
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# 创建API路由器
router = APIRouter(prefix="/api/analysis", tags=["分析"])

# 数据模型
class TimeRangeQuery(BaseModel):
    time_field: str
    start_time: str
    end_time: str
    count_only: bool = False

class AnalysisRequest(BaseModel):
    time_field: str
    start_time: str
    end_time: str
    limit: int = 100
    analysis_modules: List[str] = ["sentiment", "tags", "companies", "duplication"]

class AnalysisResponse(BaseModel):
    success: bool
    data: Optional[List[Dict[str, Any]]] = None
    total: Optional[int] = None
    analysis_results: Optional[Dict[str, Any]] = None
    message: Optional[str] = None
    error: Optional[str] = None

# 依赖注入
def get_db_manager():
    """获取统一数据库管理器实例"""
    return UnifiedDatabaseManager()

@router.get("/data-count")
async def get_data_count(
    time_field: str = Query(..., description="时间字段名"),
    start_time: str = Query(..., description="开始时间"),
    end_time: str = Query(..., description="结束时间"),
    db_manager: UnifiedDatabaseManager = Depends(get_db_manager)
):
    """根据时间范围查询数据量，使用统一的时间处理逻辑"""
    try:
        # 获取舆情数据库
        sentiment_db = db_manager.get_sentiment_database()
        
        # 构建时间过滤条件 - 使用与筛选数据量相同的格式
        filters = {
            time_field: {
                "start": start_time,
                "end": end_time
            }
        }
        
        # 查询数据量 - 使用统一的查询方法
        result = sentiment_db.get_data_count(filters=filters)
        
        if result['success']:
            return {
                "success": True,
                "total": result['total'],
                "time_range": f"{start_time} 至 {end_time}",
                "field": time_field
            }
        else:
            raise HTTPException(status_code=500, detail=result['message'])
            
    except Exception as e:
        logger.error(f"查询数据量失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"查询数据量失败: {str(e)}")

@router.get("/latest-data")
async def get_latest_data(
    limit: int = Query(100, ge=1, le=1000, description="数据条数限制"),
    time_field: str = Query("publish_time", description="时间字段名"),
    db_manager: UnifiedDatabaseManager = Depends(get_db_manager)
):
    """获取最新时间内的前N条数据"""
    try:
        # 获取舆情数据库
        sentiment_db = db_manager.get_sentiment_database()
        
        # 查询最新数据
        result = sentiment_db.get_data(
            fields=["*"],
            sort_by=time_field,
            sort_order="DESC",
            page=1,
            page_size=limit
        )
        
        if result['success']:
            return {
                "success": True,
                "data": result['data'],
                "total": len(result['data']),
                "time_field": time_field,
                "limit": limit
            }
        else:
            raise HTTPException(status_code=500, detail=result['message'])
            
    except Exception as e:
        logger.error(f"获取最新数据失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取最新数据失败: {str(e)}")

@router.post("/analyze-latest")
async def analyze_latest_data(
    request: AnalysisRequest,
    db_manager: UnifiedDatabaseManager = Depends(get_db_manager)
):
    """分析最新时间内的数据，使用统一的时间处理逻辑"""
    try:
        # 获取舆情数据库
        sentiment_db = db_manager.get_sentiment_database()
        
        # 构建时间过滤条件 - 使用与筛选数据量相同的格式
        filters = {
            request.time_field: {
                "start": request.start_time,
                "end": request.end_time
            }
        }
        
        # 查询数据 - 使用统一的查询方法
        result = sentiment_db.get_data(
            fields=["*"],
            filters=filters,
            sort_by=request.time_field,
            sort_order="DESC",
            page=1,
            page_size=request.limit
        )
        
        if not result['success']:
            raise HTTPException(status_code=500, detail=result['message'])
        
        # 分析数据
        analysis_results = await analyze_data_batch(
            result['data'], 
            request.analysis_modules,
            db_manager
        )
        
        return AnalysisResponse(
            success=True,
            data=result['data'],
            total=len(result['data']),
            analysis_results=analysis_results,
            message=f"成功分析 {len(result['data'])} 条数据"
        )
        
    except Exception as e:
        logger.error(f"分析数据失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"分析数据失败: {str(e)}")

async def analyze_data_batch(
    data: List[Dict[str, Any]], 
    modules: List[str],
    db_manager: UnifiedDatabaseManager
) -> Dict[str, Any]:
    """批量分析数据"""
    results = {
        "total_processed": len(data),
        "sentiment_analysis": [],
        "tag_analysis": [],
        "company_analysis": [],
        "duplication_analysis": [],
        "processing_time": None
    }
    
    start_time = datetime.now()
    
    try:
        # 这里应该调用相应的分析模块
        # 暂时返回模拟结果
        for item in data:
            if "sentiment" in modules:
                results["sentiment_analysis"].append({
                    "id": item.get("id"),
                    "sentiment": "positive",  # 模拟结果
                    "confidence": 0.85
                })
            
            if "tags" in modules:
                results["tag_analysis"].append({
                    "id": item.get("id"),
                    "tags": ["科技", "创新"],  # 模拟结果
                    "confidence": 0.90
                })
            
            if "companies" in modules:
                results["company_analysis"].append({
                    "id": item.get("id"),
                    "companies": ["示例公司"],  # 模拟结果
                    "confidence": 0.88
                })
            
            if "duplication" in modules:
                results["duplication_analysis"].append({
                    "id": item.get("id"),
                    "is_duplicate": False,  # 模拟结果
                    "similarity": 0.15
                })
        
        results["processing_time"] = (datetime.now() - start_time).total_seconds()
        
    except Exception as e:
        logger.error(f"批量分析失败: {str(e)}")
        results["error"] = str(e)
    
    return results

@router.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy", "message": "分析API服务正常"}
