"""
舆情分析系统主应用 - Linux生产环境版本
基于FastAPI构建的Web API服务
适配GCP虚拟机部署
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
import os
import logging
from datetime import datetime

# 导入配置 - 使用Linux版本配置
from config_linux import Config

# 导入模型和其他模块
from models import AnalysisRequest, CompanyInfo, TagResult, SentimentResult
from api_key_manager import api_key_manager, ensure_api_key_configured
from agents.company_agent import CompanyAgent
from agents.tag_agents import TagAgents
from agents.sentiment_agent import SentimentAgent
from fastapi.responses import StreamingResponse
from database_api import router as database_router
import pandas as pd
from database_config_api import router as database_config_router
from analysis_api import router as analysis_router
from data_api import router as data_router
from results_api import router as results_router
from api_config_routes import router as api_config_router
from chat_api import router as chat_router
import asyncio
import json

# 配置日志
logging.basicConfig(
    level=getattr(logging, Config.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(Config.LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="多Agent情感分析系统",
    description="专门处理企业识别、标签分类和情感等级分类",
    version="1.0.0"
)

# 初始化各个agent
company_agent = CompanyAgent()  # 企业识别模块
tag_agents = TagAgents()
sentiment_agent = SentimentAgent()

# 设置模板和静态文件
templates = Jinja2Templates(directory="templates")

# 自定义静态文件处理，添加防缓存头部
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

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
app.include_router(api_config_router)
app.include_router(chat_router)

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
    try:
        # 检查API密钥配置
        api_key = Config.get_ali_api_key()
        api_status = "configured" if api_key else "not_configured"
        
        # 检查数据库连接
        db_status = "connected"
        try:
            from database_manager import UnifiedDatabaseManager
            db_manager = UnifiedDatabaseManager()
            db_status = "connected"
        except Exception as e:
            db_status = f"error: {str(e)}"
        
        return {
            "status": "healthy",
            "message": "多Agent情感分析系统运行正常",
            "timestamp": datetime.now().isoformat(),
            "api_key_status": api_status,
            "database_status": db_status,
            "version": "1.0.0"
        }
    except Exception as e:
        logger.error(f"健康检查失败: {str(e)}")
        return {
            "status": "unhealthy",
            "message": f"系统异常: {str(e)}",
            "timestamp": datetime.now().isoformat()
        }

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
        logger.error(f"CSV文件处理失败: {str(e)}")
        return {"detail": f"处理CSV文件失败: {str(e)}"}

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
        result_db = ResultDatabase('/var/www/sentiment-analysis/data/analysis_results.db')
        
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

@app.get("/api/config")
async def get_config():
    """获取当前配置（仅返回非敏感项和API Key掩码）"""
    masked_key = None
    api_key = Config.get_ali_api_key()
    if api_key:
        # 显示后4位
        masked_key = ("*" * max(0, len(api_key) - 4)) + api_key[-4:]
    return {
        "ALI_MODEL_NAME": Config.ALI_MODEL_NAME,
        "ALI_BASE_URL": Config.ALI_BASE_URL,
        "ALI_API_KEY_MASKED": masked_key,
        "HOST": Config.HOST,
        "PORT": Config.PORT,
        "DEBUG": Config.DEBUG,
        "MAX_CONTENT_LENGTH": Config.MAX_CONTENT_LENGTH,
        "BATCH_SIZE": Config.BATCH_SIZE,
        "LOG_LEVEL": Config.LOG_LEVEL,
        "LOG_FILE": Config.LOG_FILE,
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
        "LOG_LEVEL": str,
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

def setup_api_key():
    """在启动时检查API密钥配置"""
    logger.info("检查API密钥配置...")
    
    api_key = Config.get_ali_api_key()
    if not api_key or api_key == "your_api_key_here":
        logger.warning("API密钥未配置，请在.env文件中设置DASHSCOPE_API_KEY")
        logger.info("系统将以受限模式运行")
    else:
        logger.info("API密钥配置正常")

if __name__ == "__main__":
    # 启动时检查API密钥
    setup_api_key()
    
    logger.info("情感分析系统启动中...")
    logger.info(f"服务地址: http://{Config.HOST}:{Config.PORT}")
    logger.info(f"日志级别: {Config.LOG_LEVEL}")
    logger.info(f"调试模式: {Config.DEBUG}")
    
    # 使用uvicorn启动
    uvicorn.run(
        app, 
        host=Config.HOST, 
        port=Config.PORT,
        log_level=Config.LOG_LEVEL.lower(),
        access_log=True
    )


