# -*- coding: utf-8 -*-
"""Tenant filesystem, encryption and blind-index primitives.

Isolation model:
- one physical SQLite database per tenant;
- one encryption key per tenant;
- sensitive text is encrypted before it reaches SQLite;
- blind indexes permit exact matching without storing plaintext;
- tenant directories are hardened on Windows when possible.
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import pathlib
import re
import secrets
import subprocess
import zlib

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

ROOT = pathlib.Path(__file__).resolve().parent.parent
TENANT_ROOT = pathlib.Path(os.getenv("TENDER_TENANT_DATA_DIR", str(ROOT / "tenant_data"))).resolve()
_TENANT_RE = re.compile(r"^[a-z0-9][a-z0-9_-]{1,63}$")


def validate_tenant_id(tenant_id: str) -> str:
    value = (tenant_id or "").strip().lower()
    if not _TENANT_RE.fullmatch(value):
        raise ValueError("tenant_id must match ^[a-z0-9][a-z0-9_-]{1,63}$")
    return value


def tenant_dir(tenant_id: str, create: bool = False) -> pathlib.Path:
    value = validate_tenant_id(tenant_id)
    root = TENANT_ROOT.resolve()
    candidate = (root / value).resolve()
    if candidate.parent != root:
        raise ValueError("tenant path escapes tenant root")
    if create:
        candidate.mkdir(parents=True, exist_ok=True)
        harden_path(candidate)
    return candidate


def tenant_db_path(tenant_id: str) -> pathlib.Path:
    return tenant_dir(tenant_id) / "tender_tenant.db"


def _key_path(tenant_id: str) -> pathlib.Path:
    return tenant_dir(tenant_id, create=True) / ".tenant_key"


def tenant_key(tenant_id: str) -> bytes:
    path = _key_path(tenant_id)
    if path.exists():
        raw = path.read_bytes().strip()
        key = base64.urlsafe_b64decode(raw + b"=" * (-len(raw) % 4))
        if len(key) != 32:
            raise ValueError("invalid tenant key length")
        return key
    key = secrets.token_bytes(32)
    path.write_bytes(base64.urlsafe_b64encode(key))
    try:
        os.chmod(path, 0o600)
    except OSError:
        pass
    return key


def harden_path(path: pathlib.Path) -> None:
    """Remove inherited ACLs on Windows and grant the current service account only."""
    if os.name != "nt" or not path.exists():
        return
    user = os.environ.get("USERNAME", "").strip()
    if not user:
        return
    domain = os.environ.get("USERDOMAIN", "").strip()
    principal = f"{domain}\\{user}" if domain else user
    flags = "(OI)(CI)F" if path.is_dir() else "(F)"
    try:
        subprocess.run(
            ["icacls", str(path), "/inheritance:r", "/grant:r", f"{principal}:{flags}", f"SYSTEM:{flags}"],
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=15,
        )
    except (OSError, subprocess.SubprocessError):
        pass


def normalize_index_value(value: str) -> str:
    return re.sub(r"\s+", "", str(value or "")).strip().lower()


class TenantCipher:
    """AES-GCM for sensitive fields plus HMAC blind indexes."""

    def __init__(self, tenant_id: str):
        self.tenant_id = validate_tenant_id(tenant_id)
        self._key = tenant_key(self.tenant_id)
        self._aead = AESGCM(self._key)

    def encrypt_text(self, value: str) -> str:
        plain = (value or "").encode("utf-8")
        nonce = secrets.token_bytes(12)
        sealed = self._aead.encrypt(nonce, plain, self.tenant_id.encode("utf-8"))
        return "v1:" + base64.urlsafe_b64encode(nonce + sealed).decode("ascii")

    def decrypt_text(self, value: str | None) -> str:
        if not value:
            return ""
        if not value.startswith("v1:"):
            raise ValueError("unsupported ciphertext version")
        raw = base64.urlsafe_b64decode(value[3:] + "=" * (-len(value[3:]) % 4))
        nonce, sealed = raw[:12], raw[12:]
        return self._aead.decrypt(nonce, sealed, self.tenant_id.encode("utf-8")).decode("utf-8")

    def encrypt_json(self, value) -> str:
        return self.encrypt_text(json.dumps(value, ensure_ascii=False, separators=(",", ":")))

    def decrypt_json(self, value: str | None):
        text = self.decrypt_text(value)
        return json.loads(text) if text else None

    def encrypt_bytes(self, value: bytes, compress: bool = True) -> bytes:
        plain = zlib.compress(value, level=6) if compress else value
        nonce = secrets.token_bytes(12)
        sealed = self._aead.encrypt(nonce, plain, self.tenant_id.encode("utf-8"))
        return b"v1" + nonce + sealed

    def decrypt_bytes(self, value: bytes | None, decompress: bool = True) -> bytes:
        if not value:
            return b""
        if not value.startswith(b"v1"):
            raise ValueError("unsupported binary ciphertext version")
        plain = self._aead.decrypt(value[2:14], value[14:], self.tenant_id.encode("utf-8"))
        return zlib.decompress(plain) if decompress else plain

    def blind_index(self, value: str, namespace: str = "default") -> str:
        material = f"{namespace}:{normalize_index_value(value)}".encode("utf-8")
        return hmac.new(self._key, material, hashlib.sha256).hexdigest()


def sha256_file(path: pathlib.Path, chunk_size: int = 4 * 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            chunk = handle.read(chunk_size)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()