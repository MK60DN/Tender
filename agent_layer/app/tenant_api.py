# -*- coding: utf-8 -*-
"""Tenant-scoped API. Database selection comes only from a signed tenant session."""
from __future__ import annotations

import os
import re
import sqlite3
from typing import Any

from fastapi import APIRouter, HTTPException, Query, Request
from pydantic import BaseModel

from .auth import create_session
from .tenant_store import (
    TenantMember,
    list_files,
    list_leads,
    list_projected_students,
    list_students,
    get_student,
    resolve_tenant_member,
    projection_stats,
    search_files,
    tenant_context,
    tenant_stats,
    write_tenant_audit,
)

router = APIRouter(prefix="/tenant")


class TenantSessionRequest(BaseModel):
    tenant_id: str
    actor_id: str


def _member(request: Request) -> TenantMember:
    principal = getattr(request.state, "principal", None)
    if principal is None:
        raise HTTPException(status_code=401, detail="identity_required")
    tenant_id = getattr(principal, "tenant_id", None)
    if not tenant_id:
        raise HTTPException(status_code=403, detail="tenant_session_required")
    try:
        return resolve_tenant_member(tenant_id, principal.actor_id)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="tenant_not_found") from None
    except PermissionError:
        raise HTTPException(status_code=403, detail="tenant_membership_required") from None


@router.post("/demo-session")
def tenant_demo_session(payload: TenantSessionRequest):
    if os.getenv("TENDER_DEMO_MODE", "1") != "1":
        raise HTTPException(status_code=404, detail="demo_session_disabled")
    try:
        member = resolve_tenant_member(payload.tenant_id, payload.actor_id)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="tenant_not_found") from None
    except PermissionError:
        raise HTTPException(status_code=403, detail="tenant_membership_required") from None
    session = create_session(member.actor_id, member.role, tenant_id=member.tenant_id)
    write_tenant_audit(member.tenant_id, member.actor_id, "tenant.session.create", member.membership_id, {
        "role": member.role,
    })
    session["tenant_id"] = member.tenant_id
    return session


@router.get("/context")
def get_tenant_context(request: Request):
    member = _member(request)
    return {
        "tenant": tenant_context(member.tenant_id),
        "membership": {
            "membership_id": member.membership_id,
            "actor_id": member.actor_id,
            "role": member.role,
            "campus_ids": list(member.campus_ids),
            "class_ids": list(member.class_ids),
            "student_ids": list(member.student_ids),
            "permissions": sorted(member.permissions),
            "can_write": member.can_write,
            "can_read_sensitive": member.can_read_sensitive,
        },
    }


@router.get("/stats")
def get_tenant_stats(request: Request):
    return tenant_stats(_member(request))


@router.get("/students")
def get_students(
    request: Request,
    campus_id: str | None = None,
    class_id: str | None = None,
    query: str | None = None,
    limit: int = Query(200, ge=1, le=1000),
):
    member = _member(request)
    return {"students": list_students(member, campus_id=campus_id, class_id=class_id, query=query, limit=limit)}


@router.get("/students/{student_id}")
def get_one_student(request: Request, student_id: str):
    member = _member(request)
    try:
        return get_student(member, student_id)
    except PermissionError:
        raise HTTPException(status_code=403, detail="student_access_denied") from None


@router.get("/leads")
def get_leads(
    request: Request,
    campus_id: str | None = None,
    limit: int = Query(200, ge=1, le=1000),
):
    member = _member(request)
    try:
        rows = list_leads(member, campus_id=campus_id, limit=limit)
    except PermissionError:
        raise HTTPException(status_code=403, detail="sensitive_people_access_denied") from None
    write_tenant_audit(member.tenant_id, member.actor_id, "tenant.leads.list", campus_id, {"count": len(rows)})
    return {"leads": rows}


@router.get("/projections/students")
def get_projected_students(
    request: Request,
    year: int = Query(2026, ge=2000, le=2100),
    stage: str | None = None,
    review_status: str | None = None,
    campus_id: str | None = None,
    limit: int = Query(500, ge=1, le=2000),
):
    member = _member(request)
    try:
        rows = list_projected_students(
            member, year=year, stage=stage, review_status=review_status,
            campus_id=campus_id, limit=limit,
        )
    except PermissionError:
        raise HTTPException(status_code=403, detail="sensitive_people_access_denied") from None
    write_tenant_audit(member.tenant_id, member.actor_id, "tenant.projections.read", str(year), {
        "count": len(rows), "stage": stage, "review_status": review_status,
    })
    return {
        "year": year,
        "synthetic": True,
        "notice": "推算数据仅供招生规划和数据核验，不得直接作为已确认学生事实使用。",
        "students": rows,
    }


@router.get("/projections/stats")
def get_projection_stats(request: Request, year: int = Query(2026, ge=2000, le=2100)):
    member = _member(request)
    try:
        return projection_stats(member, year=year)
    except PermissionError:
        raise HTTPException(status_code=403, detail="sensitive_people_access_denied") from None


@router.get("/files")
def get_files(
    request: Request,
    classification: str | None = None,
    campus_id: str | None = None,
    limit: int = Query(200, ge=1, le=1000),
):
    member = _member(request)
    return {"files": list_files(member, classification=classification, campus_id=campus_id, limit=limit)}


@router.get("/search")
def search_tenant(
    request: Request,
    q: str = Query(..., min_length=2, max_length=200),
    limit: int = Query(50, ge=1, le=200),
):
    member = _member(request)
    try:
        rows = search_files(member, q, limit=limit)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from None
    except sqlite3.OperationalError:
        # FTS syntax can be strict for raw user input; retry with tokenized terms.
        tokens = re.findall(r"[\w\u4e00-\u9fff]+", q)
        if not tokens:
            return {"query": q, "results": []}
        rows = search_files(member, " AND ".join(tokens), limit=limit)
    return {"query": q, "results": rows}
