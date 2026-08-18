"""Electronic signature of a certificate (interface + basic implementation).

A valid signature binds **identity** (the signer, re-authenticated in the
view), **meaning/intent** (what the signer declares) and a **hash** of the
canonical content. This module defines the :class:`SignatureProvider` protocol
and a :class:`BasicSignatureProvider` (SHA-256 of the canonical JSON).

Re-authentication (credential check) happens in the ``sign`` view, not here. An
advanced signature (e.g. PKI / X.509) would implement the same interface
without changing its consumers.
"""
from __future__ import annotations

import hashlib
import json
from typing import Any, Dict, Protocol


class SignatureResult:
    """Result of a signature: content hash + recorded meaning.\n
    :ivar hash: hex SHA-256 hash of the signed canonical content.\n
    :ivar meaning: meaning/intent declared by the signer.\n
    :ivar algorithm: hash algorithm used (``sha256``).\n
    """

    def __init__(self, hash: str, meaning: str, algorithm: str = "sha256") -> None:
        """Initialize the signature result.\n
        :param hash: hex hash of the canonical content.\n
        :param meaning: meaning/intent of the signature.\n
        :param algorithm: hash algorithm used.\n
        """
        self.hash = hash
        self.meaning = meaning
        self.algorithm = algorithm


class SignatureProvider(Protocol):
    """Interface of a certificate signature provider."""

    def canonical_content(self, payload: Dict[str, Any]) -> str:
        """Serialize the content to sign deterministically.\n
        :param payload: content bound by the signature.\n
        :returns: canonical string ready to hash.\n
        """
        ...

    def compute_hash(self, payload: Dict[str, Any]) -> str:
        """Compute the hash of the canonical content.\n
        :param payload: content to hash.\n
        :returns: hex hash of the canonical content.\n
        """
        ...

    def sign(self, payload: Dict[str, Any], meaning: str) -> SignatureResult:
        """Sign the content, recording (external) identity, meaning and hash.\n
        :param payload: canonical content of the certificate.\n
        :param meaning: meaning/intent of the signature.\n
        :returns: signature result (hash + meaning).\n
        """
        ...


class BasicSignatureProvider:
    """Basic :class:`SignatureProvider` (hash + meaning).

    Records the meaning and binds the content by SHA-256 hash of the canonical
    JSON (sorted keys, fixed separators). Does NOT perform re-authentication
    (the view does) nor advanced cryptographic signing.
    """

    algorithm = "sha256"

    def canonical_content(self, payload: Dict[str, Any]) -> str:
        """Serialize ``payload`` to canonical (deterministic) JSON.\n
        :param payload: content of the certificate.\n
        :returns: JSON with sorted keys and fixed separators.\n
        """
        return json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
            default=str,
            ensure_ascii=False,
        )

    def compute_hash(self, payload: Dict[str, Any]) -> str:
        """Compute the hex SHA-256 of the canonical content of ``payload``.\n
        :param payload: content of the certificate.\n
        :returns: hex SHA-256 hash.\n
        """
        canonical = self.canonical_content(payload=payload)
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    def sign(self, payload: Dict[str, Any], meaning: str) -> SignatureResult:
        """Basic signature: meaning + hash of the canonical content.\n
        :param payload: canonical content of the certificate.\n
        :param meaning: meaning/intent declared by the signer.\n
        :returns: result with hash and meaning.\n
        :raises ValueError: if ``meaning`` is empty (a meaning is required).\n
        """
        if not (meaning or "").strip():
            raise ValueError(
                "La firma requiere un significado/intención explícito."
            )
        return SignatureResult(
            hash=self.compute_hash(payload=payload),
            meaning=meaning,
            algorithm=self.algorithm,
        )
