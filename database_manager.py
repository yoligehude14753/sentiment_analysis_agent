#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
统一的数据库管理器
管理舆情数据库和结果数据库，并提供配置管理功能
"""

import os
import json
import logging
from typing import Dict, Any, Optional
from pydantic import BaseModel
from database import DatabaseManager
from result_database_new import ResultDatabase

logger = logging.getLogger(__name__)

class DatabaseConfig(BaseModel):
    """数据库配置模型"""
    type: str  # sqlite, mysql, postgresql, mongodb
    host: Optional[str] = None
    port: Optional[int] = None
    name: Optional[str] = None
    user: Optional[str] = None
    password: Optional[str] = None

class UnifiedDatabaseManager:
    """统一数据库管理器，管理舆情数据库和结果数据库"""
    
    def __init__(self):
        # 加载数据库配置
        self.load_database_configs()
        
        # 舆情数据库管理器 - 用于存储原始舆情数据
        self.sentiment_db = DatabaseManager(self.sentiment_db_path)
        
        # 结果数据库管理器 - 用于存储分析结果
        self.result_db = ResultDatabase(self.result_db_path)
        
        logger.info("统一数据库管理器初始化完成")
        logger.info(f"舆情数据库路径: {self.sentiment_db_path}")
        logger.info(f"结果数据库路径: {self.result_db_path}")
    
    def load_database_configs(self):
        """加载数据库配置"""
        try:
            # 默认配置
            self.sentiment_db_path = "data/sentiment_analysis.db"
            self.result_db_path = "data/analysis_results.db"
            
            # 尝试从配置文件加载
            config_file = "config/database_config.json"
            if os.path.exists(config_file):
                with open(config_file, 'r', encoding='utf-8') as f:
                    configs = json.load(f)
                    if "舆情数据库" in configs:
                        config = configs["舆情数据库"]
                        if config.get("type") == "sqlite" and config.get("name"):
                            self.sentiment_db_path = config["name"]
                    if "分析结果数据库" in configs:
                        config = configs["分析结果数据库"]
                        if config.get("type") == "sqlite" and config.get("name"):
                            self.result_db_path = config["name"]
                            
            logger.info(f"数据库配置加载完成")
            
        except Exception as e:
            logger.error(f"加载数据库配置失败: {str(e)}")
    
    def save_database_configs(self):
        """保存数据库配置到文件"""
        try:
            os.makedirs("config", exist_ok=True)
            config_file = "config/database_config.json"
            
            configs = {
                "舆情数据库": {
                    "type": "sqlite",
                    "name": self.sentiment_db_path,
                    "description": "存储原始舆情数据的数据库"
                },
                "分析结果数据库": {
                    "type": "sqlite",
                    "name": self.result_db_path,
                    "description": "存储分析结果的数据库"
                }
            }
            
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(configs, f, ensure_ascii=False, indent=2)
                
            logger.info("数据库配置已保存")
            
        except Exception as e:
            logger.error(f"保存数据库配置失败: {str(e)}")
    
    def get_database_status(self) -> Dict[str, Any]:
        """获取所有数据库状态"""
        try:
            sentiment_info = self.sentiment_db.get_database_info()
            result_info = self.result_db.get_database_info()
            
            return {
                "sentiment_database": {
                    "name": "舆情数据库",
                    "path": sentiment_info.get('database_path', 'N/A'),
                    "file_size_mb": sentiment_info.get('file_size_mb', 0),
                    "tables": sentiment_info.get('tables', []),
                    "total_records": sentiment_info.get('total_records', 0),
                    "description": "存储原始舆情数据，作为分析的数据源"
                },
                "result_database": {
                    "name": "分析结果数据库", 
                    "path": result_info.get('database_path', 'N/A'),
                    "file_size_mb": result_info.get('file_size_mb', 0),
                    "tables": result_info.get('tables', []),
                    "total_records": result_info.get('total_records', 0),
                    "description": "存储系统分析完成的结果数据"
                },
                "total_size_mb": sentiment_info.get('file_size_mb', 0) + result_info.get('file_size_mb', 0),
                "status": "healthy"
            }
            
        except Exception as e:
            logger.error(f"获取数据库状态失败: {str(e)}")
            return {
                "status": "error",
                "error_message": str(e)
            }
    
    def get_sentiment_database(self) -> DatabaseManager:
        """获取舆情数据库管理器"""
        return self.sentiment_db
    
    def get_result_database(self) -> ResultDatabase:
        """获取结果数据库管理器"""
        return self.result_db
    
    def get_database_configs(self) -> Dict[str, Any]:
        """获取数据库配置信息"""
        return {
            "舆情数据库": {
                "type": "sqlite",
                "path": self.sentiment_db_path,
                "description": "测试数据库，存储原始舆情数据"
            },
            "分析结果数据库": {
                "type": "sqlite", 
                "path": self.result_db_path,
                "description": "结果数据库，存储分析完成的数据"
            }
        }
    
    def update_database_paths(self, sentiment_path: str = None, result_path: str = None):
        """更新数据库路径"""
        if sentiment_path:
            self.sentiment_db_path = sentiment_path
            self.sentiment_db = DatabaseManager(sentiment_path)
            logger.info(f"舆情数据库路径已更新: {sentiment_path}")
            
        if result_path:
            self.result_db_path = result_path
            self.result_db = ResultDatabase(result_path)
            logger.info(f"结果数据库路径已更新: {result_path}")
        
        # 保存配置
        self.save_database_configs()
    
    def backup_databases(self, backup_dir: str = "data/backup") -> Dict[str, Any]:
        """备份所有数据库"""
        try:
            os.makedirs(backup_dir, exist_ok=True)
            
            import shutil
            from datetime import datetime
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # 备份舆情数据库
            sentiment_backup = f"{backup_dir}/sentiment_analysis_{timestamp}.db"
            shutil.copy2(self.sentiment_db.db_path, sentiment_backup)
            
            # 备份结果数据库
            result_backup = f"{backup_dir}/resultdatabase_{timestamp}.db"
            shutil.copy2(self.result_db.db_path, result_backup)
            
            logger.info(f"数据库备份完成: {backup_dir}")
            
            return {
                "status": "success",
                "backup_dir": backup_dir,
                "sentiment_backup": sentiment_backup,
                "result_backup": result_backup,
                "timestamp": timestamp
            }
            
        except Exception as e:
            logger.error(f"数据库备份失败: {str(e)}")
            return {
                "status": "error",
                "error_message": str(e)
            }
    
    def cleanup_old_data(self, sentiment_days: int = 90, result_days: int = 30) -> Dict[str, Any]:
        """清理旧数据"""
        try:
            # 清理舆情数据库旧数据
            sentiment_cleaned = self.sentiment_db.cleanup_old_records(sentiment_days)
            
            # 清理结果数据库旧数据
            result_cleaned = self.result_db.cleanup_old_results(result_days)
            
            logger.info(f"数据清理完成: 舆情数据库清理{sentiment_cleaned}条，结果数据库清理{result_cleaned}条")
            
            return {
                "status": "success",
                "sentiment_cleaned": sentiment_cleaned,
                "result_cleaned": result_cleaned
            }
            
        except Exception as e:
            logger.error(f"数据清理失败: {str(e)}")
            return {
                "status": "error",
                "error_message": str(e)
            }
    
    def get_combined_statistics(self) -> Dict[str, Any]:
        """获取综合统计信息"""
        try:
            # 获取舆情数据库统计
            sentiment_stats = self.sentiment_db.get_sentiment_statistics()
            
            # 获取结果数据库统计
            result_stats = self.result_db.get_sentiment_statistics()
            
            # 合并统计信息
            combined_stats = {
                "total_sentiment_records": sentiment_stats.get('total_records', 0),
                "total_analysis_results": result_stats.get('total_analyses', 0),
                "sentiment_distribution": sentiment_stats.get('sentiment_distribution', {}),
                "analysis_sentiment_distribution": result_stats.get('sentiment_distribution', {}),
                "avg_processing_time_ms": result_stats.get('avg_processing_time_ms', 0)
            }
            
            return combined_stats
            
        except Exception as e:
            logger.error(f"获取综合统计失败: {str(e)}")
            return {}
    
    def validate_database_integrity(self) -> Dict[str, Any]:
        """验证数据库完整性"""
        try:
            validation_results = {
                "sentiment_database": {},
                "result_database": {},
                "overall_status": "healthy"
            }
            
            # 验证舆情数据库
            try:
                sentiment_info = self.sentiment_db.get_database_info()
                validation_results["sentiment_database"] = {
                    "status": "healthy",
                    "tables": sentiment_info.get('tables', []),
                    "record_count": sentiment_info.get('total_records', 0)
                }
            except Exception as e:
                validation_results["sentiment_database"] = {
                    "status": "error",
                    "error": str(e)
                }
                validation_results["overall_status"] = "error"
            
            # 验证结果数据库
            try:
                result_info = self.result_db.get_database_info()
                validation_results["result_database"] = {
                    "status": "healthy",
                    "tables": result_info.get('tables', []),
                    "record_count": result_info.get('total_records', 0)
                }
            except Exception as e:
                validation_results["result_database"] = {
                    "status": "error",
                    "error": str(e)
                }
                validation_results["overall_status"] = "error"
            
            return validation_results
            
        except Exception as e:
            logger.error(f"数据库完整性验证失败: {str(e)}")
            return {
                "overall_status": "error",
                "error_message": str(e)
            }

if __name__ == "__main__":
    # 测试统一数据库管理器
    unified_db = UnifiedDatabaseManager()
    
    print("=" * 60)
    print("统一数据库管理器测试")
    print("=" * 60)
    
    # 显示数据库状态
    status = unified_db.get_database_status()
    print(f"舆情数据库: {status.get('sentiment_database', {}).get('path', 'N/A')}")
    print(f"结果数据库: {status.get('result_database', {}).get('path', 'N/A')}")
    print(f"总大小: {status.get('total_size_mb', 0)} MB")
    
    # 显示综合统计
    stats = unified_db.get_combined_statistics()
    print(f"\n舆情记录总数: {stats.get('total_sentiment_records', 0)}")
    print(f"分析结果总数: {stats.get('total_analysis_results', 0)}")
    
    # 验证数据库完整性
    integrity = unified_db.validate_database_integrity()
    print(f"\n数据库完整性状态: {integrity.get('overall_status', 'unknown')}")
    
    print("\n统一数据库管理器测试完成！")
