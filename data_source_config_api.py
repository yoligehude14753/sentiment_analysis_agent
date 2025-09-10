"""
数据源配置API路由
提供API数据源和文件上传的配置接口
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Depends
from fastapi.responses import JSONResponse
from typing import Optional, Dict, Any, List
import json
import tempfile
import os
import logging

from unified_data_source_manager import UnifiedDataSourceManager, QueryParams
from api_data_source_manager import APIConfig

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/data-source", tags=["数据源配置"])

# 全局数据源管理器实例
data_source_manager = UnifiedDataSourceManager()

@router.get("/status")
async def get_data_source_status():
    """获取当前数据源状态"""
    try:
        source_info = data_source_manager.get_current_source_info()
        return {
            "success": True,
            "data": source_info
        }
    except Exception as e:
        logger.error(f"获取数据源状态失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取数据源状态失败: {str(e)}")

@router.post("/api/configure")
async def configure_api_source(request: Dict[str, Any]):
    """配置API数据源"""
    try:
        # 验证必需字段
        if 'url' not in request:
            raise HTTPException(status_code=400, detail="缺少API URL")
        
        # 配置API数据源
        result = await data_source_manager.configure_api_source(request)
        
        if result['success']:
            return JSONResponse(
                status_code=200,
                content=result
            )
        else:
            raise HTTPException(status_code=400, detail=result['message'])
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"配置API数据源失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"配置API数据源失败: {str(e)}")

@router.post("/api/test")
async def test_api_connection(request: Dict[str, Any]):
    """测试API连接"""
    try:
        # 临时配置API进行测试
        temp_manager = UnifiedDataSourceManager()
        result = await temp_manager.configure_api_source(request)
        
        return JSONResponse(
            status_code=200,
            content=result
        )
        
    except Exception as e:
        logger.error(f"测试API连接失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"测试API连接失败: {str(e)}")

@router.post("/file/upload")
async def upload_data_file(
    file: UploadFile = File(...),
    field_mapping: Optional[str] = Form(None),
    encoding: str = Form("utf-8")
):
    """上传数据文件"""
    try:
        # 验证文件类型
        file_extension = file.filename.split('.')[-1].lower()
        if file_extension not in ['csv', 'json']:
            raise HTTPException(status_code=400, detail="只支持CSV和JSON文件")
        
        # 检查文件大小（10MB限制）
        file_content = await file.read()
        if len(file_content) > 10 * 1024 * 1024:  # 10MB
            raise HTTPException(status_code=400, detail="文件大小不能超过10MB")
        
        # 保存临时文件
        with tempfile.NamedTemporaryFile(delete=False, suffix=f'.{file_extension}') as temp_file:
            temp_file.write(file_content)
            temp_file_path = temp_file.name
        
        try:
            # 解析字段映射
            mapping_dict = None
            if field_mapping:
                try:
                    mapping_dict = json.loads(field_mapping)
                except json.JSONDecodeError:
                    raise HTTPException(status_code=400, detail="字段映射格式错误")
            
            # 配置文件数据源
            result = data_source_manager.configure_file_source(
                file_path=temp_file_path,
                file_type=file_extension,
                field_mapping=mapping_dict,
                encoding=encoding
            )
            
            if result['success']:
                return JSONResponse(
                    status_code=200,
                    content=result
                )
            else:
                raise HTTPException(status_code=400, detail=result['message'])
                
        finally:
            # 清理临时文件
            try:
                os.unlink(temp_file_path)
            except:
                pass
                
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"上传文件失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"上传文件失败: {str(e)}")

@router.post("/switch")
async def switch_data_source(request: Dict[str, str]):
    """切换数据源类型"""
    try:
        source_type = request.get('source_type')
        if not source_type:
            raise HTTPException(status_code=400, detail="缺少数据源类型参数")
        
        result = data_source_manager.switch_source_type(source_type)
        
        if result['success']:
            return JSONResponse(
                status_code=200,
                content=result
            )
        else:
            raise HTTPException(status_code=400, detail=result['message'])
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"切换数据源失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"切换数据源失败: {str(e)}")

@router.delete("/file/clear")
async def clear_file_data():
    """清除文件数据"""
    try:
        data_source_manager.clear_file_data()
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": "文件数据已清除"
            }
        )
    except Exception as e:
        logger.error(f"清除文件数据失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"清除文件数据失败: {str(e)}")

@router.get("/fields/suggestions")
async def get_field_suggestions():
    """获取字段映射建议"""
    try:
        # 获取当前数据源的示例数据
        source_info = data_source_manager.get_current_source_info()
        
        if source_info['source_type'] == 'api' and source_info['status'] == 'configured':
            # 对于API，返回常见字段映射建议
            suggestions = {
                "content": ["text", "body", "message", "content", "description"],
                "title": ["title", "subject", "headline", "name"],
                "publish_time": ["publish_time", "created_at", "timestamp", "date", "time"],
                "source": ["source", "platform", "channel", "origin"]
            }
        elif source_info['source_type'] == 'file' and source_info['status'] == 'configured':
            # 对于文件，分析实际数据字段
            if data_source_manager.uploaded_data:
                sample_item = data_source_manager.uploaded_data[0]
                available_fields = list(sample_item.keys())
                suggestions = {
                    "content": [f for f in available_fields if any(keyword in f.lower() for keyword in ['content', 'text', 'body', 'message'])],
                    "title": [f for f in available_fields if any(keyword in f.lower() for keyword in ['title', 'subject', 'headline', 'name'])],
                    "publish_time": [f for f in available_fields if any(keyword in f.lower() for keyword in ['time', 'date', 'created', 'publish'])],
                    "source": [f for f in available_fields if any(keyword in f.lower() for keyword in ['source', 'platform', 'channel', 'origin'])]
                }
            else:
                suggestions = {}
        else:
            suggestions = {}
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "suggestions": suggestions
            }
        )
        
    except Exception as e:
        logger.error(f"获取字段建议失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取字段建议失败: {str(e)}")

# 依赖注入函数
def get_data_source_manager() -> UnifiedDataSourceManager:
    """获取数据源管理器实例"""
    return data_source_manager
