#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
数据库配置管理API
提供数据库配置的查询和状态检查功能
集成到现有的数据库管理系统中
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from database_manager import UnifiedDatabaseManager
import logging

logger = logging.getLogger(__name__)

# 创建API路由器
router = APIRouter(prefix="/api/database-config", tags=["数据库配置管理"])

# 数据模型
class DatabaseStatusResponse(BaseModel):
    success: bool
    data: Optional[Dict[str, Any]] = None
    message: Optional[str] = None
    error: Optional[str] = None

class DatabaseConfigResponse(BaseModel):
    success: bool
    configs: Optional[Dict[str, Any]] = None
    message: Optional[str] = None
    error: Optional[str] = None

# 依赖注入
def get_db_manager():
    """获取统一数据库管理器实例"""
    return UnifiedDatabaseManager()

# API端点
@router.get("/status", response_model=DatabaseStatusResponse)
async def get_database_status(
    db_manager = Depends(get_db_manager)
):
    """获取所有数据库状态"""
    try:
        status = db_manager.get_database_status()
        
        return DatabaseStatusResponse(
            success=True,
            data=status,
            message="数据库状态获取成功"
        )
        
    except Exception as e:
        logger.error(f"获取数据库状态失败: {str(e)}")
        return DatabaseStatusResponse(
            success=False,
            error=f"获取状态失败: {str(e)}"
        )

@router.get("/configs", response_model=DatabaseConfigResponse)
async def get_database_configs(
    db_manager = Depends(get_db_manager)
):
    """获取数据库配置信息"""
    try:
        configs = db_manager.get_database_configs()
        
        return DatabaseConfigResponse(
            success=True,
            configs=configs,
            message="数据库配置获取成功"
        )
        
    except Exception as e:
        logger.error(f"获取数据库配置失败: {str(e)}")
        return DatabaseConfigResponse(
            success=False,
            error=f"获取配置失败: {str(e)}"
        )

@router.get("/sentiment/records", response_model=DatabaseStatusResponse)
async def get_sentiment_database_info(
    db_manager = Depends(get_db_manager)
):
    """获取舆情数据库信息"""
    try:
        sentiment_db = db_manager.get_sentiment_database()
        info = sentiment_db.get_database_info()
        
        return DatabaseStatusResponse(
            success=True,
            data=info,
            message="舆情数据库信息获取成功"
        )
        
    except Exception as e:
        logger.error(f"获取舆情数据库信息失败: {str(e)}")
        return DatabaseStatusResponse(
            success=False,
            error=f"获取信息失败: {str(e)}"
        )

@router.get("/result/records", response_model=DatabaseStatusResponse)
async def get_result_database_info(
    db_manager = Depends(get_db_manager)
):
    """获取结果数据库信息"""
    try:
        result_db = db_manager.get_result_database()
        info = result_db.get_database_info()
        
        return DatabaseStatusResponse(
            success=True,
            data=info,
            message="结果数据库信息获取成功"
        )
        
    except Exception as e:
        logger.error(f"获取结果数据库信息失败: {str(e)}")
        return DatabaseStatusResponse(
            success=False,
            error=f"获取信息失败: {str(e)}"
        )

@router.get("/types", response_model=DatabaseConfigResponse)
async def get_database_types():
    """获取支持的数据库类型"""
    try:
        types = [
            {"value": "sqlite", "name": "SQLite", "description": "轻量级文件数据库"},
            {"value": "mysql", "name": "MySQL", "description": "关系型数据库"},
            {"value": "postgresql", "name": "PostgreSQL", "description": "高级关系型数据库"},
            {"value": "mongodb", "name": "MongoDB", "description": "文档型数据库"}
        ]
        
        return DatabaseConfigResponse(
            success=True,
            configs={"types": types}
        )
        
    except Exception as e:
        logger.error(f"获取数据库类型失败: {str(e)}")
        return DatabaseConfigResponse(
            success=False,
            error=f"获取类型失败: {str(e)}"
        )
