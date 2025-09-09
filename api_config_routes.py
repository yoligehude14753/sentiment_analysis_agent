"""
API密钥配置路由
提供Web界面的API密钥管理功能
"""

from fastapi import APIRouter, HTTPException, Form, Request
from fastapi.responses import JSONResponse
from api_key_manager import api_key_manager
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/config", tags=["API配置"])

@router.post("/save-api-key")
async def save_api_key(
    api_key: str = Form(...),
    provider: str = Form(default="dashscope")
):
    """保存API密钥"""
    try:
        # 验证API密钥格式
        is_valid, message = api_key_manager.validate_api_key(api_key, provider)
        if not is_valid:
            return JSONResponse(
                status_code=400,
                content={"success": False, "message": message}
            )
        
        # 保存API密钥
        api_key_manager.save_api_key(api_key, provider)
        
        logger.info(f"API密钥已保存 - Provider: {provider}")
        
        return JSONResponse(content={
            "success": True,
            "message": "API密钥保存成功！"
        })
        
    except Exception as e:
        logger.error(f"保存API密钥失败: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": f"保存失败: {str(e)}"}
        )

@router.get("/api-key-status")
async def get_api_key_status(provider: str = "dashscope"):
    """获取API密钥状态"""
    try:
        status = api_key_manager.get_key_status(provider)
        return JSONResponse(content={
            "success": True,
            "data": status
        })
    except Exception as e:
        logger.error(f"获取API密钥状态失败: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": f"获取状态失败: {str(e)}"}
        )

@router.post("/test-api-key")
async def test_api_key(provider: str = Form(default="dashscope")):
    """测试API密钥是否有效"""
    try:
        api_key = api_key_manager.get_api_key(provider)
        if not api_key:
            return JSONResponse(
                status_code=400,
                content={"success": False, "message": "未找到API密钥"}
            )
        
        # 这里可以添加实际的API测试逻辑
        # 例如调用一个简单的API接口验证密钥是否有效
        
        # 暂时只做格式验证
        is_valid, message = api_key_manager.validate_api_key(api_key, provider)
        
        return JSONResponse(content={
            "success": is_valid,
            "message": "API密钥格式正确" if is_valid else message
        })
        
    except Exception as e:
        logger.error(f"测试API密钥失败: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": f"测试失败: {str(e)}"}
        )

@router.delete("/api-key")
async def delete_api_key(provider: str = "dashscope"):
    """删除API密钥"""
    try:
        success = api_key_manager.remove_api_key(provider)
        
        if success:
            logger.info(f"API密钥已删除 - Provider: {provider}")
            return JSONResponse(content={
                "success": True,
                "message": "API密钥删除成功！"
            })
        else:
            return JSONResponse(
                status_code=404,
                content={"success": False, "message": "未找到API密钥"}
            )
            
    except Exception as e:
        logger.error(f"删除API密钥失败: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": f"删除失败: {str(e)}"}
        ) 