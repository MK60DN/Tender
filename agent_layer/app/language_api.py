from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from .language_signals import MODEL_VERSION, analyze_language

router = APIRouter(prefix="/language", tags=["language-signals"])


class LanguageAnalyzeRequest(BaseModel):
    text: str = Field(min_length=1, max_length=8000)
    response_time_ms: float | None = Field(default=None, ge=0, le=3_600_000)
    context: dict[str, Any] | None = None


@router.post("/analyze")
def language_analyze(request: LanguageAnalyzeRequest):
    try:
        return analyze_language(request.text, response_time_ms=request.response_time_ms, context=request.context)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/schema")
def language_schema():
    return {
        "model_version": MODEL_VERSION,
        "pipeline": [
            "原始话语",
            "脚本与语言识别",
            "证据片段抽取",
            "候选状态假设",
            "与行为、答题、时间、结果和历史融合",
            "最小行动",
            "结果回流与校准",
        ],
        "signal_types": [
            "显式情绪表达", "不确定性与低把握", "回避或行动阻力", "自我效能受威胁",
            "对他人心智状态的推断", "元认知校准偏差", "主动求助", "具体任务请求",
            "因果归因表达", "潜在安全风险词",
        ],
        "model_role": {
            "language_model": "结构化抽取候选信号并自然表达",
            "tender_model": "融合多源证据、保留不确定性和长期因果",
            "deterministic_guard": "高风险词、证据来源、置信度和禁止结论边界",
        },
        "not_supported": [
            "仅凭语言判断知识掌握度",
            "仅凭语言诊断抑郁、焦虑或其他疾病",
            "仅凭语言确定人格类型",
            "把用户此刻的话当成永久特征",
        ],
        "boundary": "语言检测是弱证据层。掌握度来自作答与任务结果，状态由多源证据共同更新，高风险信号进入人工保护流程。",
    }
