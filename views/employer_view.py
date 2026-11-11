"""
Employer View for Local Hire.
Features Job Posting with backend blacklist validation, listings management,
applicant review with Haversine proximity, candidate decisions, and no-show reporting.
"""

from typing import Any, Dict, List, Optional
import customtkinter as ctk

import database
from coordinates import (
    DISTRICTS,
    LOCALITIES_BY_DISTRICT,
    JOB_CATEGORIES,
    calculate_distance,
    format_distance,
)
from views.base_view import (
    BaseView,
    COLOR_CARD,
    COLOR_BORDER,
    COLOR_PRIMARY,
    COLOR_PRIMARY_HOVER,
    COLOR_MUTED_TEXT,
    COLOR_TITLE_TEXT,
    COLOR_SUCCESS,
    COLOR_SUCCESS_HOVER,
    COLOR_WARNING,
    COLOR_DANGER,
    COLOR_DANGER_HOVER,
    COLOR_SECONDARY,
    COLOR_SECONDARY_HOVER,
    FONT_TITLE,
    FONT_SECTION,
    FONT_CARD_TITLE,
    FONT_BODY,
    FONT_BODY_BOLD,
    FONT_SMALL,
    FONT_SMALL_BOLD,
    FONT_BADGE,
)


class EmployerView(BaseView):
    """Dashboard interface for Employers and Business Owners."""

    def __init__(self, master: Any, app: Any, **kwargs: Any) -> None:
        super().__init__(master, app, **kwargs)
        self.pack(fill="both", expand=True)

        self._build_ui()

    def _build_ui(self) -> None:
        """Constructs header, alert banners, and navigation tabs."""
        self.create_header(
            title="Employer Console",
            subtitle="Post shifts, screen local applicants, and manage workforce attendance.",
        )

        user = self.app.session.current_user
        if not user:
            return

        # Blacklist Alert Banner if employer is blacklisted
        if user.get("is_blacklisted", 0) == 1:
            bl_frame = ctk.CTkFrame(self, fg_color="#7f1d1d", corner_radius=8)
            bl_frame.pack(fill="x", padx=16, pady=(0, 8))

            lbl = ctk.CTkLabel(
                bl_frame,
                text="⚠️ ACCOUNT BLACKLISTED: Your account has been permanently blacklisted due to verified "
                     "wage theft or non-payment. Job posting privileges have been revoked.",
                font=FONT_BODY_BOLD,
                text_color="#fecaca",
            )
            lbl.pack(padx=16, pady=10)

        # Tabview for Navigation
        self.tabview = ctk.CTkTabview(
            self,
            segmented_button_selected_color=COLOR_PRIMARY,
            segmented_button_selected_hover_color=COLOR_PRIMARY_HOVER,
        )
        self.tabview.pack(fill="both", expand=True, padx=16, pady=(0, 12))

        self.tab_listings = self.tabview.add("  My Listings & Applicants  ")
        self.tab_post_job = self.tabview.add("  Post New Job  ")
        self.tab_disputes = self.tabview.add("  No-Show Reports  ")

        self._build_listings_tab()
        self._build_post_job_tab()
        self._build_disputes_tab()

    # ==========================================================================
    # TAB 1: MY LISTINGS & APPLICANTS
    # ==========================================================================
    def _build_listings_tab(self) -> None:
        tab = self.tab_listings

        top_bar = ctk.CTkFrame(tab, fg_color="transparent")
        top_bar.pack(fill="x", padx=8, pady=(8, 10))

        ctk.CTkLabel(
            top_bar,
            text="Manage active jobs, review applicant proximity, and accept candidates.",
            font=FONT_BODY,
            text_color=COLOR_MUTED_TEXT,
        ).pack(side="left")

        ctk.CTkButton(
            top_bar,
            text="🔄 Refresh",
            width=90,
            height=32,
            font=FONT_SMALL_BOLD,
            fg_color=COLOR_SECONDARY,
            hover_color=COLOR_SECONDARY_HOVER,
            command=self.refresh_listings,
        ).pack(side="right")

        self.listings_scroll = ctk.CTkScrollableFrame(tab, fg_color="transparent")
        self.listings_scroll.pack(fill="both", expand=True, padx=4, pady=4)

        self.refresh_listings()

    def refresh_listings(self) -> None:
        """Fetches employer's jobs and renders them with applicants."""
        for widget in self.listings_scroll.winfo_children():
            widget.destroy()

        user = self.app.session.current_user
        if not user:
            return

        jobs = database.get_jobs_by_employer(user["user_id"])

        if not jobs:
            empty = ctk.CTkFrame(self.listings_scroll, fg_color=COLOR_CARD, corner_radius=12)
            empty.pack(fill="x", padx=16, pady=24)
            ctk.CTkLabel(
                empty,
                text="You have not posted any jobs yet.\nClick on the 'Post New Job' tab to create your first listing!",
                font=FONT_BODY,
                text_color=COLOR_MUTED_TEXT,
            ).pack(pady=24)
            return

        for job in jobs:
            self._render_job_management_card(job)

    def _render_job_management_card(self, job: Dict[str, Any]) -> None:
        card = ctk.CTkFrame(
            self.listings_scroll,
            fg_color=COLOR_CARD,
            corner_radius=12,
            border_width=1,
            border_color=COLOR_BORDER,
        )
        card.pack(fill="x", padx=8, pady=8)

        content = ctk.CTkFrame(card, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=16, pady=12)

        # Job Summary Header
        top_row = ctk.CTkFrame(content, fg_color="transparent")
        top_row.pack(fill="x")

        ctk.CTkLabel(top_row, text=job["title"], font=FONT_CARD_TITLE, text_color=COLOR_TITLE_TEXT).pack(side="left")

        # Status badge
        status = job["status"]
        status_colors = {
            "open": COLOR_SUCCESS,
            "filled": "#0284c7",
            "completed": "#7c3aed",
            "cancelled": COLOR_DANGER,
        }
        ctk.CTkLabel(
            top_row,
            text=f" {status.upper()} ",
            font=FONT_BADGE,
            fg_color=status_colors.get(status, COLOR_SECONDARY),
            text_color="#ffffff",
            corner_radius=6,
        ).pack(side="left", padx=10)

        # Right side: Job Status Actions
        actions_box = ctk.CTkFrame(top_row, fg_color="transparent")
        actions_box.pack(side="right")

        if status == "open":
            ctk.CTkButton(
                actions_box,
                text="Mark Filled",
                font=FONT_SMALL,
                width=80,
                height=26,
                fg_color="#0284c7",
                hover_color="#0369a1",
                command=lambda: self._update_job_status(job["job_id"], "filled"),
            ).pack(side="left", padx=2)

        if status in ("open", "filled"):
            ctk.CTkButton(
                actions_box,
                text="Mark Completed",
                font=FONT_SMALL,
                width=110,
                height=26,
                fg_color="#7c3aed",
                hover_color="#6d28d9",
                command=lambda: self._update_job_status(job["job_id"], "completed"),
            ).pack(side="left", padx=2)

            ctk.CTkButton(
                actions_box,
                text="Cancel",
                font=FONT_SMALL,
                width=65,
                height=26,
                fg_color=COLOR_DANGER,
                hover_color=COLOR_DANGER_HOVER,
                command=lambda: self._update_job_status(job["job_id"], "cancelled"),
            ).pack(side="left", padx=2)

        # Job Specs
        specs_row = ctk.CTkFrame(content, fg_color="transparent")
        specs_row.pack(fill="x", pady=(4, 6))

        info_text = (
            f"Category: {job['category']}  |  📍 {job['locality']}  |  "
            f"📅 {job['job_date']} ({job['start_time']} - {job['end_time']})  |  "
            f"Pay: ₹{job['payment']:.0f}"
        )
        ctk.CTkLabel(specs_row, text=info_text, font=FONT_SMALL, text_color=COLOR_MUTED_TEXT).pack(anchor="w")

        # Applicants Section
        applicants = database.get_job_applicants(job["job_id"])
        app_count = len(applicants)

        ctk.CTkLabel(
            content,
            text=f"Applicants ({app_count}):",
            font=FONT_BODY_BOLD,
            text_color=COLOR_TITLE_TEXT,
        ).pack(anchor="w", pady=(8, 4))

        if not applicants:
            ctk.CTkLabel(
                content,
                text="No workers have applied for this listing yet.",
                font=FONT_SMALL,
                text_color=COLOR_MUTED_TEXT,
            ).pack(anchor="w", padx=10, pady=(2, 6))
        else:
            app_container = ctk.CTkFrame(content, fg_color="transparent")
            app_container.pack(fill="x", pady=2)

            for applicant in applicants:
                self._render_applicant_row(app_container, job, applicant)

    def _render_applicant_row(
        self,
        container: ctk.CTkFrame,
        job: Dict[str, Any],
        applicant: Dict[str, Any],
    ) -> None:
        """Renders individual applicant info, proximity distance, strikes, and decision buttons."""
        app_box = ctk.CTkFrame(
            container,
            fg_color=("rgba(0,0,0,0.03)", "rgba(255,255,255,0.04)"),
            corner_radius=8,
            border_width=1,
            border_color=COLOR_BORDER,
        )
        app_box.pack(fill="x", pady=3)

        inner = ctk.CTkFrame(app_box, fg_color="transparent")
        inner.pack(fill="x", padx=12, pady=8)

        # Worker Details (Name, Phone, Locality, Distance)
        left = ctk.CTkFrame(inner, fg_color="transparent")
        left.pack(side="left")

        # Calculate distance between worker locality and job locality
        dist_km = calculate_distance(applicant["worker_locality"], job["locality"])
        dist_display = format_distance(dist_km)

        name_txt = f"{applicant['worker_name']} (📞 {applicant['worker_phone']})"
        ctk.CTkLabel(left, text=name_txt, font=FONT_BODY_BOLD, text_color=COLOR_TITLE_TEXT).pack(anchor="w")

        meta_txt = f"📍 {applicant['worker_locality']}  •  Proximity: {dist_display}"
        ctk.CTkLabel(left, text=meta_txt, font=FONT_SMALL, text_color=COLOR_MUTED_TEXT).pack(anchor="w")

        # Strikes indicator
        strikes_count = applicant.get("active_strikes_count", 0)
        if strikes_count > 0:
            strike_color = COLOR_DANGER if strikes_count >= 3 else COLOR_WARNING
            ctk.CTkLabel(
                left,
                text=f"⚠️ {strikes_count} Active Strike(s) on record",
                font=FONT_SMALL_BOLD,
                text_color=strike_color,
            ).pack(anchor="w")

        # Right side: Status and Actions
        right = ctk.CTkFrame(inner, fg_color="transparent")
        right.pack(side="right")

        app_status = applicant["status"]
        app_id = applicant["application_id"]

        if app_status == "pending":
            ctk.CTkButton(
                right,
                text="✓ Accept",
                font=FONT_SMALL_BOLD,
                width=80,
                height=30,
                fg_color=COLOR_SUCCESS,
                hover_color=COLOR_SUCCESS_HOVER,
                command=lambda: self._handle_applicant_decision(app_id, "accepted"),
            ).pack(side="left", padx=4)

            ctk.CTkButton(
                right,
                text="✕ Reject",
                font=FONT_SMALL_BOLD,
                width=80,
                height=30,
                fg_color=COLOR_DANGER,
                hover_color=COLOR_DANGER_HOVER,
                command=lambda: self._handle_applicant_decision(app_id, "rejected"),
            ).pack(side="left", padx=4)

        elif app_status == "accepted":
            ctk.CTkLabel(
                right,
                text=" ACCEPTED ",
                font=FONT_BADGE,
                fg_color=COLOR_SUCCESS,
                text_color="#ffffff",
                corner_radius=6,
            ).pack(side="left", padx=6)

            # Report No-Show button
            ctk.CTkButton(
                right,
                text="Report No-Show",
                font=FONT_SMALL_BOLD,
                width=120,
                height=30,
                fg_color=COLOR_DANGER,
                hover_color=COLOR_DANGER_HOVER,
                command=lambda: self._open_no_show_modal(job, applicant),
            ).pack(side="left", padx=4)

        else:
            ctk.CTkLabel(
                right,
                text=f" {app_status.upper()} ",
                font=FONT_BADGE,
                fg_color=COLOR_SECONDARY,
                text_color="#ffffff",
                corner_radius=6,
            ).pack(side="left", padx=6)

    def _handle_applicant_decision(self, app_id: int, decision: str) -> None:
        user = self.app.session.current_user
        if not user:
            return

        try:
            database.update_application_status(
                application_id=app_id,
                new_status=decision,
                employer_id=user["user_id"],
            )
            self.refresh_listings()
        except ValueError as e:
            self.show_alert("Action Failed", str(e), is_error=True)

    def _update_job_status(self, job_id: int, new_status: str) -> None:
        user = self.app.session.current_user
        if not user:
            return

        try:
            database.update_job_status(job_id=job_id, new_status=new_status, employer_id=user["user_id"])
            self.refresh_listings()
        except ValueError as e:
            self.show_alert("Status Update Failed", str(e), is_error=True)

    # ==========================================================================
    # TAB 2: POST NEW JOB
    # ==========================================================================
    def _build_post_job_tab(self) -> None:
        tab = self.tab_post_job

        card = ctk.CTkFrame(tab, fg_color=COLOR_CARD, corner_radius=12, border_width=1, border_color=COLOR_BORDER)
        card.pack(fill="x", padx=16, pady=12)

        content = ctk.CTkFrame(card, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=24, pady=16)

        ctk.CTkLabel(content, text="Create a Micro-Job Posting", font=FONT_SECTION, text_color=COLOR_TITLE_TEXT).pack(anchor="w")
        ctk.CTkLabel(
            content,
            text="Specify shift timing, clear payment, and exact district locality.",
            font=FONT_SMALL,
            text_color=COLOR_MUTED_TEXT,
        ).pack(anchor="w", pady=(0, 14))

        # Job Title
        ctk.CTkLabel(content, text="Job Title", font=FONT_BODY_BOLD).pack(anchor="w", pady=(4, 2))
        self.job_title_entry = ctk.CTkEntry(content, placeholder_text="e.g. Sales Assistant or Event Setup Helper", height=36, font=FONT_BODY)
        self.job_title_entry.pack(fill="x", pady=(0, 10))

        # Category and Payment Row
        row1 = ctk.CTkFrame(content, fg_color="transparent")
        row1.pack(fill="x", pady=(0, 10))

        # Category
        cat_box = ctk.CTkFrame(row1, fg_color="transparent")
        cat_box.pack(side="left", fill="x", expand=True, padx=(0, 8))
        ctk.CTkLabel(cat_box, text="Category", font=FONT_BODY_BOLD).pack(anchor="w", pady=(0, 2))
        self.job_category_menu = ctk.CTkOptionMenu(cat_box, values=JOB_CATEGORIES, height=36, font=FONT_BODY)
        self.job_category_menu.pack(fill="x")
        self.job_category_menu.set(JOB_CATEGORIES[0])

        # Payment (₹)
        pay_box = ctk.CTkFrame(row1, fg_color="transparent")
        pay_box.pack(side="left", fill="x", expand=True, padx=(8, 0))
        ctk.CTkLabel(pay_box, text="Shift Payment (₹)", font=FONT_BODY_BOLD).pack(anchor="w", pady=(0, 2))
        self.job_pay_entry = ctk.CTkEntry(pay_box, placeholder_text="e.g. 600", height=36, font=FONT_BODY)
        self.job_pay_entry.pack(fill="x")

        # District and Locality Row
        geo_box = ctk.CTkFrame(content, fg_color="transparent")
        geo_box.pack(fill="x", pady=(0, 10))

        # District
        dist_box = ctk.CTkFrame(geo_box, fg_color="transparent")
        dist_box.pack(side="left", fill="x", expand=True, padx=(0, 8))
        ctk.CTkLabel(dist_box, text="District", font=FONT_BODY_BOLD).pack(anchor="w", pady=(0, 2))
        self.job_district_menu = ctk.CTkOptionMenu(
            dist_box,
            values=DISTRICTS,
            command=self._on_job_district_changed,
            height=36,
            font=FONT_BODY,
        )
        self.job_district_menu.pack(fill="x")
        self.job_district_menu.set(DISTRICTS[0])

        # Locality
        loc_box = ctk.CTkFrame(geo_box, fg_color="transparent")
        loc_box.pack(side="left", fill="x", expand=True, padx=(8, 0))
        ctk.CTkLabel(loc_box, text="Locality", font=FONT_BODY_BOLD).pack(anchor="w", pady=(0, 2))
        initial_locs = LOCALITIES_BY_DISTRICT[DISTRICTS[0]]
        self.job_locality_menu = ctk.CTkOptionMenu(loc_box, values=initial_locs, height=36, font=FONT_BODY)
        self.job_locality_menu.pack(fill="x")
        self.job_locality_menu.set(initial_locs[0])

        # Date and Timing Row
        time_box = ctk.CTkFrame(content, fg_color="transparent")
        time_box.pack(fill="x", pady=(0, 14))

        # Date
        date_col = ctk.CTkFrame(time_box, fg_color="transparent")
        date_col.pack(side="left", fill="x", expand=True, padx=(0, 8))
        ctk.CTkLabel(date_col, text="Job Date (YYYY-MM-DD)", font=FONT_BODY_BOLD).pack(anchor="w", pady=(0, 2))
        self.job_date_entry = ctk.CTkEntry(date_col, placeholder_text="2026-11-20", height=36, font=FONT_BODY)
        self.job_date_entry.insert(0, "2026-11-20")
        self.job_date_entry.pack(fill="x")

        # Start Time
        start_col = ctk.CTkFrame(time_box, fg_color="transparent")
        start_col.pack(side="left", fill="x", expand=True, padx=4)
        ctk.CTkLabel(start_col, text="Start Time", font=FONT_BODY_BOLD).pack(anchor="w", pady=(0, 2))
        self.job_start_entry = ctk.CTkEntry(start_col, placeholder_text="09:00", height=36, font=FONT_BODY)
        self.job_start_entry.insert(0, "09:00")
        self.job_start_entry.pack(fill="x")

        # End Time
        end_col = ctk.CTkFrame(time_box, fg_color="transparent")
        end_col.pack(side="left", fill="x", expand=True, padx=(8, 0))
        ctk.CTkLabel(end_col, text="End Time", font=FONT_BODY_BOLD).pack(anchor="w", pady=(0, 2))
        self.job_end_entry = ctk.CTkEntry(end_col, placeholder_text="18:00", height=36, font=FONT_BODY)
        self.job_end_entry.insert(0, "18:00")
        self.job_end_entry.pack(fill="x")

        # Submit Button
        self.btn_submit_job = ctk.CTkButton(
            content,
            text="Publish Job Listing",
            font=FONT_BODY_BOLD,
            height=42,
            fg_color=COLOR_PRIMARY,
            hover_color=COLOR_PRIMARY_HOVER,
            command=self._handle_create_job,
        )
        self.btn_submit_job.pack(fill="x", pady=(10, 4))

    def _on_job_district_changed(self, selected_district: str) -> None:
        localities = LOCALITIES_BY_DISTRICT.get(selected_district, [])
        self.job_locality_menu.configure(values=localities)
        if localities:
            self.job_locality_menu.set(localities[0])

    def _handle_create_job(self) -> None:
        """Submits job creation to database layer (strictly validating blacklist)."""
        user = self.app.session.current_user
        if not user:
            return

        title = self.job_title_entry.get().strip()
        category = self.job_category_menu.get().strip()
        district = self.job_district_menu.get().strip()
        locality = self.job_locality_menu.get().strip()
        job_date = self.job_date_entry.get().strip()
        start_time = self.job_start_entry.get().strip()
        end_time = self.job_end_entry.get().strip()
        pay_str = self.job_pay_entry.get().strip()

        if not title:
            self.show_alert("Validation Error", "Please enter a job title.", is_error=True)
            return

        try:
            payment = float(pay_str)
            if payment <= 0:
                raise ValueError()
        except ValueError:
            self.show_alert("Validation Error", "Please enter a valid numeric payment amount greater than 0.", is_error=True)
            return

        try:
            job_id = database.create_job(
                employer_id=user["user_id"],
                title=title,
                category=category,
                district=district,
                locality=locality,
                job_date=job_date,
                start_time=start_time,
                end_time=end_time,
                payment=payment,
            )
            self.show_alert(
                title="Job Published",
                message=f"Job '{title}' was successfully published! Workers in {locality} can now view and apply.",
            )
            # Reset fields
            self.job_title_entry.delete(0, "end")
            self.job_pay_entry.delete(0, "end")
            self.refresh_listings()
            self.tabview.set("  My Listings & Applicants  ")
        except ValueError as e:
            # Backend blacklist rule or validation error caught here
            self.show_alert("Job Posting Rejected", str(e), is_error=True)

    # ==========================================================================
    # TAB 3: DISPUTES & NO-SHOW HISTORY
    # ==========================================================================
    def _build_disputes_tab(self) -> None:
        tab = self.tab_disputes

        self.disputes_scroll = ctk.CTkScrollableFrame(tab, fg_color="transparent")
        self.disputes_scroll.pack(fill="both", expand=True, padx=4, pady=4)

        self.refresh_disputes_tab()

    def refresh_disputes_tab(self) -> None:
        for widget in self.disputes_scroll.winfo_children():
            widget.destroy()

        user = self.app.session.current_user
        if not user:
            return

        complaints = database.get_complaints_by_user(user["user_id"], as_complainant=True)

        ctk.CTkLabel(
            self.disputes_scroll,
            text="Worker No-Show Disputes Lodged by You:",
            font=FONT_SECTION,
            text_color=COLOR_TITLE_TEXT,
        ).pack(anchor="w", padx=12, pady=(12, 6))

        if not complaints:
            empty = ctk.CTkFrame(self.disputes_scroll, fg_color=COLOR_CARD, corner_radius=8)
            empty.pack(fill="x", padx=8, pady=4)
            ctk.CTkLabel(
                empty,
                text="No attendance disputes reported. You can report an accepted worker who failed to show up from 'My Listings'.",
                font=FONT_BODY,
                text_color=COLOR_MUTED_TEXT,
            ).pack(pady=20)
        else:
            for c in complaints:
                self._render_no_show_complaint_card(c)

    def _render_no_show_complaint_card(self, c: Dict[str, Any]) -> None:
        card = ctk.CTkFrame(self.disputes_scroll, fg_color=COLOR_CARD, corner_radius=10, border_width=1, border_color=COLOR_BORDER)
        card.pack(fill="x", padx=8, pady=4)

        box = ctk.CTkFrame(card, fg_color="transparent")
        box.pack(fill="both", expand=True, padx=14, pady=10)

        top = ctk.CTkFrame(box, fg_color="transparent")
        top.pack(fill="x")

        ctk.CTkLabel(top, text=f"Complaint #{c['complaint_id']} — {c['job_title']}", font=FONT_BODY_BOLD).pack(side="left")

        status_colors = {
            "submitted": COLOR_WARNING,
            "under_review": "#0284c7",
            "verified": COLOR_SUCCESS,
            "dismissed": COLOR_MUTED_TEXT[1],
        }
        status_lbl = ctk.CTkLabel(
            top,
            text=f" {c['status'].upper()} ",
            font=FONT_BADGE,
            fg_color=status_colors.get(c["status"], COLOR_SECONDARY),
            text_color="#ffffff",
            corner_radius=6,
        )
        status_lbl.pack(side="right")

        ctk.CTkLabel(
            box,
            text=f"Worker: {c['other_party_name']} (📞 {c['other_party_phone']})  |  Submitted: {c['created_at']}",
            font=FONT_SMALL,
            text_color=COLOR_MUTED_TEXT,
        ).pack(anchor="w", pady=(2, 2))

        ctk.CTkLabel(box, text=f"Incident: {c['details']}", font=FONT_SMALL, wraplength=700, justify="left").pack(anchor="w")

        if c.get("admin_notes"):
            ctk.CTkLabel(
                box,
                text=f"Admin Resolution Note: {c['admin_notes']}",
                font=FONT_SMALL_BOLD,
                text_color=COLOR_PRIMARY,
            ).pack(anchor="w", pady=(4, 0))

    # ==========================================================================
    # MODAL: REPORT WORKER NO-SHOW
    # ==========================================================================
    def _open_no_show_modal(self, job: Dict[str, Any], applicant: Dict[str, Any]) -> None:
        modal = self.show_modal(title="Report Worker No-Show", width=480, height=420)

        frame = ctk.CTkFrame(modal, fg_color=COLOR_CARD, corner_radius=12)
        frame.pack(fill="both", expand=True, padx=16, pady=16)

        ctk.CTkLabel(frame, text="Lodge No-Show Complaint", font=FONT_SECTION).pack(anchor="w", pady=(4, 2))
        ctk.CTkLabel(
            frame,
            text="Admins will review. Verified complaints issue a strike against the worker.",
            font=FONT_SMALL,
            text_color=COLOR_MUTED_TEXT,
        ).pack(anchor="w", pady=(0, 12))

        info = ctk.CTkFrame(frame, fg_color="transparent")
        info.pack(fill="x", pady=(0, 10))

        ctk.CTkLabel(info, text=f"Job: {job['title']}", font=FONT_BODY_BOLD).pack(anchor="w")
        ctk.CTkLabel(info, text=f"Worker: {applicant['worker_name']} (📞 {applicant['worker_phone']})", font=FONT_SMALL).pack(anchor="w")

        ctk.CTkLabel(frame, text="Incident Details", font=FONT_BODY_BOLD).pack(anchor="w", pady=(6, 2))
        details_box = ctk.CTkTextbox(frame, height=110, font=FONT_BODY)
        details_box.pack(fill="x", pady=(0, 12))
        details_box.insert("1.0", "Worker accepted shift but failed to arrive at the designated time without notice.")

        def submit_no_show() -> None:
            details_text = details_box.get("1.0", "end").strip()
            if not details_text:
                self.show_alert("Error", "Please provide details of the no-show incident.", is_error=True)
                return

            user = self.app.session.current_user
            if not user:
                return

            try:
                database.file_complaint(
                    complaint_type="no_show",
                    job_id=job["job_id"],
                    complainant_id=user["user_id"],
                    accused_id=applicant["worker_id"],
                    details=details_text,
                )
                modal.destroy()
                self.show_alert(
                    title="No-Show Reported",
                    message=f"No-show complaint against {applicant['worker_name']} lodged for administrator investigation.",
                )
                self.refresh_disputes_tab()
                self.tabview.set("  No-Show Reports  ")
            except ValueError as e:
                self.show_alert("Submission Failed", str(e), is_error=True)

        btn_box = ctk.CTkFrame(frame, fg_color="transparent")
        btn_box.pack(fill="x", pady=(4, 0))

        ctk.CTkButton(
            btn_box,
            text="Cancel",
            font=FONT_BODY_BOLD,
            fg_color=COLOR_SECONDARY,
            hover_color=COLOR_SECONDARY_HOVER,
            command=modal.destroy,
        ).pack(side="left", expand=True, fill="x", padx=(0, 6))

        ctk.CTkButton(
            btn_box,
            text="Submit Report",
            font=FONT_BODY_BOLD,
            fg_color=COLOR_DANGER,
            hover_color=COLOR_DANGER_HOVER,
            command=submit_no_show,
        ).pack(side="right", expand=True, fill="x", padx=(6, 0))

