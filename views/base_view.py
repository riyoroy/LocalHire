"""
Base View and UI Styling Constants for Local Hire.
Provides consistent colors, fonts, modal dialogs, and navigation headers.
"""

from typing import Any, Callable, Dict, Optional
import customtkinter as ctk

# Color Palette (Dual Mode: light, dark)
COLOR_PRIMARY = "#2563eb"
COLOR_PRIMARY_HOVER = "#1d4ed8"
COLOR_SECONDARY = "#475569"
COLOR_SECONDARY_HOVER = "#334155"
COLOR_SUCCESS = "#16a34a"
COLOR_SUCCESS_HOVER = "#15803d"
COLOR_WARNING = "#d97706"
COLOR_WARNING_HOVER = "#b45309"
COLOR_DANGER = "#dc2626"
COLOR_DANGER_HOVER = "#b91c1c"

# Structural Colors
COLOR_BG = ("#f1f5f9", "#0f172a")
COLOR_CARD = ("#ffffff", "#1e293b")
COLOR_CARD_HOVER = ("#f8fafc", "#243247")
COLOR_BORDER = ("#cbd5e1", "#334155")
COLOR_MUTED_TEXT = ("#64748b", "#94a3b8")
COLOR_TITLE_TEXT = ("#0f172a", "#f8fafc")

# Typography
FONT_FAMILY = "Segoe UI"
FONT_TITLE = (FONT_FAMILY, 20, "bold")
FONT_SECTION = (FONT_FAMILY, 16, "bold")
FONT_CARD_TITLE = (FONT_FAMILY, 15, "bold")
FONT_BODY = (FONT_FAMILY, 13)
FONT_BODY_BOLD = (FONT_FAMILY, 13, "bold")
FONT_SMALL = (FONT_FAMILY, 11)
FONT_SMALL_BOLD = (FONT_FAMILY, 11, "bold")
FONT_BADGE = (FONT_FAMILY, 10, "bold")


class BaseView(ctk.CTkFrame):
    """Base class for all application views with common header and utilities."""

    def __init__(self, master: Any, app: Any, **kwargs: Any) -> None:
        super().__init__(master, fg_color="transparent", **kwargs)
        self.app = app

    def create_header(self, title: str, subtitle: Optional[str] = None) -> ctk.CTkFrame:
        """Constructs a responsive header banner with user details, status badges, and action buttons."""
        header = ctk.CTkFrame(self, fg_color=COLOR_CARD, corner_radius=12, border_width=1, border_color=COLOR_BORDER)
        header.pack(fill="x", padx=16, pady=(12, 10))

        # Left: App Brand & View Title
        left_box = ctk.CTkFrame(header, fg_color="transparent")
        left_box.pack(side="left", padx=16, pady=12)

        app_title = ctk.CTkLabel(
            left_box,
            text=f"LOCAL HIRE  |  {title}",
            font=FONT_TITLE,
            text_color=COLOR_TITLE_TEXT,
        )
        app_title.pack(anchor="w")

        if subtitle:
            sub_lbl = ctk.CTkLabel(
                left_box,
                text=subtitle,
                font=FONT_SMALL,
                text_color=COLOR_MUTED_TEXT,
            )
            sub_lbl.pack(anchor="w", pady=(2, 0))

        # Right: User info, Mode toggle & Logout
        right_box = ctk.CTkFrame(header, fg_color="transparent")
        right_box.pack(side="right", padx=16, pady=12)

        user = self.app.session.current_user
        if user:
            # User Name & Locality
            info_frame = ctk.CTkFrame(right_box, fg_color="transparent")
            info_frame.pack(side="left", padx=(0, 16))

            name_lbl = ctk.CTkLabel(
                info_frame,
                text=f"{user['name']}",
                font=FONT_BODY_BOLD,
                text_color=COLOR_TITLE_TEXT,
            )
            name_lbl.pack(anchor="e")

            loc_lbl = ctk.CTkLabel(
                info_frame,
                text=f"📍 {user.get('locality', 'Kerala')}",
                font=FONT_SMALL,
                text_color=COLOR_MUTED_TEXT,
            )
            loc_lbl.pack(anchor="e")

            # Role Badge
            role_text = user["role"].upper()
            role_color = COLOR_PRIMARY
            if user["role"] == "admin":
                role_color = "#7c3aed"  # Violet for admin
            elif user["role"] == "employer":
                role_color = "#0284c7"  # Sky blue for employer
            elif user["role"] == "worker":
                role_color = "#059669"  # Emerald for worker

            role_badge = ctk.CTkLabel(
                right_box,
                text=f" {role_text} ",
                font=FONT_BADGE,
                fg_color=role_color,
                text_color="#ffffff",
                corner_radius=6,
            )
            role_badge.pack(side="left", padx=(0, 12))

            # Status Warning Badges (Blacklisted / Suspended)
            if user.get("is_blacklisted", 0) == 1:
                bl_badge = ctk.CTkLabel(
                    right_box,
                    text=" ⚠️ BLACKLISTED ",
                    font=FONT_BADGE,
                    fg_color=COLOR_DANGER,
                    text_color="#ffffff",
                    corner_radius=6,
                )
                bl_badge.pack(side="left", padx=(0, 10))

            if user.get("is_suspended", 0) == 1:
                susp_badge = ctk.CTkLabel(
                    right_box,
                    text=" ⚠️ SUSPENDED (3 STRIKES) ",
                    font=FONT_BADGE,
                    fg_color=COLOR_DANGER,
                    text_color="#ffffff",
                    corner_radius=6,
                )
                susp_badge.pack(side="left", padx=(0, 10))

            # Logout button
            logout_btn = ctk.CTkButton(
                right_box,
                text="Logout",
                width=80,
                height=32,
                font=FONT_SMALL_BOLD,
                fg_color=COLOR_DANGER,
                hover_color=COLOR_DANGER_HOVER,
                command=self.app.logout,
            )
            logout_btn.pack(side="left", padx=(4, 0))

        return header

    def show_modal(
        self,
        title: str,
        width: int = 500,
        height: int = 400,
    ) -> ctk.CTkToplevel:
        """Creates a centered, modal modal dialog on top of the root window."""
        modal = ctk.CTkToplevel(self)
        modal.title(title)
        modal.geometry(f"{width}x{height}")
        modal.resizable(False, False)
        modal.transient(self.winfo_toplevel())
        modal.grab_set()

        # Center on screen / parent
        parent_x = self.winfo_toplevel().winfo_x()
        parent_y = self.winfo_toplevel().winfo_y()
        parent_w = self.winfo_toplevel().winfo_width()
        parent_h = self.winfo_toplevel().winfo_height()

        x = parent_x + max(0, (parent_w - width) // 2)
        y = parent_y + max(0, (parent_h - height) // 2)
        modal.geometry(f"{width}x{height}+{x}+{y}")

        return modal

    def show_alert(self, title: str, message: str, is_error: bool = False) -> None:
        """Displays a clean informational or error popup dialog."""
        modal = self.show_modal(title, width=420, height=220)

        frame = ctk.CTkFrame(modal, fg_color=COLOR_CARD, corner_radius=12)
        frame.pack(fill="both", expand=True, padx=16, pady=16)

        title_color = COLOR_DANGER if is_error else COLOR_PRIMARY
        title_label = ctk.CTkLabel(frame, text=title, font=FONT_SECTION, text_color=title_color)
        title_label.pack(pady=(16, 8), padx=16)

        msg_label = ctk.CTkLabel(
            frame,
            text=message,
            font=FONT_BODY,
            wraplength=360,
            justify="center",
        )
        msg_label.pack(pady=(4, 16), padx=16, fill="both", expand=True)

        btn = ctk.CTkButton(
            frame,
            text="Close",
            font=FONT_BODY_BOLD,
            width=100,
            fg_color=COLOR_PRIMARY,
            hover_color=COLOR_PRIMARY_HOVER,
            command=modal.destroy,
        )
        btn.pack(pady=(0, 16))

