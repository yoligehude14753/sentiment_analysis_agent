"""
Chat API - 智能问答功能
基于搜索结果和知识库提供智能问答服务
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Dict, Optional, Any
import json
import logging
from agents.ali_llm_client import AliLLMClient
from database_manager import UnifiedDatabaseManager
from config import Config

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["智能问答"])

class ChatMessage(BaseModel):
    role: str  # 'user' or 'assistant'
    content: str
    timestamp: Optional[str] = None

class ChatRequest(BaseModel):
    message: str
    search_results: Optional[List[Dict[str, Any]]] = []
    knowledge_base_fields: Optional[List[str]] = []
    conversation_history: Optional[List[ChatMessage]] = []

class ChatResponse(BaseModel):
    success: bool
    response: Optional[str] = None
    error: Optional[str] = None
    context_used: Optional[int] = None

def get_db_manager():
    """获取数据库管理器实例"""
    return UnifiedDatabaseManager()

@router.post("/chat", response_model=ChatResponse)
async def chat_with_ai(
    request: ChatRequest,
    db_manager: UnifiedDatabaseManager = Depends(get_db_manager)
):
    """
    智能问答接口
    基于搜索结果和知识库回答用户问题
    """
    try:
        # 验证输入
        if not request.message or not request.message.strip():
            raise HTTPException(status_code=400, detail="问题不能为空")
        
        # 初始化LLM客户端，使用当前配置的模型
        llm_client = AliLLMClient()
        
        # 构建上下文信息
        context_info = _build_context(
            search_results=request.search_results or [],
            knowledge_base_fields=request.knowledge_base_fields or [],
            conversation_history=request.conversation_history or []
        )
        
        # 构建系统提示词
        system_prompt = _build_system_prompt(context_info)
        
        # 构建用户消息
        user_message = request.message.strip()
        
        # 调用LLM生成回答
        response = await llm_client.call_llm(
            system_prompt=system_prompt,
            user_message=user_message
        )
        
        if response.get("success"):
            return ChatResponse(
                success=True,
                response=response.get("response", "抱歉，没有获取到回答"),
                context_used=len(request.search_results or [])
            )
        else:
            error_msg = response.get("error", "调用AI服务失败")
            logger.error(f"LLM调用失败: {error_msg}")
            return ChatResponse(
                success=False,
                error=f"AI服务错误: {error_msg}"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        error_msg = f"智能问答服务出现错误: {str(e)}"
        logger.error(error_msg)
        return ChatResponse(
            success=False,
            error=error_msg
        )

def _build_context(
    search_results: List[Dict[str, Any]], 
    knowledge_base_fields: List[str],
    conversation_history: List[ChatMessage]
) -> Dict[str, Any]:
    """构建上下文信息"""
    
    # 处理搜索结果
    context_data = []
    if search_results:
        for i, result in enumerate(search_results[:10], 1):  # 限制最多10条结果
            item_data = {}
            
            # 根据选择的字段构建上下文
            if not knowledge_base_fields:
                # 如果没有指定字段，使用默认重要字段
                knowledge_base_fields = ['title', 'content', 'summary', 'sentiment_level', 'companies']
            
            for field in knowledge_base_fields:
                if field in result and result[field] is not None:
                    # 处理不同类型的字段值
                    value = result[field]
                    if isinstance(value, (list, dict)):
                        value = json.dumps(value, ensure_ascii=False)
                    elif isinstance(value, str) and len(value) > 500:
                        value = value[:500] + "..."
                    
                    item_data[field] = value
            
            if item_data:  # 只有当有数据时才添加
                context_data.append({
                    "序号": i,
                    **item_data
                })
    
    # 处理对话历史
    recent_history = []
    if conversation_history:
        # 只保留最近的5轮对话
        recent_conversations = conversation_history[-10:]  # 最多10条消息，即5轮对话
        for msg in recent_conversations:
            recent_history.append({
                "角色": "用户" if msg.role == "user" else "助手",
                "内容": msg.content
            })
    
    return {
        "search_results": context_data,
        "conversation_history": recent_history,
        "total_results": len(search_results),
        "fields_used": knowledge_base_fields
    }

def _build_system_prompt(context_info: Dict[str, Any]) -> str:
    """构建系统提示词"""
    
    system_prompt = """你是一个专业的情感分析和舆情监测AI助手，专门帮助用户分析和理解舆情数据。

你的能力包括：
1. 基于搜索结果回答用户关于舆情数据的问题
2. 分析情感倾向、风险等级、企业相关信息
3. 提供数据洞察和趋势分析
4. 解释分析结果和标签含义

回答要求：
- 基于提供的数据回答问题，不要编造信息
- 回答要专业、准确、有条理
- 如果数据不足以回答问题，请明确说明
- 使用中文回答
- 回答长度适中，重点突出

"""
    
    # 添加搜索结果上下文
    if context_info["search_results"]:
        system_prompt += f"\n当前搜索结果数据（共{context_info['total_results']}条，显示前10条）：\n"
        for item in context_info["search_results"]:
            system_prompt += f"\n【数据{item['序号']}】\n"
            for key, value in item.items():
                if key != "序号":
                    system_prompt += f"{key}: {value}\n"
        
        system_prompt += f"\n使用的字段: {', '.join(context_info['fields_used'])}\n"
    else:
        system_prompt += "\n注意：当前没有搜索结果数据，请提醒用户先进行数据搜索。\n"
    
    # 添加对话历史
    if context_info["conversation_history"]:
        system_prompt += "\n对话历史：\n"
        for msg in context_info["conversation_history"]:
            system_prompt += f"{msg['角色']}: {msg['内容']}\n"
    
    system_prompt += "\n请基于以上信息回答用户的问题。"
    
    return system_prompt

@router.get("/chat/status")
async def get_chat_status():
    """获取聊天服务状态"""
    try:
        # 检查LLM服务是否可用
        config = Config()
        llm_client = AliLLMClient()
        
        # 这里可以添加简单的健康检查
        return {
            "success": True,
            "status": "available",
            "message": "智能问答服务正常",
            "model": config.ALI_MODEL_NAME
        }
    except Exception as e:
        return {
            "success": False,
            "status": "unavailable", 
            "message": f"智能问答服务不可用: {str(e)}"
        }

@router.get("/chat/model-info")
async def get_model_info():
    """获取当前配置的模型信息"""
    try:
        config = Config()
        return {
            "success": True,
            "model_name": config.ALI_MODEL_NAME,
            "base_url": config.ALI_BASE_URL,
            "available_models": [
                {"value": "qwen-turbo", "label": "通义千问-Turbo (快速响应)"},
                {"value": "qwen-plus", "label": "通义千问-Plus (平衡性能)"},
                {"value": "qwen-max", "label": "通义千问-Max (最强性能)"},
                {"value": "qwen-max-longcontext", "label": "通义千问-Max-LongContext (长文本)"}
            ]
        }
    except Exception as e:
        logger.error(f"获取模型信息失败: {e}")
        return {
            "success": False,
            "error": f"获取模型信息失败: {str(e)}"
        } 