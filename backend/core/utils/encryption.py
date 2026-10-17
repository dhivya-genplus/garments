import base64
import hashlib
from typing import Optional, Any
from django.conf import settings
from django.db import models
from cryptography.fernet import Fernet, InvalidToken

CIPHER_PREFIX = "enc:v1:"


class EncryptionService:
    """
    Symmetric authenticated encryption service for sensitive data fields.
    Uses Fernet (AES-128-CBC + HMAC-SHA256).
    Key is derived securely from settings.COMPANY_ENCRYPTION_KEY or settings.SECRET_KEY.
    """
    _fernet: Optional[Fernet] = None

    @classmethod
    def get_fernet(cls) -> Fernet:
        if cls._fernet is None:
            raw_key = getattr(settings, "COMPANY_ENCRYPTION_KEY", None)
            if raw_key:
                key = raw_key.encode("utf-8") if isinstance(raw_key, str) else raw_key
            else:
                secret = getattr(settings, "SECRET_KEY", "garments-erp-default-secret-key")
                derived = hashlib.sha256(secret.encode("utf-8")).digest()
                key = base64.urlsafe_b64encode(derived)
            cls._fernet = Fernet(key)
        return cls._fernet

    @classmethod
    def encrypt(cls, value: Optional[str]) -> Optional[str]:
        """
        Encrypts a plain text string.
        Returns ciphertext prefixed with 'enc:v1:'.
        If already encrypted, returns as is.
        """
        if value is None:
            return None
        if not isinstance(value, str):
            value = str(value)
        value = value.strip()
        if not value:
            return value
        if cls.is_encrypted(value):
            return value

        fernet = cls.get_fernet()
        token = fernet.encrypt(value.encode("utf-8")).decode("utf-8")
        return f"{CIPHER_PREFIX}{token}"

    @classmethod
    def decrypt(cls, value: Optional[str]) -> Optional[str]:
        """
        Decrypts a ciphertext string starting with 'enc:v1:'.
        If value is unencrypted (legacy plain text), returns it directly.
        """
        if value is None:
            return None
        if not isinstance(value, str):
            value = str(value)
        if not cls.is_encrypted(value):
            return value

        token = value[len(CIPHER_PREFIX):]
        fernet = cls.get_fernet()
        try:
            decrypted_bytes = fernet.decrypt(token.encode("utf-8"))
            return decrypted_bytes.decode("utf-8")
        except (InvalidToken, Exception):
            # If decryption fails (corrupted data), preserve original value to prevent data loss
            return value

    @classmethod
    def is_encrypted(cls, value: Optional[str]) -> bool:
        """Checks if a string is encrypted with the current prefix."""
        return bool(value and isinstance(value, str) and value.startswith(CIPHER_PREFIX))


class EncryptedCharField(models.CharField):
    """
    Django model field that automatically encrypts plaintext on database save
    and transparently decrypts ciphertext on retrieval.
    """
    description = "Encrypted CharField storing authenticated ciphertext"

    def __init__(self, *args: Any, **kwargs: Any):
        # Ensure default length can accommodate ciphertext overhead
        kwargs.setdefault("max_length", 512)
        super().__init__(*args, **kwargs)

    def get_internal_type(self) -> str:
        return "CharField"

    def from_db_value(self, value: Any, expression: Any, connection: Any) -> Optional[str]:
        if value is None:
            return None
        return EncryptionService.decrypt(value)

    def to_python(self, value: Any) -> Optional[str]:
        if value is None or not isinstance(value, str):
            return value
        return EncryptionService.decrypt(value)

    def get_prep_value(self, value: Any) -> Optional[str]:
        value = super().get_prep_value(value)
        if value is None:
            return None
        return EncryptionService.encrypt(value)
