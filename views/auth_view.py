"""
Authentication View for Local Hire.
Provides login and registration interfaces with Kerala locality selection and demo account buttons.
"""

from typing import Any, List
import customtkinter as ctk

from coordinates import DISTRICTS, LOCALITIES_BY_DISTRICT
from views.base_view import (
    BaseView,
    COLOR_BG,
    COLOR_CARD,
    COLOR_BORDER,
    COLOR_PRIMARY,
    COLOR_PRIMARY_HOVER,
    COLOR_MUTED_TEXT,
    COLOR_DANGER,
    COLOR_SUCCESS,
    FONT_TITLE,
    FONT_SECTION,
    FONT_BODY,
    FONT_BODY_BOLD,
    FONT_SMALL,
    FONT_SMALL_BOLD,
)


class AuthView(BaseView):
    """View managing user sign-in and registration flows."""

    def __init__(self, master: Any, app: Any, **kwargs: Any) -> None:
        super().__init__(master, app, **kwargs)
        self.pack(fill="both", expand=True)

        self._build_ui()

    def _build_ui(self) -> None:
        """Constructs the centered card layout."""
        # Top branding header
        brand_frame = ctk.CTkFrame(self, fg_color="transparent")
        brand_frame.pack(pady=(36, 12))

        logo_lbl = ctk.CTkLabel(
            brand_frame,
            text="🤝 LOCAL HIRE",
            font=("Segoe UI", 28, "bold"),
            text_color=COLOR_PRIMARY,
        )
        logo_lbl.pack()

        tagline_lbl = ctk.CTkLabel(
            brand_frame,
            text="Direct Local Micro-Employment & Bilateral Protection System",
            font=FONT_BODY,
            text_color=COLOR_MUTED_TEXT,
        )
        tagline_lbl.pack(pady=(4, 0))

        geo_lbl = ctk.CTkLabel(
            brand_frame,
            text="📍 Kollam  •  Ernakulam  •  Thiruvananthapuram",
            font=FONT_SMALL_BOLD,
            text_color=COLOR_PRIMARY,
        )
        geo_lbl.pack(pady=(2, 0))

        # Main Card
        card = ctk.CTkFrame(
            self,
            fg_color=COLOR_CARD,
            corner_radius=16,
            border_width=1,
            border_color=COLOR_BORDER,
            width=500,
        )
        card.pack(pady=10, padx=20)

        # Tabview for Login vs Register
        self.tabview = ctk.CTkTabview(
            card,
            width=480,
            segmented_button_selected_color=COLOR_PRIMARY,
            segmented_button_selected_hover_color=COLOR_PRIMARY_HOVER,
        )
        self.tabview.pack(padx=20, pady=16)

        self.tab_login = self.tabview.add("  Sign In  ")
        self.tab_register = self.tabview.add("  Create Account  ")

        self._build_login_tab()
        self._build_register_tab()

    # ==========================================================================
    # LOGIN TAB
    # ==========================================================================
    def _build_login_tab(self) -> None:
        tab = self.tab_login

        lbl = ctk.CTkLabel(tab, text="Welcome Back", font=FONT_SECTION)
        lbl.pack(anchor="w", pady=(10, 4))

        sub = ctk.CTkLabel(
            tab,
            text="Sign in using your 10-digit registered phone number.",
            font=FONT_SMALL,
            text_color=COLOR_MUTED_TEXT,
        )
        sub.pack(anchor="w", pady=(0, 16))

        # Phone field
        ctk.CTkLabel(tab, text="Phone Number", font=FONT_BODY_BOLD).pack(anchor="w")
        self.login_phone_entry = ctk.CTkEntry(tab, placeholder_text="e.g. 9876543210", height=38, font=FONT_BODY)
        self.login_phone_entry.pack(fill="x", pady=(4, 12))

        # Password field
        ctk.CTkLabel(tab, text="Password", font=FONT_BODY_BOLD).pack(anchor="w")
        self.login_pass_entry = ctk.CTkEntry(tab, placeholder_text="••••••••", show="*", height=38, font=FONT_BODY)
        self.login_pass_entry.pack(fill="x", pady=(4, 8))

        # Status / Error Label
        self.login_msg_lbl = ctk.CTkLabel(tab, text="", font=FONT_SMALL_BOLD, text_color=COLOR_DANGER)
        self.login_msg_lbl.pack(pady=(2, 6))

        # Login Button
        self.btn_signin = ctk.CTkButton(
            tab,
            text="Sign In",
            font=FONT_BODY_BOLD,
            height=42,
            fg_color=COLOR_PRIMARY,
            hover_color=COLOR_PRIMARY_HOVER,
            command=self._handle_login,
        )
        self.btn_signin.pack(fill="x", pady=(4, 16))

        # Quick Test / Demo Accounts Pre-fill
        sep_frame = ctk.CTkFrame(tab, fg_color="transparent")
        sep_frame.pack(fill="x", pady=(8, 8))
        ctk.CTkLabel(sep_frame, text="Quick Fill Demo Accounts:", font=FONT_SMALL_BOLD, text_color=COLOR_MUTED_TEXT).pack(anchor="w")

        btn_box = ctk.CTkFrame(tab, fg_color="transparent")
        btn_box.pack(fill="x", pady=(4, 8))

        admin_demo = ctk.CTkButton(
            btn_box,
            text="Admin (0000000000)",
            font=FONT_SMALL,
            height=30,
            fg_color="#6d28d9",
            hover_color="#5b21b6",
            command=lambda: self._prefill_login("0000000000", "admin123"),
        )
        admin_demo.pack(side="left", expand=True, fill="x", padx=(0, 4))

        emp_demo = ctk.CTkButton(
            btn_box,
            text="Employer (9876543210)",
            font=FONT_SMALL,
            height=30,
            fg_color="#0284c7",
            hover_color="#0369a1",
            command=lambda: self._prefill_login("9876543210", "pass123"),
        )
        emp_demo.pack(side="left", expand=True, fill="x", padx=4)

        worker_demo = ctk.CTkButton(
            btn_box,
            text="Worker (9123456789)",
            font=FONT_SMALL,
            height=30,
            fg_color="#059669",
            hover_color="#047857",
            command=lambda: self._prefill_login("9123456789", "pass123"),
        )
        worker_demo.pack(side="left", expand=True, fill="x", padx=(4, 0))

    def _prefill_login(self, phone: str, pwd: str) -> None:
        self.login_phone_entry.delete(0, "end")
        self.login_phone_entry.insert(0, phone)
        self.login_pass_entry.delete(0, "end")
        self.login_pass_entry.insert(0, pwd)
        self.login_msg_lbl.configure(text=f"Filled credentials for {phone}", text_color=COLOR_MUTED_TEXT)

    def _handle_login(self) -> None:
        phone = self.login_phone_entry.get().strip()
        pwd = self.login_pass_entry.get().strip()

        ok, msg = self.app.session.login(phone, pwd)
        if ok:
            self.login_msg_lbl.configure(text=msg, text_color=COLOR_SUCCESS)
            self.app.on_login_success()
        else:
            self.login_msg_lbl.configure(text=msg, text_color=COLOR_DANGER)

    # ==========================================================================
    # REGISTER TAB
    # ==========================================================================
    def _build_register_tab(self) -> None:
        tab = self.tab_register

        # Full Name
        ctk.CTkLabel(tab, text="Full Name / Business Name", font=FONT_BODY_BOLD).pack(anchor="w", pady=(4, 2))
        self.reg_name_entry = ctk.CTkEntry(tab, placeholder_text="e.g. Rahul Sharma or Metro Bakery", height=34, font=FONT_BODY)
        self.reg_name_entry.pack(fill="x", pady=(0, 8))

        # Phone
        ctk.CTkLabel(tab, text="Phone Number (10 digits)", font=FONT_BODY_BOLD).pack(anchor="w", pady=(0, 2))
        self.reg_phone_entry = ctk.CTkEntry(tab, placeholder_text="e.g. 9845012345", height=34, font=FONT_BODY)
        self.reg_phone_entry.pack(fill="x", pady=(0, 8))

        # Role Selector
        ctk.CTkLabel(tab, text="Account Type", font=FONT_BODY_BOLD).pack(anchor="w", pady=(0, 2))
        self.reg_role_var = ctk.StringVar(value="worker")
        self.reg_role_seg = ctk.CTkSegmentedButton(
            tab,
            values=["worker", "employer"],
            variable=self.reg_role_var,
            font=FONT_BODY_BOLD,
            selected_color=COLOR_PRIMARY,
            selected_hover_color=COLOR_PRIMARY_HOVER,
        )
        self.reg_role_seg.pack(fill="x", pady=(0, 8))

        # District and Locality Row
        geo_box = ctk.CTkFrame(tab, fg_color="transparent")
        geo_box.pack(fill="x", pady=(0, 8))

        # District
        dist_frame = ctk.CTkFrame(geo_box, fg_color="transparent")
        dist_frame.pack(side="left", fill="x", expand=True, padx=(0, 6))
        ctk.CTkLabel(dist_frame, text="District", font=FONT_BODY_BOLD).pack(anchor="w", pady=(0, 2))
        self.reg_district_menu = ctk.CTkOptionMenu(
            dist_frame,
            values=DISTRICTS,
            command=self._on_district_changed,
            font=FONT_BODY,
            height=34,
        )
        self.reg_district_menu.pack(fill="x")
        self.reg_district_menu.set(DISTRICTS[0])

        # Locality
        loc_frame = ctk.CTkFrame(geo_box, fg_color="transparent")
        loc_frame.pack(side="left", fill="x", expand=True, padx=(6, 0))
        ctk.CTkLabel(loc_frame, text="Locality", font=FONT_BODY_BOLD).pack(anchor="w", pady=(0, 2))
        initial_localities = LOCALITIES_BY_DISTRICT[DISTRICTS[0]]
        self.reg_locality_menu = ctk.CTkOptionMenu(
            loc_frame,
            values=initial_localities,
            font=FONT_BODY,
            height=34,
        )
        self.reg_locality_menu.pack(fill="x")
        self.reg_locality_menu.set(initial_localities[0])

        # Password
        ctk.CTkLabel(tab, text="Password (min 6 characters)", font=FONT_BODY_BOLD).pack(anchor="w", pady=(0, 2))
        self.reg_pass_entry = ctk.CTkEntry(tab, placeholder_text="••••••••", show="*", height=34, font=FONT_BODY)
        self.reg_pass_entry.pack(fill="x", pady=(0, 8))

        # Confirm Password
        ctk.CTkLabel(tab, text="Confirm Password", font=FONT_BODY_BOLD).pack(anchor="w", pady=(0, 2))
        self.reg_pass_confirm_entry = ctk.CTkEntry(tab, placeholder_text="••••••••", show="*", height=34, font=FONT_BODY)
        self.reg_pass_confirm_entry.pack(fill="x", pady=(0, 8))

        # Message Label
        self.reg_msg_lbl = ctk.CTkLabel(tab, text="", font=FONT_SMALL_BOLD, text_color=COLOR_DANGER)
        self.reg_msg_lbl.pack(pady=(2, 6))

        # Register Button
        self.btn_register = ctk.CTkButton(
            tab,
            text="Create Account",
            font=FONT_BODY_BOLD,
            height=40,
            fg_color=COLOR_PRIMARY,
            hover_color=COLOR_PRIMARY_HOVER,
            command=self._handle_register,
        )
        self.btn_register.pack(fill="x", pady=(2, 8))

    def _on_district_changed(self, selected_district: str) -> None:
        """Dynamically populates localities dropdown based on selected district."""
        localities = LOCALITIES_BY_DISTRICT.get(selected_district, [])
        self.reg_locality_menu.configure(values=localities)
        if localities:
            self.reg_locality_menu.set(localities[0])

    def _handle_register(self) -> None:
        name = self.reg_name_entry.get().strip()
        phone = self.reg_phone_entry.get().strip()
        role = self.reg_role_var.get().strip()
        district = self.reg_district_menu.get().strip()
        locality = self.reg_locality_menu.get().strip()
        pwd = self.reg_pass_entry.get().strip()
        confirm_pwd = self.reg_pass_confirm_entry.get().strip()

        if pwd != confirm_pwd:
            self.reg_msg_lbl.configure(text="Passwords do not match.", text_color=COLOR_DANGER)
            return

        ok, msg = self.app.session.register(
            name=name,
            phone=phone,
            password=pwd,
            role=role,
            district=district,
            locality=locality,
        )

        if ok:
            self.reg_msg_lbl.configure(text=msg, text_color=COLOR_SUCCESS)
            # Switch to Sign In tab and pre-fill phone
            self.tabview.set("  Sign In  ")
            self.login_phone_entry.delete(0, "end")
            self.login_phone_entry.insert(0, phone)
            self.login_pass_entry.delete(0, "end")
            self.login_msg_lbl.configure(text="Account created! Please enter your password to sign in.", text_color=COLOR_SUCCESS)
        else:
            self.reg_msg_lbl.configure(text=msg, text_color=COLOR_DANGER)

