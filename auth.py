"""
Authentication and Session Management Module for Local Hire.
Implements zero-dependency SHA-256 password hashing with salt and centralized session tracking.
"""

import hashlib
import secrets
from typing import Any, Dict, Optional, Tuple

import database


def hash_password(password: str, salt: Optional[str] = None) -> Tuple[str, str]:
    """
    Hashes a password using SHA-256 with a unique random hexadecimal salt.
    Returns (password_hash, salt).
    """
    if not salt:
        salt = secrets.token_hex(16)
    hashed = hashlib.sha256((salt + password).encode("utf-8")).hexdigest()
    return hashed, salt


def verify_password(password: str, stored_hash: str, salt: str) -> bool:
    """Verifies a plain text password against the stored salt and hash."""
    hashed, _ = hash_password(password, salt)
    return hashed == stored_hash


class SessionManager:
    """Manages active user authentication session and role state."""

    def __init__(self) -> None:
        self._current_user: Optional[Dict[str, Any]] = None

    @property
    def current_user(self) -> Optional[Dict[str, Any]]:
        return self._current_user

    def is_authenticated(self) -> bool:
        return self._current_user is not None

    def get_role(self) -> Optional[str]:
        return self._current_user.get("role") if self._current_user else None

    def is_worker(self) -> bool:
        return self.get_role() == "worker"

    def is_employer(self) -> bool:
        return self.get_role() == "employer"

    def is_admin(self) -> bool:
        return self.get_role() == "admin"

    def is_suspended(self) -> bool:
        return bool(self._current_user and self._current_user.get("is_suspended", 0) == 1)

    def is_blacklisted(self) -> bool:
        return bool(self._current_user and self._current_user.get("is_blacklisted", 0) == 1)

    def login(self, phone: str, password: str) -> Tuple[bool, str]:
        """
        Validates phone and password.
        Returns (success: bool, message: str).
        """
        phone = phone.strip()
        if not phone:
            return False, "Please enter your phone number."

        if not password:
            return False, "Please enter your password."

        user = database.get_user_by_phone(phone)
        if not user:
            return False, "No account found with this phone number."

        if not verify_password(password, user["password_hash"], user["salt"]):
            return False, "Incorrect password. Please try again."

        # Successful login - store safe user details
        self._current_user = {
            "user_id": user["user_id"],
            "name": user["name"],
            "phone": user["phone"],
            "role": user["role"],
            "district": user["district"],
            "locality": user["locality"],
            "is_blacklisted": user["is_blacklisted"],
            "is_suspended": user["is_suspended"],
            "created_at": user["created_at"],
        }
        return True, f"Welcome back, {user['name']}!"

    def register(
        self,
        name: str,
        phone: str,
        password: str,
        role: str,
        district: str,
        locality: str,
    ) -> Tuple[bool, str]:
        """
        Validates and registers a new user.
        Returns (success: bool, message: str).
        """
        name = name.strip()
        phone = phone.strip()
        password = password.strip()

        if not name:
            return False, "Name cannot be empty."

        if not phone.isdigit() or len(phone) != 10:
            return False, "Phone number must be a valid 10-digit number."

        if len(password) < 6:
            return False, "Password must be at least 6 characters long."

        if role not in ("worker", "employer"):
            return False, "Please select a valid account role (Worker or Employer)."

        if not district or not locality:
            return False, "Please select both District and Locality."

        pwd_hash, salt = hash_password(password)

        try:
            user_id = database.create_user(
                name=name,
                phone=phone,
                password_hash=pwd_hash,
                salt=salt,
                role=role,
                district=district,
                locality=locality,
            )
            return True, "Registration successful! You may now sign in."
        except ValueError as e:
            return False, str(e)
        except Exception as e:
            return False, f"Registration failed: {e}"

    def logout(self) -> None:
        """Clears the active session."""
        self._current_user = None

    def refresh(self) -> None:
        """Reloads the current user's profile from the database (e.g. for status updates)."""
        if not self._current_user:
            return

        user = database.get_user_by_id(self._current_user["user_id"])
        if user:
            self._current_user = {
                "user_id": user["user_id"],
                "name": user["name"],
                "phone": user["phone"],
                "role": user["role"],
                "district": user["district"],
                "locality": user["locality"],
                "is_blacklisted": user["is_blacklisted"],
                "is_suspended": user["is_suspended"],
                "created_at": user["created_at"],
            }


# Singleton session instance for the application runtime
session = SessionManager()

