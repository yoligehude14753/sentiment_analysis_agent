#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import List
from pydantic import BaseModel

class AnalysisRequest(BaseModel):
    content: str

class AnalyzeRequest(BaseModel):
    content: str

class CompanyInfo(BaseModel):
    name: str
    credit_code: str
    reason: str

class CompanyName(BaseModel):
    """简化的企业名称模型，只包含企业名称"""
    name: str

class TagResult(BaseModel):
    tag: str
    belongs: bool
    reason: str

class SentimentResult(BaseModel):
    level: str
    reason: str

class AnalysisResponse(BaseModel):
    companies: List[CompanyInfo]
    tags: List[TagResult]
    sentiment: SentimentResult 