#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
结果API接口
提供分析结果的保存、查询和导出功能
"""

from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from typing import List, Dict, Optional, Any
from pydantic import BaseModel
from database_manager import UnifiedDatabaseManager
from result_database_new import ResultDatabase
import logging

# 初始化数据库实例
result_database = ResultDatabase('data/analysis_results.db')
from datetime import datetime
import json
import csv
import io
from comprehensive_fixes import ComprehensiveFixes
from auto_deduplicator import get_auto_deduplicator, get_database_auto_deduplicator

logger = logging.getLogger(__name__)

# 创建API路由器
router = APIRouter(tags=["结果"])

# 数据模型
class ExportRequest(BaseModel):
    format: str = "csv"  # csv, json, excel
    options: Dict[str, bool] = {}
    auto_deduplicate: bool = True  # 默认启用自动去重
    similarity_threshold: float = 0.85  # 相似度阈值

# 依赖注入
def get_db_manager():
    """获取统一数据库管理器实例"""
    return UnifiedDatabaseManager()

def get_result_db():
    """获取新的结果数据库实例"""
    return ResultDatabase('data/analysis_results.db')

@router.post("/save")
async def save_results(
    request: Dict[str, Any],
    db_manager: UnifiedDatabaseManager = Depends(get_db_manager)
):
    """保存分析结果"""
    try:
        results = request.get('results', [])
        database = request.get('database', 'default')
        
        if not results:
            raise HTTPException(status_code=400, detail="没有结果数据")
        
        # 获取结果数据库
        result_db = db_manager.get_result_database()
        
        # 保存结果
        saved_count = 0
        for result_data in results:
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
            "total_count": len(results)
        }
        
    except Exception as e:
        logger.error(f"保存分析结果失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"保存分析结果失败: {str(e)}")

@router.get("/list")
async def list_results(
    page: int = 1,
    page_size: int = 50,
    result_db: ResultDatabase = Depends(get_result_db)
):
    """获取分析结果列表"""
    try:
        # 查询结果
        result = result_db.get_analysis_results(
            page=page,
            page_size=page_size
        )
        
        if result['success']:
            return {
                "success": True,
                "data": result['data'],
                "total": result['total'],
                "page": page,
                "page_size": page_size,
                "total_pages": result['total_pages']
            }
        else:
            raise HTTPException(status_code=500, detail=result['message'])
            
    except Exception as e:
        logger.error(f"获取分析结果失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取分析结果失败: {str(e)}")

@router.get("/article/{article_id}")
async def get_article_detail(
    article_id: int,
    result_db: ResultDatabase = Depends(get_result_db)
):
    """获取单条文章详情"""
    try:
        # 查询单条结果
        result = result_db.get_analysis_result_by_id(article_id)
        
        if result['success']:
            return {
                "success": True,
                "data": result['data']
            }
        else:
            raise HTTPException(status_code=404, detail=result['message'])
            
    except Exception as e:
        logger.error(f"获取文章详情失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取文章详情失败: {str(e)}")

@router.post("/export")
async def export_results(
    request: ExportRequest,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    session_id: Optional[str] = None,
    result_db: ResultDatabase = Depends(get_result_db)
):
    """导出分析结果"""
    try:
        # 优先按会话ID导出
        if session_id:
            result = result_db.get_results_by_session(session_id)
            if not result['success']:
                raise HTTPException(status_code=500, detail=result['message'])
            data = result['data']
            logger.info(f"按会话ID导出: {session_id}, 共 {len(data)} 条记录")
        else:
            # 获取所有结果数据
            result = result_db.get_analysis_results(
                page=1,
                page_size=10000  # 获取大量数据用于导出
            )
            
            if not result['success']:
                raise HTTPException(status_code=500, detail=result['message'])
            
            data = result['data']
        
        # 如果有日期过滤参数，使用SQL查询获取数据
        if start_date and end_date:
            try:
                import sqlite3
                with sqlite3.connect(result_db.db_path) as conn:
                    cursor = conn.cursor()
                    
                    # 构建日期过滤的SQL查询
                    query = '''
                    SELECT * FROM sentiment_results 
                    WHERE publish_time BETWEEN ? AND ? 
                    ORDER BY id DESC
                    '''
                    cursor.execute(query, (start_date, end_date))
                    logger.info(f"JSON导出应用日期过滤: {start_date} 到 {end_date}")
                    
                    columns = [description[0] for description in cursor.description]
                    rows = cursor.fetchall()
                    data = [dict(zip(columns, row)) for row in rows]
                    logger.info(f"JSON导出通过SQL查询获取到 {len(data)} 条记录")
            except Exception as e:
                logger.error(f"JSON导出SQL查询失败: {e}")
                raise HTTPException(status_code=500, detail="获取数据失败")
        
        if not data:
            raise HTTPException(status_code=404, detail="没有可导出的数据")
        
        logger.info(f"导出前数据量: {len(data)} 条")
        
        # 🔧 自动去重处理
        if request.auto_deduplicate and len(data) > 1:
            logger.info(f"🔄 开始自动去重处理，相似度阈值: {request.similarity_threshold}")
            
            try:
                # 获取自动去重器
                deduplicator = get_auto_deduplicator()
                deduplicator.similarity_threshold = request.similarity_threshold
                
                # 执行自动去重
                dedup_result = deduplicator.auto_deduplicate_export_data(data)
                
                if dedup_result['success']:
                    data = dedup_result['data']
                    stats = dedup_result['stats']
                    
                    logger.info(f"✅ 去重完成: {stats['original_count']} → {stats['final_count']} 条 (移除 {stats['removed_count']} 条重复)")
                    logger.info(f"去重率: {stats['deduplication_rate']:.2%}, 处理时间: {stats['processing_time_seconds']:.2f}s")
                else:
                    logger.warning(f"⚠️ 去重失败，使用原始数据: {dedup_result['message']}")
                    
            except Exception as e:
                logger.error(f"❌ 自动去重过程出错，使用原始数据: {str(e)}")
        else:
            logger.info("ℹ️ 跳过自动去重 (未启用或数据量不足)")
        
        # 根据格式导出
        if request.format.lower() == 'csv':
            return export_as_csv(data, request.options)
        elif request.format.lower() == 'json':
            return export_as_json(data, request.options)
        else:
            raise HTTPException(status_code=400, detail="不支持的导出格式")
            
    except Exception as e:
        logger.error(f"导出结果失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"导出结果失败: {str(e)}")

def export_as_csv(data: List[Dict], options: Dict[str, bool]):
    """导出为CSV格式"""
    try:
        # 准备CSV数据
        csv_data = []
        
        # 标签名称列表
        tag_names = [
            "同业竞争", "股权与控制权", "关联交易", "历史沿革与股东核查", "重大违法违规",
            "收入与成本", "财务内控不规范", "客户与供应商", "资产质量与减值", "研发与技术",
            "募集资金用途", "突击分红与对赌协议", "市场传闻与负面报道", "行业政策与环境"
        ]
        
        for item in data:
            row = {}
            
            if options.get('original', True):
                row['原始ID'] = item.get('original_id', '')
                row['标题'] = item.get('title', '')
                row['内容'] = item.get('content', '')
                row['摘要'] = item.get('summary', '')
                row['来源'] = item.get('source', '')
                row['发布时间'] = item.get('publish_time', '')
            
            if options.get('sentiment', True):
                row['情感等级'] = item.get('sentiment_level', '')
                row['情感原因'] = item.get('sentiment_reason', '')
            
            if options.get('tags', True):
                # 添加所有标签字段
                for tag_name in tag_names:
                    tag_key = f'tag_{tag_name}'
                    reason_key = f'reason_{tag_name}'
                    row[f'标签_{tag_name}'] = item.get(tag_key, '否')
                    row[f'原因_{tag_name}'] = item.get(reason_key, '无')
            
            if options.get('companies', True):
                row['涉及企业'] = item.get('companies', '')
            
            if options.get('duplication', True):
                row['重复ID'] = item.get('duplicate_id', '')
                row['重复度'] = item.get('duplication_rate', '')
            
            if options.get('processingTime', True):
                row['处理时间(s)'] = item.get('processing_time', '')
            
            csv_data.append(row)
        
        # 创建CSV文件
        output = io.StringIO()
        if csv_data:
            writer = csv.DictWriter(output, fieldnames=csv_data[0].keys())
            writer.writeheader()
            writer.writerows(csv_data)
        
        # 返回CSV文件
        output.seek(0)
        filename = f"analysis_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except Exception as e:
        logger.error(f"CSV导出失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"CSV导出失败: {str(e)}")

def export_as_json(data: List[Dict], options: Dict[str, bool]):
    """导出为JSON格式"""
    try:
        # 根据选项过滤数据
        filtered_data = []
        
        # 标签名称列表
        tag_names = [
            "同业竞争", "股权与控制权", "关联交易", "历史沿革与股东核查", "重大违法违规",
            "收入与成本", "财务内控不规范", "客户与供应商", "资产质量与减值", "研发与技术",
            "募集资金用途", "突击分红与对赌协议", "市场传闻与负面报道", "行业政策与环境"
        ]
        
        for item in data:
            filtered_item = {}
            
            if options.get('original', True):
                filtered_item['original_id'] = item.get('original_id')
                filtered_item['title'] = item.get('title')
                filtered_item['content'] = item.get('content')
                filtered_item['summary'] = item.get('summary')
                filtered_item['source'] = item.get('source')
                filtered_item['publish_time'] = item.get('publish_time')
            
            if options.get('sentiment', True):
                filtered_item['sentiment_level'] = item.get('sentiment_level')
                filtered_item['sentiment_reason'] = item.get('sentiment_reason')
            
            if options.get('tags', True):
                # 添加所有标签字段
                tag_results = {}
                for tag_name in tag_names:
                    tag_key = f'tag_{tag_name}'
                    reason_key = f'reason_{tag_name}'
                    tag_results[tag_name] = {
                        'belongs': item.get(tag_key, '否'),
                        'reason': item.get(reason_key, '无')
                    }
                filtered_item['tag_results'] = tag_results
            
            if options.get('companies', True):
                filtered_item['companies'] = item.get('companies')
            
            if options.get('duplication', True):
                filtered_item['duplicate_id'] = item.get('duplicate_id')
                filtered_item['duplication_rate'] = item.get('duplication_rate')
            
            if options.get('processingTime', True):
                filtered_item['processing_time'] = item.get('processing_time')
            
            filtered_data.append(filtered_item)
        
        # 返回JSON文件
        filename = f"analysis_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        return StreamingResponse(
            iter([json.dumps(filtered_data, ensure_ascii=False, indent=2)]),
            media_type="application/json",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except Exception as e:
        logger.error(f"JSON导出失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"JSON导出失败: {str(e)}")

@router.get("/export/excel")
async def export_excel(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
):
    """导出Excel文件"""
    try:
        logger.info("开始Excel导出")
        
        # 使用全局数据库实例
        db = result_database
        
        # 如果有日期过滤参数，直接使用SQL查询
        if start_date and end_date:
            results = []  # 强制使用SQL查询
        else:
            # 获取所有分析结果
            results_data = db.get_analysis_results(page_size=10000)  # 获取大量数据
            results = results_data.get('results', [])
        
        # 如果需要使用SQL查询
        if (start_date and end_date) or not results:
            # 如果使用新方法没有数据，尝试直接SQL查询
            import sqlite3
            try:
                with sqlite3.connect(db.db_path) as conn:
                    cursor = conn.cursor()
                    
                    # 构建日期过滤的SQL查询
                    if start_date and end_date:
                        query = '''
                        SELECT * FROM sentiment_results 
                        WHERE publish_time BETWEEN ? AND ? 
                        ORDER BY id DESC
                        '''
                        cursor.execute(query, (start_date, end_date))
                        logger.info(f"应用日期过滤: {start_date} 到 {end_date}")
                    else:
                        cursor.execute('SELECT * FROM sentiment_results ORDER BY id DESC')
                    
                    columns = [description[0] for description in cursor.description]
                    rows = cursor.fetchall()
                    results = [dict(zip(columns, row)) for row in rows]
                    logger.info(f"通过直接SQL查询获取到 {len(results)} 条记录")
            except Exception as e:
                logger.error(f"直接SQL查询失败: {e}")
                raise HTTPException(status_code=500, detail="获取数据失败")
        
        if not results:
            raise HTTPException(status_code=404, detail="没有可导出的数据")
        
        # 创建Excel文件
        from io import BytesIO
        import pandas as pd
        
        # 准备导出数据
        export_data = []
        for result in results:
            row = {
                'ID': result.get('id', ''),
                '原始ID': result.get('original_id', ''),
                '标题': result.get('title', ''),
                '内容': result.get('content', ''),
                '摘要': result.get('summary', ''),
                '来源': result.get('source', ''),
                '发布时间': result.get('publish_time', ''),
                '情感倾向': result.get('sentiment_level', ''),
                '情感原因': result.get('sentiment_reason', ''),
                '相关公司': result.get('companies', ''),
                '重复ID': result.get('duplicate_id', ''),
                '重复率': result.get('duplication_rate', 0),
                '处理时间(ms)': result.get('processing_time', 0),
                '分析时间': result.get('analysis_time', ''),
                '处理状态': result.get('processing_status', '')
            }
            
            # 添加标签字段
            tag_labels = ['同业竞争', '股权与控制权', '关联交易', '历史沿革与股东核查', '重大违法违规',
                         '收入与成本', '财务内控不规范', '客户与供应商', '资产质量与减值', '研发与技术',
                         '募集资金用途', '突击分红与对赌协议', '市场传闻与负面报道', '行业政策与环境']
            
            for tag in tag_labels:
                tag_key = f'tag_{tag}'
                reason_key = f'reason_{tag}'
                row[f'标签-{tag}'] = result.get(tag_key, '否')
                row[f'原因-{tag}'] = result.get(reason_key, '无')
            
            export_data.append(row)
        
        # 创建DataFrame
        df = pd.DataFrame(export_data)
        
        # 写入Excel
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='分析结果', index=False)
        
        output.seek(0)
        excel_data = output.read()
        
        logger.info(f"Excel导出成功，共导出 {len(results)} 条记录，文件大小: {len(excel_data)} 字节")
        
        # 返回Excel文件
        from fastapi.responses import Response
        return Response(
            content=excel_data,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": "attachment; filename=sentiment_analysis_results.xlsx"}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Excel导出失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Excel导出失败: {str(e)}")

@router.get("/export/json")
async def export_json(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    auto_deduplicate: bool = True,
    similarity_threshold: float = 0.85
):
    """导出JSON文件"""
    try:
        logger.info("开始JSON导出")
        
        # 使用全局数据库实例
        db = result_database
        
        # 如果有日期过滤参数，直接使用SQL查询
        if start_date and end_date:
            results = []  # 强制使用SQL查询
        else:
            # 获取所有分析结果
            results_data = db.get_analysis_results(page_size=10000)  # 获取大量数据
            results = results_data.get('results', [])
        
        # 如果需要使用SQL查询
        if (start_date and end_date) or not results:
            # 如果使用新方法没有数据，尝试直接SQL查询
            import sqlite3
            try:
                with sqlite3.connect(db.db_path) as conn:
                    cursor = conn.cursor()
                    
                    # 构建日期过滤的SQL查询
                    if start_date and end_date:
                        query = '''
                        SELECT * FROM sentiment_results 
                        WHERE publish_time BETWEEN ? AND ? 
                        ORDER BY id DESC
                        '''
                        cursor.execute(query, (start_date, end_date))
                        logger.info(f"JSON导出应用日期过滤: {start_date} 到 {end_date}")
                    else:
                        cursor.execute('SELECT * FROM sentiment_results ORDER BY id DESC')
                    
                    columns = [description[0] for description in cursor.description]
                    rows = cursor.fetchall()
                    results = [dict(zip(columns, row)) for row in rows]
                    logger.info(f"JSON导出通过SQL查询获取到 {len(results)} 条记录")
            except Exception as e:
                logger.error(f"JSON导出SQL查询失败: {e}")
                raise HTTPException(status_code=500, detail="获取数据失败")
        
        if not results:
            raise HTTPException(status_code=404, detail="没有可导出的数据")
        
        logger.info(f"导出前数据量: {len(results)} 条")
        
        # 准备JSON导出数据
        export_data = []
        for result in results:
            item = {
                'id': result.get('id', ''),
                'original_id': result.get('original_id', ''),
                'title': result.get('title', ''),
                'content': result.get('content', ''),
                'summary': result.get('summary', ''),
                'source': result.get('source', ''),
                'publish_time': result.get('publish_time', ''),
                'sentiment_level': result.get('sentiment_level', ''),
                'sentiment_reason': result.get('sentiment_reason', ''),
                'companies': result.get('companies', ''),
                'duplicate_id': result.get('duplicate_id', ''),
                'duplication_rate': result.get('duplication_rate', 0),
                'processing_time': result.get('processing_time', 0),
                'analysis_time': result.get('analysis_time', ''),
                'processing_status': result.get('processing_status', '')
            }
            
            # 添加标签字段
            tag_labels = ['同业竞争', '股权与控制权', '关联交易', '历史沿革与股东核查', '重大违法违规',
                         '收入与成本', '财务内控不规范', '客户与供应商', '资产质量与减值', '研发与技术',
                         '募集资金用途', '突击分红与对赌协议', '市场传闻与负面报道', '行业政策与环境']
            
            tag_results = {}
            for tag in tag_labels:
                tag_key = f'tag_{tag}'
                reason_key = f'reason_{tag}'
                tag_results[tag] = {
                    'belongs': result.get(tag_key, '否'),
                    'reason': result.get(reason_key, '无')
                }
            
            item['tag_results'] = tag_results
            export_data.append(item)
        
        # 🔧 自动去重处理
        if auto_deduplicate and len(export_data) > 1:
            logger.info(f"🔄 开始自动去重处理，相似度阈值: {similarity_threshold}")
            
            try:
                # 获取自动去重器
                deduplicator = get_auto_deduplicator()
                deduplicator.similarity_threshold = similarity_threshold
                
                # 执行自动去重
                dedup_result = deduplicator.auto_deduplicate_export_data(export_data)
                
                if dedup_result['success']:
                    export_data = dedup_result['data']
                    stats = dedup_result['stats']
                    
                    logger.info(f"✅ 去重完成: {stats['original_count']} → {stats['final_count']} 条 (移除 {stats['removed_count']} 条重复)")
                    logger.info(f"去重率: {stats['deduplication_rate']:.2%}, 处理时间: {stats['processing_time_seconds']:.2f}s")
                else:
                    logger.warning(f"⚠️ 去重失败，使用原始数据: {dedup_result['message']}")
                    
            except Exception as e:
                logger.error(f"❌ 自动去重过程出错，使用原始数据: {str(e)}")
        else:
            logger.info("ℹ️ 跳过自动去重 (未启用或数据量不足)")
        
        # 返回JSON文件
        dedup_suffix = "_deduplicated" if auto_deduplicate and len(export_data) > 1 else ""
        filename = f"sentiment_analysis_results{dedup_suffix}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        logger.info(f"JSON导出成功，共导出 {len(export_data)} 条记录")
        
        return StreamingResponse(
            iter([json.dumps(export_data, ensure_ascii=False, indent=2)]),
            media_type="application/json",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"JSON导出失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"JSON导出失败: {str(e)}")

@router.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "results_api"
    }

# 数据库管理相关API
@router.get("/database/stats")
async def get_database_stats():
    """获取数据库统计信息"""
    try:
        fixer = ComprehensiveFixes()
        stats = fixer.get_database_stats()
        return {
            "success": True,
            "data": stats,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"获取数据库统计失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取统计信息失败: {str(e)}")

@router.post("/database/fix-summaries")
async def fix_empty_summaries():
    """修复空摘要"""
    try:
        fixer = ComprehensiveFixes()
        fixer.fix_empty_summaries()
        return {
            "success": True,
            "message": "摘要修复完成",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"修复摘要失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"修复摘要失败: {str(e)}")

@router.post("/database/detect-duplicates")
async def detect_duplicates(similarity_threshold: float = 0.8):
    """检测并标记重复数据"""
    try:
        if similarity_threshold < 0.1 or similarity_threshold > 1.0:
            raise HTTPException(status_code=400, detail="相似度阈值必须在0.1-1.0之间")
        
        fixer = ComprehensiveFixes()
        duplicate_count = fixer.detect_duplicates_and_update(similarity_threshold)
        
        return {
            "success": True,
            "message": f"重复检测完成，找到 {duplicate_count} 对重复数据",
            "duplicate_pairs": duplicate_count,
            "similarity_threshold": similarity_threshold,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"检测重复数据失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"检测重复数据失败: {str(e)}")

@router.post("/database/auto-deduplicate")
async def auto_deduplicate_database(similarity_threshold: float = 0.85):
    """自动去重数据库记录"""
    try:
        if similarity_threshold < 0.1 or similarity_threshold > 1.0:
            raise HTTPException(status_code=400, detail="相似度阈值必须在0.1-1.0之间")
        
        # 获取数据库自动去重器
        db_deduplicator = get_database_auto_deduplicator()
        db_deduplicator.similarity_threshold = similarity_threshold
        
        # 执行自动去重
        result = db_deduplicator.auto_deduplicate_database()
        
        if result['success']:
            return {
                "success": True,
                "message": result['message'],
                "stats": result['stats'],
                "similarity_threshold": similarity_threshold,
                "timestamp": datetime.now().isoformat()
            }
        else:
            raise HTTPException(status_code=500, detail=result['message'])
            
    except Exception as e:
        logger.error(f"数据库自动去重失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"数据库自动去重失败: {str(e)}")

@router.post("/database/clean-duplicates")
async def clean_duplicate_records(keep_strategy: str = "first"):
    """清理重复记录"""
    try:
        if keep_strategy not in ["first", "latest"]:
            raise HTTPException(status_code=400, detail="保留策略必须是 'first' 或 'latest'")
        
        fixer = ComprehensiveFixes()
        deleted_count = fixer.clean_duplicate_records(keep_strategy)
        
        return {
            "success": True,
            "message": f"重复数据清理完成，删除了 {deleted_count} 条记录",
            "deleted_count": deleted_count,
            "keep_strategy": keep_strategy,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"清理重复数据失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"清理重复数据失败: {str(e)}")

@router.post("/export/deduplicated")
async def export_deduplicated_data(
    session_id: Optional[str] = None,
    format: str = "json"
):
    """导出去重后的数据"""
    try:
        if format not in ["json", "csv"]:
            raise HTTPException(status_code=400, detail="格式必须是 'json' 或 'csv'")
        
        fixer = ComprehensiveFixes()
        
        if format == "json":
            # JSON导出
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"deduplicated_results_{timestamp}.json"
            
            export_result = fixer.export_deduplicated_data(session_id, filename)
            
            if export_result.get('success'):
                # 读取生成的文件
                with open(filename, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                return StreamingResponse(
                    iter([content]),
                    media_type="application/json",
                    headers={"Content-Disposition": f"attachment; filename={filename}"}
                )
            else:
                raise HTTPException(status_code=500, detail=export_result.get('error', '导出失败'))
        
        else:
            # CSV导出 (未来实现)
            raise HTTPException(status_code=501, detail="CSV去重导出功能开发中")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"导出去重数据失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"导出失败: {str(e)}")
