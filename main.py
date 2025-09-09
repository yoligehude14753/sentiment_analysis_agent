"""
舆情分析系统主应用
基于FastAPI构建的Web API服务
"""

from fastapi import FastAPI, Request, UploadFile, File, HTTPException, Query, Form
from typing import Optional
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
import uvicorn
import csv
import io
import time
from models import AnalysisRequest, CompanyInfo, TagResult, SentimentResult
from config import Config
from agents.company_agent import CompanyAgent
from agents.tag_agents import TagAgents
from agents.sentiment_agent import SentimentAgent
from fastapi.responses import StreamingResponse
from database_api import router as database_router
import pandas as pd
from datetime import datetime
from database_config_api import router as database_config_router
from analysis_api import router as analysis_router
from data_api import router as data_router
from results_api import router as results_router
import asyncio
import json
import logging

logger = logging.getLogger(__name__)

app = FastAPI(title="多Agent情感分析系统", description="专门处理企业识别、标签分类和情感等级分类")

# 初始化各个agent
company_agent = CompanyAgent()  # 企业识别模块
tag_agents = TagAgents()
sentiment_agent = SentimentAgent()
# system_agent = SystemAgent() # 暂时注释掉系统风险分析模块

# 设置模板和静态文件
templates = Jinja2Templates(directory="templates")

# 自定义静态文件处理，添加防缓存头部
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

class NoCacheStaticFiles(StaticFiles):
    def file_response(self, full_path, stat_result, scope, status_code=200):
        response = FileResponse(
            full_path, stat_result=stat_result, status_code=status_code
        )
        # 添加防缓存头部
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        return response

app.mount("/static", NoCacheStaticFiles(directory="static"), name="static")

# 集成数据库API
app.include_router(database_router)
app.include_router(database_config_router)
app.include_router(analysis_router)
app.include_router(data_router, prefix="/api/data")
app.include_router(results_router, prefix="/api/results")

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """主页 - 显示分析界面"""
    response = templates.TemplateResponse("index.html", {"request": request})
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

@app.get("/parsing", response_class=HTMLResponse)
async def parsing_tasks_page(request: Request):
    """执行解析任务页面"""
    return templates.TemplateResponse("parsing_tasks.html", {"request": request})

# 移除 /results 路由，主页直接显示分析结果

@app.get("/config", response_class=HTMLResponse)
async def config_page(request: Request):
    """配置页面"""
    return templates.TemplateResponse("config.html", {"request": request})

@app.get("/database-management", response_class=HTMLResponse)
async def database_management_page(request: Request):
    """数据库管理页面"""
    return templates.TemplateResponse("database_management.html", {"request": request})

@app.get("/database", response_class=HTMLResponse)
async def database_page(request: Request):
    """数据库管理页面"""
    return templates.TemplateResponse("database.html", {"request": request})

@app.get("/detail", response_class=HTMLResponse)
async def detail_page(request: Request):
    """文章详情页面"""
    return templates.TemplateResponse("detail.html", {"request": request})

@app.post("/api/analyze")
async def analyze_text(request: AnalysisRequest):
    """分析文本内容"""
    try:
        # 验证输入
        if not request.content or not request.content.strip():
            raise HTTPException(status_code=400, detail="文本内容不能为空")
        
        # 创建流式响应
        async def generate_stream():
            # 开始分析
            yield f"data: {json.dumps({'type': 'start', 'message': '开始分析文本...'})}\n\n"
            
            # 定义异步生成器函数
            async def sentiment_analysis():
                yield f"data: {json.dumps({'type': 'progress', 'step': 'sentiment', 'message': '正在进行情感分析...'})}\n\n"
                result = await sentiment_agent.analyze_sentiment(request.content)
                yield f"data: {json.dumps({'type': 'result', 'step': 'sentiment', 'data': result.model_dump()})}\n\n"

            async def tag_analysis():
                yield f"data: {json.dumps({'type': 'progress', 'step': 'tags', 'message': '正在进行标签分析...'})}\n\n"
                results = await tag_agents.analyze_tags(request.content)
                for tag_result in results:
                    yield f"data: {json.dumps({'type': 'progress', 'step': 'tags', 'message': f'正在分析标签: {tag_result.tag}'})}\n\n"
                    yield f"data: {json.dumps({'type': 'result', 'step': 'tags', 'data': tag_result.model_dump()})}\n\n"
                    tag_status = '匹配' if getattr(tag_result, 'belongs', False) else '不匹配'
                    yield f"data: {json.dumps({'type': 'progress', 'step': 'tags', 'message': f'标签 {tag_result.tag} 分析完成: {tag_status}'})}\n\n"

            async def company_analysis():
                yield f"data: {json.dumps({'type': 'progress', 'step': 'companies', 'message': '正在识别企业信息...'})}\n\n"
                results = await company_agent.analyze_companies(request.content)
                # 现在企业识别只返回企业名称，转换为兼容格式
                company_data = [{"name": c.name, "credit_code": "", "reason": f"LLM智能识别: {c.name}"} for c in results]
                yield f"data: {json.dumps({'type': 'result', 'step': 'companies', 'data': company_data})}\n\n"

            # 创建任务列表
            generators = [
                sentiment_analysis(),
                tag_analysis(),
                company_analysis()
            ]
            
            # 并行执行所有任务
            for generator in generators:
                async for message in generator:
                    yield message
            

            
            # 完成分析
            yield f"data: {json.dumps({'type': 'complete', 'message': '分析完成！'})}\n\n"
        
        return StreamingResponse(
            generate_stream(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"
            }
        )
        
    except Exception as e:
        logger.error(f"分析失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"分析失败: {str(e)}")

@app.get("/api/health")
async def health_check():
    """健康检查接口"""
    return {"status": "healthy", "message": "多Agent情感分析系统运行正常"}

@app.post("/api/upload_csv")
async def upload_csv(file: UploadFile = File(...)):
    """上传CSV文件进行批量分析"""
    if not file.filename.endswith('.csv'):
        return {"detail": "只支持CSV文件"}
    
    try:
        # 读取CSV文件内容
        content = await file.read()
        content_str = content.decode('utf-8')
        
        # 解析CSV
        csv_reader = csv.DictReader(io.StringIO(content_str))
        rows = list(csv_reader)
        
        if not rows:
            return {"detail": "CSV文件为空"}
        
        # 检查必要的列
        if 'content' not in rows[0]:
            return {"detail": "CSV文件必须包含'content'列"}
        
        # 批量分析
        results = []
        for row in rows:
            content_text = row['content'].strip()
            if content_text:
                # 分析单条内容
                # 创建所有分析任务
                tasks = [
                    company_agent.analyze_companies(content_text),
                    tag_agents.analyze_tags(content_text),
                    sentiment_agent.analyze_sentiment(content_text)
                ]
                
                # 并行执行所有任务
                companies, tags, sentiment = await asyncio.gather(*tasks)
                
                # 直接使用对象的model_dump方法转换为字典
                results.append({
                    "content": content_text,
                    "companies": [{"name": company.name, "credit_code": "", "reason": f"LLM智能识别: {company.name}"} for company in companies],
                    "tags": [tag.model_dump() for tag in tags],
                    "sentiment": sentiment.model_dump()
                })
        
        return {
            "total": len(results),
            "results": results
        }
        
    except Exception as e:
        return {"detail": f"处理CSV文件失败: {str(e)}"}

@app.post("/api/batch_parse")
async def batch_parse_data(request: Request):
    """批量解析数据接口 - 使用真实数据"""
    try:
        from database_manager import UnifiedDatabaseManager
        from result_database_new import ResultDatabase
        import hashlib
        
        body = await request.json()
        data_source = body.get("data_source", "舆情数据")
        data_range = body.get("data_range", "all")
        # 兼容两种参数名称：优先使用 start_time/end_time，回退到 start_date/end_date
        start_date = body.get("start_time") or body.get("start_date")
        end_date = body.get("end_time") or body.get("end_date")
        
        enable_sentiment = body.get("enable_sentiment", True)
        enable_tags = body.get("enable_tags", True)
        enable_companies = body.get("enable_companies", True)
        
        # 生成唯一的会话ID
        import uuid
        session_id = str(uuid.uuid4())
        
        # 创建流式响应
        async def generate_stream():
            # 调试信息
            start_time_param = body.get("start_time")
            end_time_param = body.get("end_time")
            yield f"data: {json.dumps({'type': 'log', 'message': f'接收到的参数: start_time={start_time_param}, end_time={end_time_param}'})}\n\n"
            yield f"data: {json.dumps({'type': 'log', 'message': f'解析后的时间: start_date={start_date}, end_date={end_date}'})}\n\n"
            try:
                yield f"data: {json.dumps({'type': 'start', 'message': f'开始批量解析 {data_source} 数据...'})}\n\n"
                
                # 获取数据库管理器
                db_manager = UnifiedDatabaseManager()
                result_db = ResultDatabase('data/analysis_results.db')
                
                # 初始化重复检测管理器
                from text_deduplicator import DuplicateDetectionManager
                duplicate_manager = DuplicateDetectionManager({
                    'similarity_threshold': 0.6,  # 降低阈值以捕获更多相似文本
                    'hamming_threshold': 25        # 基于测试结果，汉明距离25可以捕获相似文本
                })
                
                yield f"data: {json.dumps({'type': 'log', 'message': '初始化SimHash重复检测系统...'})}\n\n"
                
                # 从舆情数据库获取实际数据
                sentiment_db = db_manager.get_sentiment_database()
                
                # 构建查询条件 - 修复SQLite参数绑定问题
                filters = {}
                if start_date and end_date:
                    # 使用与筛选数据量相同的时间范围处理方式
                    # 确保时间格式统一，精确到分钟
                    filters["publish_time"] = {
                        "start": start_date,
                        "end": end_date
                    }
                    
                    # 记录时间范围信息
                    yield f"data: {json.dumps({'type': 'log', 'message': f'查询时间范围: {start_date} 至 {end_date}'})}\n\n"
                else:
                    yield f"data: {json.dumps({'type': 'log', 'message': '未指定时间范围，将查询所有数据'})}\n\n"
                
                # 先获取数据总量 - 使用与筛选数据量相同的查询方式
                count_result = sentiment_db.get_data_count(filters=filters)
                
                if not count_result['success']:
                    error_msg = count_result.get('message', '未知错误')
                    yield f"data: {json.dumps({'type': 'error', 'message': f'获取数据量失败: {error_msg}'})}\n\n"
                    return
                
                total_available = count_result['total']
                
                if total_available == 0:
                    yield f"data: {json.dumps({'type': 'complete', 'total_processed': 0, 'message': '没有找到需要分析的数据'})}\n\n"
                    return
                
                yield f"data: {json.dumps({'type': 'log', 'message': f'找到 {total_available} 条数据需要分析'})}\n\n"
                
                # 查询所有符合条件的数据（不设置数量限制）
                data_result = sentiment_db.get_data(
                    fields=["*"],
                    filters=filters,
                    page=1,
                    page_size=total_available  # 使用实际的数据总量
                )
                
                if not data_result['success']:
                    error_msg = data_result.get('message', '未知错误')
                    yield f"data: {json.dumps({'type': 'error', 'message': f'获取数据失败: {error_msg}'})}\n\n"
                    return
                
                source_data = data_result['data']
                total_items = len(source_data)
                
                processed = 0
                success_count = 0
                failed_count = 0
                
                # 收集所有数据用于批量重复检测
                all_data_items = []
                
                # 处理每条数据
                for i, data_item in enumerate(source_data):
                    try:
                        processed += 1
                        processing_start_time = time.time()  # 记录处理开始时间
                        progress = (processed / total_items) * 100
                        
                        yield f"data: {json.dumps({'type': 'progress', 'current': processed, 'total': total_items, 'percentage': progress})}\n\n"
                        
                        # 提取文本内容
                        content_text = data_item.get('content', '') or data_item.get('title', '')
                        if not content_text:
                            yield f"data: {json.dumps({'type': 'log', 'message': f'第 {processed} 条数据内容为空，跳过'})}\n\n"
                            failed_count += 1
                            continue
                        
                        content_preview = content_text[:50] + "..." if len(content_text) > 50 else content_text
                        yield f"data: {json.dumps({'type': 'log', 'message': f'正在分析第 {processed} 条数据: {content_preview}'})}\n\n"
                        
                        # 生成原始ID (使用序号)
                        original_id = processed
                        
                        # 创建分析任务
                        analysis_tasks = []
                        if enable_sentiment:
                            analysis_tasks.append(sentiment_agent.analyze_sentiment(content_text))
                        if enable_tags:
                            analysis_tasks.append(tag_agents.analyze_tags(content_text))
                        if enable_companies:
                            analysis_tasks.append(company_agent.analyze_companies(content_text))
                        
                        # 并行执行所有分析任务
                        analysis_results = await asyncio.gather(*analysis_tasks, return_exceptions=True)
                        
                        # 解析分析结果
                        sentiment_result = None
                        tag_results = []
                        company_results = []
                        
                        result_index = 0
                        if enable_sentiment:
                            sentiment_result = analysis_results[result_index] if not isinstance(analysis_results[result_index], Exception) else None
                            result_index += 1
                        if enable_tags:
                            tag_results = analysis_results[result_index] if not isinstance(analysis_results[result_index], Exception) else []
                            result_index += 1
                        if enable_companies:
                            company_results = analysis_results[result_index] if not isinstance(analysis_results[result_index], Exception) else []
                        
                        # 构建标签结果字典
                        tag_results_dict = {}
                        if tag_results:
                            for tag_result in tag_results:
                                tag_results_dict[tag_result.tag] = {
                                    'belongs': tag_result.belongs,
                                    'reason': tag_result.reason
                                }
                        
                        # 生成内容摘要 - 使用AI生成真正的摘要
                        try:
                            from ali_llm_client import AliLLMClient
                            llm_client = AliLLMClient()
                            summary = llm_client.generate_summary(content_text)
                            yield f"data: {json.dumps({'type': 'log', 'message': f'第 {processed} 条数据摘要生成完成'})}\n\n"
                        except Exception as e:
                            summary = content_text[:200] + "..." if len(content_text) > 200 else content_text
                            yield f"data: {json.dumps({'type': 'warning', 'message': f'第 {processed} 条数据摘要生成失败，使用截取摘要: {str(e)}'})}\n\n"
                        
                        # 准备数据用于重复检测
                        data_for_duplicate = {
                            'id': original_id,
                            'content': content_text,
                            'title': data_item.get('title', '无标题'),
                            'publish_time': data_item.get('publish_time', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
                        }
                        all_data_items.append(data_for_duplicate)
                        
                        # 暂时存储分析结果，等待重复检测
                        temp_save_data = {
                            'original_id': original_id,
                            'title': data_item.get('title', '无标题'),
                            'content': content_text,
                            'summary': summary,
                            'source': data_item.get('source', data_source),
                            'publish_time': data_item.get('publish_time', datetime.now().strftime('%Y-%m-%d %H:%M:%S')),
                            'sentiment_level': sentiment_result.level if sentiment_result else '未知',
                            'sentiment_reason': sentiment_result.reason if sentiment_result else '无原因',
                            'companies': ','.join([company.name for company in company_results]) if company_results else '',
                            'processing_time': round(time.time() - processing_start_time, 2),  # 处理时间（秒）
                            'tag_results': tag_results_dict
                        }
                        
                        # 将分析结果与数据项关联
                        data_for_duplicate['analysis_result'] = temp_save_data
                        
                        yield f"data: {json.dumps({'type': 'log', 'message': f'第 {processed} 条数据分析完成，等待重复检测...'})}\n\n"
                        
                    except Exception as e:
                        failed_count += 1
                        yield f"data: {json.dumps({'type': 'log', 'message': f'第 {processed} 条数据分析失败: {str(e)}'})}\n\n"
                        continue
                
                # 执行批量重复检测
                if all_data_items:
                    yield f"data: {json.dumps({'type': 'log', 'message': f'开始执行SimHash重复检测，共 {len(all_data_items)} 条数据...'})}\n\n"
                    
                    try:
                        # 执行重复检测
                        duplicated_results = duplicate_manager.detect_duplicates(all_data_items)
                        
                        yield f"data: {json.dumps({'type': 'log', 'message': '重复检测完成，开始保存到数据库...'})}\n\n"
                        
                        # 保存带有重复检测结果的数据
                        for result_item in duplicated_results:
                            try:
                                analysis_result = result_item['analysis_result']
                                
                                # 添加重复检测结果
                                save_data = {
                                    **analysis_result,
                                    'duplicate_id': result_item['duplicate_id'],
                                    'duplication_rate': result_item['duplication_rate'],
                                    'session_id': session_id,  # 添加会话ID
                                }
                                
                                # 保存到结果数据库
                                save_result = result_db.save_analysis_result(save_data)
                                
                                if save_result['success']:
                                    success_count += 1
                                elif save_result.get('duplicate', False):
                                    # 跳过重复记录，不算作失败
                                    item_id = result_item['id']
                                    yield f"data: {json.dumps({'type': 'log', 'message': f'ID {item_id} 已存在，跳过重复保存'})}\n\n"
                                else:
                                    save_error = save_result.get('message', '未知错误')
                                    failed_count += 1
                                    item_id = result_item['id']
                                    yield f"data: {json.dumps({'type': 'log', 'message': f'ID {item_id} 保存失败: {save_error}'})}\n\n"
                                    
                            except Exception as e:
                                failed_count += 1
                                item_id = result_item.get('id', '未知')
                                yield f"data: {json.dumps({'type': 'log', 'message': f'ID {item_id} 处理失败: {str(e)}'})}\n\n"
                        
                        # 输出重复检测统计
                        duplicate_count = sum(1 for item in duplicated_results if item['is_duplicate'])
                        yield f"data: {json.dumps({'type': 'log', 'message': f'重复检测完成！发现 {duplicate_count} 条重复文本'})}\n\n"
                        
                    except Exception as e:
                        yield f"data: {json.dumps({'type': 'error', 'message': f'重复检测失败: {str(e)}'})}\n\n"
                
                # 完成
                completion_msg = f'批量解析完成！总处理: {processed}, 成功: {success_count}, 失败: {failed_count}'
                yield f"data: {json.dumps({'type': 'complete', 'total_processed': processed, 'success_count': success_count, 'failed_count': failed_count, 'session_id': session_id, 'message': completion_msg})}\n\n"
                
                # 自动触发去重和导出流程
                if success_count > 0:
                    yield f"data: {json.dumps({'type': 'log', 'message': '开始自动去重和导出流程...'})}\n\n"
                    
                    try:
                        # 执行自动去重
                        yield f"data: {json.dumps({'type': 'log', 'message': '正在执行数据库去重...'})}\n\n"
                        
                        # 调用去重模块
                        from deduplicate_any_json import deduplicate_database_records
                        dedup_result = deduplicate_database_records()
                        
                        if dedup_result['success']:
                            yield f"data: {json.dumps({'type': 'log', 'message': f'去重完成！删除重复记录: {dedup_result["duplicates_removed"]}'})}\n\n"
                            
                            # 执行自动导出
                            yield f"data: {json.dumps({'type': 'log', 'message': '正在执行自动导出...'})}\n\n"
                            
                            from deduplicate_any_json import auto_export_after_dedup
                            export_result = auto_export_after_dedup()
                            
                            if export_result['success']:
                                yield f"data: {json.dumps({'type': 'log', 'message': f'自动导出完成！文件: {export_result["export_file"]}'})}\n\n"
                            else:
                                yield f"data: {json.dumps({'type': 'warning', 'message': f'自动导出失败: {export_result["message"]}'})}\n\n"
                        else:
                            yield f"data: {json.dumps({'type': 'warning', 'message': f'去重失败: {dedup_result["message"]}'})}\n\n"
                            
                    except Exception as e:
                        yield f"data: {json.dumps({'type': 'warning', 'message': f'自动去重导出过程中发生错误: {str(e)}'})}\n\n"
                
            except Exception as e:
                yield f"data: {json.dumps({'type': 'error', 'message': f'批量解析过程中发生错误: {str(e)}'})}\n\n"
        
        return StreamingResponse(
            generate_stream(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"
            }
        )
        
    except Exception as e:
        logger.error(f"批量解析失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"批量解析失败: {str(e)}")

@app.get("/api/analysis_results")
async def get_analysis_results(
    search: Optional[str] = Query(None, description="搜索关键词"),
    data_source: Optional[str] = Query(None, description="数据源"),
    sentiment: Optional[str] = Query(None, description="情感等级"),
    tags: Optional[str] = Query(None, description="风险标签"),
    date_range: Optional[str] = Query(None, description="时间范围"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(10, ge=1, le=100, description="每页大小")
):
    """获取分析结果数据"""
    try:
        from result_database_new import ResultDatabase
        
        # 直接使用结果数据库 - 修复数据库路径
        result_db = ResultDatabase('data/analysis_results.db')
        
        # 获取分析结果，支持搜索
        result = result_db.get_analysis_results(
            page=page, 
            page_size=page_size,
            search_keyword=search
        )
        
        logger.info(f"数据库查询结果 - success: {result.get('success')}, total: {result.get('total')}")
        
        if result['success']:
            # ResultDatabase已经返回了正确格式的数据，直接返回
            # 确保返回JSONResponse以正确设置Content-Type和编码
            from fastapi.responses import JSONResponse
            return JSONResponse(
                content=result,
                media_type="application/json; charset=utf-8"
            )
        else:
            return {
                "success": False,
                "error": result.get('message', '查询失败'),
                "data": [],
                "total": 0,
                "page": page,
                "page_size": page_size,
                "total_pages": 0
            }
        
    except Exception as e:
        logger.error(f"获取分析结果失败: {str(e)}")
        return {
            "success": False,
            "error": f"获取分析结果失败: {str(e)}",
            "data": [],
            "total": 0,
            "page": page,
            "page_size": page_size,
            "total_pages": 0
        }

@app.get("/api/duplicates/statistics")
async def get_duplicate_statistics():
    """获取去重统计信息"""
    # 这里可以连接到数据库或文件系统来获取真实的统计信息
    # 目前返回模拟数据
    return {
        "total_texts": 0,
        "unique_texts": 0,
        "duplicate_texts": 0,
        "duplication_rate": 0.0
    }

@app.post("/api/export/enhanced")
async def enhanced_export(
    export_format: str = Form("json", description="导出格式 (json/csv/excel)"),
    include_metadata: bool = Form(True, description="是否包含元数据"),
    filter_tags: Optional[str] = Form(None, description="过滤标签，逗号分隔")
):
    """增强数据导出接口"""
    try:
        from deduplicate_any_json import enhanced_export_data
        
        # 处理标签过滤
        tags_list = None
        if filter_tags:
            tags_list = [tag.strip() for tag in filter_tags.split(',') if tag.strip()]
        
        # 执行增强导出
        export_result = enhanced_export_data(
            export_format=export_format,
            include_metadata=include_metadata,
            filter_tags=tags_list
        )
        
        if export_result['success']:
            return {
                "success": True,
                "message": export_result['message'],
                "export_file": export_result['export_file'],
                "total_records": export_result['total_records'],
                "format": export_result['format']
            }
        else:
            raise HTTPException(status_code=400, detail=export_result['message'])
            
    except Exception as e:
        logger.error(f"增强导出失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"增强导出失败: {str(e)}")

@app.get("/api/config")
async def get_config():
    """获取当前配置（仅返回非敏感项和API Key掩码）"""
    masked_key = None
    if Config.ALI_API_KEY:
        # 显示后4位
        masked_key = ("*" * max(0, len(Config.ALI_API_KEY) - 4)) + Config.ALI_API_KEY[-4:]
    return {
        "ALI_MODEL_NAME": Config.ALI_MODEL_NAME,
        "ALI_BASE_URL": Config.ALI_BASE_URL,
        "ALI_API_KEY_MASKED": masked_key,
        "HOST": Config.HOST,
        "PORT": Config.PORT,
        "DEBUG": Config.DEBUG,
        "MAX_CONTENT_LENGTH": Config.MAX_CONTENT_LENGTH,
        "BATCH_SIZE": Config.BATCH_SIZE,
        "TAG_PROMPT_TEMPLATE": Config.TAG_PROMPT_TEMPLATE,
        "AGENT_PROMPTS": Config.AGENT_PROMPTS,
    }

@app.post("/api/config")
async def update_config(payload: dict):
    """更新运行时配置（进程内，仅当次生效）。建议持久化到.env手动管理。"""
    # 允许更新的字段
    updatable_fields = {
        "ALI_API_KEY": str,
        "ALI_MODEL_NAME": str,
        "ALI_BASE_URL": str,
        "HOST": str,
        "PORT": int,
        "DEBUG": bool,
        "MAX_CONTENT_LENGTH": int,
        "BATCH_SIZE": int,
        "TAG_PROMPT_TEMPLATE": str,
    }
    updated = {}
    for key, caster in updatable_fields.items():
        if key in payload and payload[key] is not None:
            try:
                value = payload[key]
                # 手动处理bool/int等
                if caster is bool and isinstance(value, str):
                    value = value.lower() == "true"
                elif caster is int and isinstance(value, str):
                    value = int(value)
                setattr(Config, key, value)
                updated[key] = value if key != "ALI_API_KEY" else "UPDATED"
            except Exception as e:
                return JSONResponse(status_code=400, content={"detail": f"配置项 {key} 无效: {e}"})

    # 特殊处理AGENT_PROMPTS
    if "AGENT_PROMPTS" in payload and payload["AGENT_PROMPTS"] is not None:
        try:
            agent_prompts = payload["AGENT_PROMPTS"]
            if isinstance(agent_prompts, dict):
                # 更新Config中的AGENT_PROMPTS
                Config.AGENT_PROMPTS.update(agent_prompts)

                # 更新所有相关Agent的提示词
                for tag_name, prompt in agent_prompts.items():
                    if hasattr(tag_agents, 'update_agent_prompt'):
                        tag_agents.update_agent_prompt(tag_name, prompt)

                    # 单独处理情感分析Agent的提示词更新
                    if tag_name == "情感分析":
                        sentiment_agent.prompt_template = prompt or Config.SENTIMENT_PROMPT_TEMPLATE

                updated["AGENT_PROMPTS"] = "UPDATED"
            else:
                return JSONResponse(status_code=400, content={"detail": "AGENT_PROMPTS必须是字典格式"})
        except Exception as e:
            return JSONResponse(status_code=400, content={"detail": f"AGENT_PROMPTS更新失败: {e}"})

    # 同步到相关运行实例（例如AliLLMClient），此处仅在下次实例化生效；
    # 如需立刻生效，可考虑重新创建相关客户端实例。
    return {"message": "配置已更新（进程内）", "updated": updated}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000) 