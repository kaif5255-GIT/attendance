# Standard Python built-in hashlib password security (Zero heavy external packages)
import hashlib
import secrets

try:
    from pwdlib import PasswordHash
    _pwd_context = PasswordHash.recommended()
except Exception:
    _pwd_context = None


def hash_password(password: str) -> str:
    salt = secrets.token_hex(8)
    hashed = hashlib.sha256((salt + password).encode("utf-8")).hexdigest()
    return f"{salt}${hashed}"


def verify_password(password: str, hashed_password: str) -> bool:
    try:
        # Backward compatibility for existing argon2 hashes if pwdlib is installed
        if hashed_password.startswith("$argon2"):
            if _pwd_context is not None:
                return _pwd_context.verify(password, hashed_password)
            return False

        # Standard salt$hash verification using built-in hashlib
        if "$" in hashed_password:
            salt, stored_hash = hashed_password.split("$", 1)
            computed = hashlib.sha256((salt + password).encode("utf-8")).hexdigest()
            return secrets.compare_digest(stored_hash, computed)

        # Plain SHA-256 or direct fallback
        computed = hashlib.sha256(password.encode("utf-8")).hexdigest()
        return secrets.compare_digest(hashed_password, computed)
    except Exception:
        return False
