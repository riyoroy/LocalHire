"""
Worker View for Local Hire.
Features Job Feed with Haversine distance calculations, filtering, sorting,
application status tracking, strike awareness, and wage-theft dispute reporting.
"""

from typing import Any, Dict, List, Optional
import customtkinter as ctk

import database
from coordinates import calculate_distance, format_distance, JOB_CATEGORIES
from views.base_view import (
    BaseView,
    COLOR_CARD,
    COLOR_CARD_HOVER,
    COLOR_BORDER,
    COLOR_PRIMARY,
    COLOR_PRIMARY_HOVER,
    COLOR_SECONDARY,
    COLOR_SECONDARY_HOVER,
    COLOR_MUTED_TEXT,
    COLOR_TITLE_TEXT,
    COLOR_SUCCESS,
    COLOR_SUCCESS_HOVER,
    COLOR_WARNING,
    COLOR_DANGER,
    COLOR_DANGER_HOVER,
    FONT_TITLE,
    FONT_SECTION,
    FONT_CARD_TITLE,
    FONT_BODY,
    FONT_BODY_BOLD,
    FONT_SMALL,
    FONT_SMALL_BOLD,
    FONT_BADGE,
)


class WorkerView(BaseView):
    """Main dashboard interface for Job Seekers / Workers."""

    def __init__(self, master: Any, app: Any, **kwargs: Any) -> None:
        super().__init__(master, app, **kwargs)
        self.pack(fill="both", expand=True)

        self._build_ui()

    def _build_ui(self) -> None:
        """Builds header, tabs, and content areas."""
        # Top Header
        self.create_header(
            title="Worker Dashboard",
            subtitle="Browse nearby shifts, track applications, and protect your wages.",
        )

        user = self.app.session.current_user
        if not user:
            return

        # Suspension Alert Banner if suspended
        if user.get("is_suspended", 0) == 1:
            susp_frame = ctk.CTkFrame(self, fg_color="#7f1d1d", corner_radius=8, height=44)
            susp_frame.pack(fill="x", padx=16, pady=(0, 8))

            lbl = ctk.CTkLabel(
                susp_frame,
                text="⚠️ ACCOUNT SUSPENDED: You have accumulated 3 active strikes for reported no-shows. "
                     "New job applications are disabled. Contact the administrator for dispute resolution.",
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

        self.tab_feed = self.tabview.add("  Browse Jobs  ")
        self.tab_applications = self.tabview.add("  My Applications  ")
        self.tab_disputes = self.tabview.add("  Disputes & Strikes  ")

        self._build_job_feed_tab()
        self._build_applications_tab()
        self._build_disputes_tab()

    # ==========================================================================
    # TAB 1: BROWSE JOBS (JOB FEED)
    # ==========================================================================
    def _build_job_feed_tab(self) -> None:
        tab = self.tab_feed

        # Filters Bar
        filter_bar = ctk.CTkFrame(tab, fg_color=COLOR_CARD, corner_radius=10, border_width=1, border_color=COLOR_BORDER)
        filter_bar.pack(fill="x", padx=8, pady=(8, 10))

        # Category Filter
        cat_frame = ctk.CTkFrame(filter_bar, fg_color="transparent")
        cat_frame.pack(side="left", padx=10, pady=8)
        ctk.CTkLabel(cat_frame, text="Category", font=FONT_SMALL_BOLD, text_color=COLOR_MUTED_TEXT).pack(anchor="w")
        self.cat_filter = ctk.CTkOptionMenu(
            cat_frame,
            values=["All Categories"] + JOB_CATEGORIES,
            command=lambda _: self.refresh_job_feed(),
            height=32,
            font=FONT_SMALL,
        )
        self.cat_filter.pack()

        # Distance Filter
        dist_frame = ctk.CTkFrame(filter_bar, fg_color="transparent")
        dist_frame.pack(side="left", padx=10, pady=8)
        ctk.CTkLabel(dist_frame, text="Radius", font=FONT_SMALL_BOLD, text_color=COLOR_MUTED_TEXT).pack(anchor="w")
        self.dist_filter = ctk.CTkOptionMenu(
            dist_frame,
            values=["All Distances", "Within 5 km", "Within 10 km", "Within 25 km", "Within 50 km"],
            command=lambda _: self.refresh_job_feed(),
            height=32,
            font=FONT_SMALL,
        )
        self.dist_filter.pack()

        # Sort Filter
        sort_frame = ctk.CTkFrame(filter_bar, fg_color="transparent")
        sort_frame.pack(side="left", padx=10, pady=8)
        ctk.CTkLabel(sort_frame, text="Sort By", font=FONT_SMALL_BOLD, text_color=COLOR_MUTED_TEXT).pack(anchor="w")
        self.sort_filter = ctk.CTkOptionMenu(
            sort_frame,
            values=["Nearest First", "Highest Pay", "Newest First"],
            command=lambda _: self.refresh_job_feed(),
            height=32,
            font=FONT_SMALL,
        )
        self.sort_filter.pack()

        # Refresh Button
        btn_refresh = ctk.CTkButton(
            filter_bar,
            text="🔄 Refresh",
            width=90,
            height=32,
            font=FONT_SMALL_BOLD,
            fg_color=COLOR_SECONDARY,
            hover_color=COLOR_SECONDARY_HOVER,
            command=self.refresh_job_feed,
        )
        btn_refresh.pack(side="right", padx=12, pady=8)

        # Scrollable Feed Container
        self.feed_scroll = ctk.CTkScrollableFrame(tab, fg_color="transparent")
        self.feed_scroll.pack(fill="both", expand=True, padx=4, pady=4)

        self.refresh_job_feed()

    def refresh_job_feed(self) -> None:
        """Fetches open jobs, applies distance calculation and filters, renders job cards."""
        for widget in self.feed_scroll.winfo_children():
            widget.destroy()

        user = self.app.session.current_user
        if not user:
            return

        worker_loc = user.get("locality", "")
        worker_id = user["user_id"]

        # Fetch all open jobs
        jobs = database.get_jobs(status="open")

        # Fetch worker's existing applications to reflect status
        my_apps = database.get_worker_applications(worker_id)
        applied_job_ids = {a["job_id"]: a["status"] for a in my_apps}

        # Calculate distances
        processed_jobs = []
        for job in jobs:
            dist = calculate_distance(worker_loc, job["locality"])
            processed_jobs.append({
                **job,
                "distance_km": dist,
            })

        # Apply Category Filter
        cat_choice = self.cat_filter.get()
        if cat_choice != "All Categories":
            processed_jobs = [j for j in processed_jobs if j["category"] == cat_choice]

        # Apply Distance Filter
        dist_choice = self.dist_filter.get()
        if dist_choice == "Within 5 km":
            processed_jobs = [j for j in processed_jobs if j["distance_km"] is not None and j["distance_km"] <= 5.0]
        elif dist_choice == "Within 10 km":
            processed_jobs = [j for j in processed_jobs if j["distance_km"] is not None and j["distance_km"] <= 10.0]
        elif dist_choice == "Within 25 km":
            processed_jobs = [j for j in processed_jobs if j["distance_km"] is not None and j["distance_km"] <= 25.0]
        elif dist_choice == "Within 50 km":
            processed_jobs = [j for j in processed_jobs if j["distance_km"] is not None and j["distance_km"] <= 50.0]

        # Apply Sorting
        sort_choice = self.sort_filter.get()
        if sort_choice == "Nearest First":
            processed_jobs.sort(key=lambda j: j["distance_km"] if j["distance_km"] is not None else 99999.0)
        elif sort_choice == "Highest Pay":
            processed_jobs.sort(key=lambda j: j["payment"], reverse=True)
        elif sort_choice == "Newest First":
            processed_jobs.sort(key=lambda j: j["job_id"], reverse=True)

        if not processed_jobs:
            empty_box = ctk.CTkFrame(self.feed_scroll, fg_color=COLOR_CARD, corner_radius=12)
            empty_box.pack(fill="x", padx=16, pady=24)
            ctk.CTkLabel(
                empty_box,
                text="No jobs found matching your filters.\nTry selecting 'All Distances' or 'All Categories'.",
                font=FONT_BODY,
                text_color=COLOR_MUTED_TEXT,
            ).pack(pady=24)
            return

        # Render Job Cards
        for job in processed_jobs:
            self._render_job_card(job, applied_status=applied_job_ids.get(job["job_id"]))

    def _render_job_card(self, job: Dict[str, Any], applied_status: Optional[str]) -> None:
        """Renders an individual job card."""
        user = self.app.session.current_user
        is_suspended = bool(user and user.get("is_suspended", 0) == 1)

        card = ctk.CTkFrame(
            self.feed_scroll,
            fg_color=COLOR_CARD,
            corner_radius=12,
            border_width=1,
            border_color=COLOR_BORDER,
        )
        card.pack(fill="x", padx=8, pady=6)

        # Content Grid
        content = ctk.CTkFrame(card, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=16, pady=14)

        # Top row: Title, Category pill, Distance pill
        top_row = ctk.CTkFrame(content, fg_color="transparent")
        top_row.pack(fill="x")

        title_lbl = ctk.CTkLabel(
            top_row,
            text=job["title"],
            font=FONT_CARD_TITLE,
            text_color=COLOR_TITLE_TEXT,
        )
        title_lbl.pack(side="left")

        # Category Badge
        cat_badge = ctk.CTkLabel(
            top_row,
            text=f" {job['category']} ",
            font=FONT_BADGE,
            fg_color=COLOR_SECONDARY,
            text_color="#ffffff",
            corner_radius=6,
        )
        cat_badge.pack(side="left", padx=10)

        # Distance Badge
        dist_km = job.get("distance_km")
        dist_str = format_distance(dist_km)
        dist_badge_color = "#047857" if (dist_km is not None and dist_km <= 10.0) else "#0369a1"
        dist_badge = ctk.CTkLabel(
            top_row,
            text=f" 📍 {dist_str} ",
            font=FONT_BADGE,
            fg_color=dist_badge_color,
            text_color="#ffffff",
            corner_radius=6,
        )
        dist_badge.pack(side="left")

        # Middle row: Employer, Locality, Shift Date & Timing
        mid_row = ctk.CTkFrame(content, fg_color="transparent")
        mid_row.pack(fill="x", pady=(8, 8))

        emp_info = f"Employer: {job['employer_name']}  •  📍 {job['locality']}"
        ctk.CTkLabel(mid_row, text=emp_info, font=FONT_SMALL, text_color=COLOR_MUTED_TEXT).pack(anchor="w")

        timing_info = f"📅 Date: {job['job_date']}  |  🕒 Shift: {job['start_time']} - {job['end_time']}"
        ctk.CTkLabel(mid_row, text=timing_info, font=FONT_SMALL_BOLD, text_color=COLOR_TITLE_TEXT).pack(anchor="w", pady=(2, 0))

        # Bottom row: Payment and Apply Button
        bot_row = ctk.CTkFrame(content, fg_color="transparent")
        bot_row.pack(fill="x", pady=(6, 0))

        pay_lbl = ctk.CTkLabel(
            bot_row,
            text=f"₹{job['payment']:.0f}",
            font=("Segoe UI", 18, "bold"),
            text_color=COLOR_SUCCESS,
        )
        pay_lbl.pack(side="left")

        pay_sub = ctk.CTkLabel(bot_row, text=" / shift", font=FONT_SMALL, text_color=COLOR_MUTED_TEXT)
        pay_sub.pack(side="left", padx=(2, 0), pady=(4, 0))

        # Action Button Handling
        if applied_status:
            # Already applied
            status_colors = {
                "pending": COLOR_WARNING,
                "accepted": COLOR_SUCCESS,
                "rejected": COLOR_DANGER,
                "completed": "#7c3aed",
            }
            btn_text = f"Applied ({applied_status.capitalize()})"
            applied_btn = ctk.CTkButton(
                bot_row,
                text=btn_text,
                font=FONT_SMALL_BOLD,
                width=140,
                height=34,
                fg_color=status_colors.get(applied_status, COLOR_SECONDARY),
                state="disabled",
            )
            applied_btn.pack(side="right")
        elif is_suspended:
            susp_btn = ctk.CTkButton(
                bot_row,
                text="Suspended (Apply Disabled)",
                font=FONT_SMALL_BOLD,
                width=180,
                height=34,
                fg_color=COLOR_DANGER,
                hover_color=COLOR_DANGER,
                state="disabled",
            )
            susp_btn.pack(side="right")
        else:
            apply_btn = ctk.CTkButton(
                bot_row,
                text="Apply Now",
                font=FONT_BODY_BOLD,
                width=130,
                height=34,
                fg_color=COLOR_PRIMARY,
                hover_color=COLOR_PRIMARY_HOVER,
                command=lambda jid=job["job_id"], jtitle=job["title"]: self._handle_apply(jid, jtitle),
            )
            apply_btn.pack(side="right")

    def _handle_apply(self, job_id: int, job_title: str) -> None:
        """Handles worker application submission."""
        user = self.app.session.current_user
        if not user:
            return

        try:
            database.apply_for_job(job_id=job_id, worker_id=user["user_id"])
            self.show_alert(
                title="Application Sent",
                message=f"You have successfully applied for '{job_title}'. Track status in 'My Applications'.",
            )
            self.refresh_job_feed()
            self.refresh_applications()
        except ValueError as e:
            self.show_alert(title="Application Blocked", message=str(e), is_error=True)
            self.app.session.refresh()
            self.refresh_job_feed()

    # ==========================================================================
    # TAB 2: MY APPLICATIONS
    # ==========================================================================
    def _build_applications_tab(self) -> None:
        tab = self.tab_applications

        # Top Bar
        bar = ctk.CTkFrame(tab, fg_color="transparent")
        bar.pack(fill="x", padx=8, pady=(8, 10))

        ctk.CTkLabel(
            bar,
            text="Track your active and past job applications.",
            font=FONT_BODY,
            text_color=COLOR_MUTED_TEXT,
        ).pack(side="left")

        ctk.CTkButton(
            bar,
            text="🔄 Refresh",
            width=90,
            height=32,
            font=FONT_SMALL_BOLD,
            fg_color=COLOR_SECONDARY,
            hover_color=COLOR_SECONDARY_HOVER,
            command=self.refresh_applications,
        ).pack(side="right")

        self.apps_scroll = ctk.CTkScrollableFrame(tab, fg_color="transparent")
        self.apps_scroll.pack(fill="both", expand=True, padx=4, pady=4)

        self.refresh_applications()

    def refresh_applications(self) -> None:
        """Fetches and displays applications for this worker."""
        for widget in self.apps_scroll.winfo_children():
            widget.destroy()

        user = self.app.session.current_user
        if not user:
            return

        applications = database.get_worker_applications(user["user_id"])

        if not applications:
            empty = ctk.CTkFrame(self.apps_scroll, fg_color=COLOR_CARD, corner_radius=12)
            empty.pack(fill="x", padx=16, pady=24)
            ctk.CTkLabel(
                empty,
                text="You have not applied for any jobs yet.\nBrowse open positions in 'Browse Jobs'!",
                font=FONT_BODY,
                text_color=COLOR_MUTED_TEXT,
            ).pack(pady=24)
            return

        for app_row in applications:
            self._render_application_card(app_row)

    def _render_application_card(self, app_row: Dict[str, Any]) -> None:
        card = ctk.CTkFrame(
            self.apps_scroll,
            fg_color=COLOR_CARD,
            corner_radius=12,
            border_width=1,
            border_color=COLOR_BORDER,
        )
        card.pack(fill="x", padx=8, pady=6)

        content = ctk.CTkFrame(card, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=16, pady=12)

        # Header: Job title and status badge
        top_row = ctk.CTkFrame(content, fg_color="transparent")
        top_row.pack(fill="x")

        ctk.CTkLabel(top_row, text=app_row["job_title"], font=FONT_CARD_TITLE, text_color=COLOR_TITLE_TEXT).pack(side="left")

        status = app_row["status"]
        status_colors = {
            "pending": COLOR_WARNING,
            "accepted": COLOR_SUCCESS,
            "rejected": COLOR_DANGER,
            "completed": "#7c3aed",
        }
        badge = ctk.CTkLabel(
            top_row,
            text=f" {status.upper()} ",
            font=FONT_BADGE,
            fg_color=status_colors.get(status, COLOR_SECONDARY),
            text_color="#ffffff",
            corner_radius=6,
        )
        badge.pack(side="right")

        # Details
        info_row = ctk.CTkFrame(content, fg_color="transparent")
        info_row.pack(fill="x", pady=(6, 4))

        emp_contact = f"Employer: {app_row['employer_name']}"
        if status in ("accepted", "completed"):
            emp_contact += f"  (📞 Phone: {app_row['employer_phone']})"

        ctk.CTkLabel(info_row, text=emp_contact, font=FONT_SMALL_BOLD, text_color=COLOR_TITLE_TEXT).pack(anchor="w")

        timing = f"📅 {app_row['job_date']}  |  🕒 {app_row['start_time']} - {app_row['end_time']}  |  📍 {app_row['job_locality']}"
        ctk.CTkLabel(info_row, text=timing, font=FONT_SMALL, text_color=COLOR_MUTED_TEXT).pack(anchor="w", pady=(2, 0))

        # Bottom row: Payment and Dispute Action Button
        bot_row = ctk.CTkFrame(content, fg_color="transparent")
        bot_row.pack(fill="x", pady=(6, 0))

        ctk.CTkLabel(
            bot_row,
            text=f"Agreed Payment: ₹{app_row['payment']:.0f}",
            font=FONT_BODY_BOLD,
            text_color=COLOR_SUCCESS,
        ).pack(side="left")

        # If job is accepted or completed, allow filing wage dispute
        if status in ("accepted", "completed"):
            dispute_btn = ctk.CTkButton(
                bot_row,
                text="Report Non-Payment",
                font=FONT_SMALL_BOLD,
                width=160,
                height=32,
                fg_color=COLOR_DANGER,
                hover_color=COLOR_DANGER_HOVER,
                command=lambda: self._open_dispute_modal(app_row),
            )
            dispute_btn.pack(side="right")

    # ==========================================================================
    # TAB 3: DISPUTES & STRIKES
    # ==========================================================================
    def _build_disputes_tab(self) -> None:
        tab = self.tab_disputes

        self.disputes_scroll = ctk.CTkScrollableFrame(tab, fg_color="transparent")
        self.disputes_scroll.pack(fill="both", expand=True, padx=4, pady=4)

        self.refresh_disputes_tab()

    def refresh_disputes_tab(self) -> None:
        """Refreshes worker strikes summary and history of lodged wage complaints."""
        for widget in self.disputes_scroll.winfo_children():
            widget.destroy()

        user = self.app.session.current_user
        if not user:
            return

        worker_id = user["user_id"]

        # Fetch strikes for this worker
        strikes = database.get_worker_strikes(worker_id)
        active_strikes = [s for s in strikes if s["is_active"] == 1]
        active_count = len(active_strikes)

        # Overview Banner
        banner = ctk.CTkFrame(self.disputes_scroll, fg_color=COLOR_CARD, corner_radius=12, border_width=1, border_color=COLOR_BORDER)
        banner.pack(fill="x", padx=8, pady=(8, 12))

        b_content = ctk.CTkFrame(banner, fg_color="transparent")
        b_content.pack(fill="x", padx=16, pady=14)

        ctk.CTkLabel(b_content, text="Account Standing & Strike Record", font=FONT_SECTION, text_color=COLOR_TITLE_TEXT).pack(anchor="w")

        status_text = f"Active Strikes: {active_count} / 3"
        status_color = COLOR_SUCCESS if active_count == 0 else (COLOR_WARNING if active_count < 3 else COLOR_DANGER)
        ctk.CTkLabel(b_content, text=status_text, font=("Segoe UI", 16, "bold"), text_color=status_color).pack(anchor="w", pady=(4, 2))

        rule_note = "Rule: Accumulating 3 active strikes for verified employer no-shows automatically suspends your account."
        ctk.CTkLabel(b_content, text=rule_note, font=FONT_SMALL, text_color=COLOR_MUTED_TEXT).pack(anchor="w")

        # Strikes List
        if active_strikes:
            ctk.CTkLabel(self.disputes_scroll, text="Active Strikes Issued:", font=FONT_BODY_BOLD, text_color=COLOR_DANGER).pack(anchor="w", padx=12, pady=(10, 4))
            for st in active_strikes:
                s_card = ctk.CTkFrame(self.disputes_scroll, fg_color=COLOR_CARD, corner_radius=8, border_width=1, border_color=COLOR_DANGER)
                s_card.pack(fill="x", padx=8, pady=4)
                s_box = ctk.CTkFrame(s_card, fg_color="transparent")
                s_box.pack(fill="x", padx=12, pady=10)
                ctk.CTkLabel(s_box, text=f"Strike #{st['strike_id']} — Job: {st['job_title']}", font=FONT_BODY_BOLD).pack(anchor="w")
                ctk.CTkLabel(s_box, text=f"Reason: {st['reason']}  |  Issued: {st['issued_at']}", font=FONT_SMALL, text_color=COLOR_MUTED_TEXT).pack(anchor="w")

        # Lodged Complaints Section
        complaints = database.get_complaints_by_user(worker_id, as_complainant=True)

        ctk.CTkLabel(
            self.disputes_scroll,
            text="Wage-Theft Disputes Lodged by You:",
            font=FONT_SECTION,
            text_color=COLOR_TITLE_TEXT,
        ).pack(anchor="w", padx=12, pady=(16, 6))

        if not complaints:
            empty = ctk.CTkFrame(self.disputes_scroll, fg_color=COLOR_CARD, corner_radius=8)
            empty.pack(fill="x", padx=8, pady=4)
            ctk.CTkLabel(
                empty,
                text="No wage disputes reported. You can lodge a non-payment report from 'My Applications'.",
                font=FONT_BODY,
                text_color=COLOR_MUTED_TEXT,
            ).pack(pady=16)
        else:
            for c in complaints:
                self._render_complaint_card(c)

    def _render_complaint_card(self, c: Dict[str, Any]) -> None:
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
            text=f"Employer: {c['other_party_name']}  |  Agreed Pay: ₹{c['agreed_payment']:.0f}  |  Submitted: {c['created_at']}",
            font=FONT_SMALL,
            text_color=COLOR_MUTED_TEXT,
        ).pack(anchor="w", pady=(2, 2))

        ctk.CTkLabel(
            box,
            text=f"Details: {c['details']}",
            font=FONT_SMALL,
            wraplength=700,
            justify="left",
        ).pack(anchor="w")

        if c.get("admin_notes"):
            ctk.CTkLabel(
                box,
                text=f"Admin Resolution Note: {c['admin_notes']}",
                font=FONT_SMALL_BOLD,
                text_color=COLOR_PRIMARY,
            ).pack(anchor="w", pady=(4, 0))

    # ==========================================================================
    # MODAL: REPORT NON-PAYMENT
    # ==========================================================================
    def _open_dispute_modal(self, app_row: Dict[str, Any]) -> None:
        """Opens modal dialog for reporting wage non-payment."""
        modal = self.show_modal(title="Report Non-Payment", width=480, height=440)

        frame = ctk.CTkFrame(modal, fg_color=COLOR_CARD, corner_radius=12)
        frame.pack(fill="both", expand=True, padx=16, pady=16)

        ctk.CTkLabel(frame, text="Lodge Wage-Theft Complaint", font=FONT_SECTION).pack(anchor="w", pady=(4, 2))
        ctk.CTkLabel(
            frame,
            text="Admins will investigate. Verified non-payment blacklists the employer.",
            font=FONT_SMALL,
            text_color=COLOR_MUTED_TEXT,
        ).pack(anchor="w", pady=(0, 12))

        # Job Summary info
        info_frame = ctk.CTkFrame(frame, fg_color="transparent")
        info_frame.pack(fill="x", pady=(0, 10))

        ctk.CTkLabel(info_frame, text=f"Job: {app_row['job_title']}", font=FONT_BODY_BOLD).pack(anchor="w")
        ctk.CTkLabel(info_frame, text=f"Employer: {app_row['employer_name']}", font=FONT_SMALL).pack(anchor="w")
        ctk.CTkLabel(
            info_frame,
            text=f"Agreed Payment: ₹{app_row['payment']:.0f}",
            font=FONT_BODY_BOLD,
            text_color=COLOR_SUCCESS,
        ).pack(anchor="w")

        ctk.CTkLabel(frame, text="Incident Details / Statement", font=FONT_BODY_BOLD).pack(anchor="w", pady=(6, 2))
        details_box = ctk.CTkTextbox(frame, height=120, font=FONT_BODY)
        details_box.pack(fill="x", pady=(0, 12))
        details_box.insert("1.0", "Completed shift on scheduled date but employer refused payment without cause.")

        def submit_complaint() -> None:
            details_text = details_box.get("1.0", "end").strip()
            if not details_text:
                self.show_alert("Error", "Please provide details of the non-payment.", is_error=True)
                return

            user = self.app.session.current_user
            if not user:
                return

            try:
                database.file_complaint(
                    complaint_type="non_payment",
                    job_id=app_row["job_id"],
                    complainant_id=user["user_id"],
                    accused_id=app_row["employer_id"],
                    details=details_text,
                    agreed_payment=float(app_row["payment"]),
                )
                modal.destroy()
                self.show_alert(
                    title="Complaint Submitted",
                    message="Your wage-theft complaint has been lodged and sent to the administrator queue.",
                )
                self.refresh_disputes_tab()
                self.tabview.set("  Disputes & Strikes  ")
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
            text="Submit Dispute",
            font=FONT_BODY_BOLD,
            fg_color=COLOR_DANGER,
            hover_color=COLOR_DANGER_HOVER,
            command=submit_complaint,
        ).pack(side="right", expand=True, fill="x", padx=(6, 0))
