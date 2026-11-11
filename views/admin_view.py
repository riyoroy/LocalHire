"""
Administrator Console View for Local Hire.
Features System Metric Cards, Wage Disputes Review with Employer Blacklisting,
No-Show Disputes Review with Worker Strike Issuance, and Strike Reversals.
"""

from typing import Any, Dict, List, Optional
import customtkinter as ctk

import database
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


class AdminView(BaseView):
    """Console interface for System Administrators."""

    def __init__(self, master: Any, app: Any, **kwargs: Any) -> None:
        super().__init__(master, app, **kwargs)
        self.pack(fill="both", expand=True)

        self._build_ui()

    def _build_ui(self) -> None:
        """Constructs admin header, system metrics cards, and tabview navigation."""
        self.create_header(
            title="Administrator Console",
            subtitle="Oversee platform health, adjudicate bilateral disputes, and enforce sanctions.",
        )

        # Top System Metrics Dashboard
        self.metrics_container = ctk.CTkFrame(self, fg_color="transparent")
        self.metrics_container.pack(fill="x", padx=16, pady=(0, 10))
        self._render_metrics()

        # Tab Navigation
        self.tabview = ctk.CTkTabview(
            self,
            segmented_button_selected_color=COLOR_PRIMARY,
            segmented_button_selected_hover_color=COLOR_PRIMARY_HOVER,
        )
        self.tabview.pack(fill="both", expand=True, padx=16, pady=(0, 12))

        self.tab_wage = self.tabview.add("  Wage Disputes (Worker vs Employer)  ")
        self.tab_noshow = self.tabview.add("  No-Show Disputes (Employer vs Worker)  ")
        self.tab_strikes = self.tabview.add("  Strikes & Sanctions Console  ")
        self.tab_users = self.tabview.add("  User Directory  ")

        self._build_wage_disputes_tab()
        self._build_noshow_disputes_tab()
        self._build_strikes_tab()
        self._build_users_tab()

    # ==========================================================================
    # METRICS DASHBOARD
    # ==========================================================================
    def _render_metrics(self) -> None:
        for w in self.metrics_container.winfo_children():
            w.destroy()

        metrics = database.get_admin_metrics()

        cards_data = [
            (
                "Platform Users",
                f"{metrics['total_workers']} Workers  |  {metrics['total_employers']} Employers",
                "#0284c7",
            ),
            (
                "Job Listings",
                f"{metrics['open_jobs']} Open  |  {metrics['total_jobs']} Total",
                "#059669",
            ),
            (
                "Pending Disputes",
                f"{metrics['pending_wage_disputes']} Wage  |  {metrics['pending_no_show_disputes']} No-Show",
                "#d97706",
            ),
            (
                "Sanctions & Strikes",
                f"{metrics['blacklisted_employers']} Blacklisted  |  {metrics['suspended_workers']} Suspended  |  {metrics['active_strikes']} Strikes",
                "#dc2626",
            ),
        ]

        grid = ctk.CTkFrame(self.metrics_container, fg_color="transparent")
        grid.pack(fill="x")

        for idx, (title, value, color) in enumerate(cards_data):
            c = ctk.CTkFrame(grid, fg_color=COLOR_CARD, corner_radius=10, border_width=1, border_color=COLOR_BORDER)
            c.pack(side="left", fill="x", expand=True, padx=(0 if idx == 0 else 6, 0))

            pad = ctk.CTkFrame(c, fg_color="transparent")
            pad.pack(fill="both", expand=True, padx=12, pady=10)

            ctk.CTkLabel(pad, text=title, font=FONT_SMALL_BOLD, text_color=COLOR_MUTED_TEXT).pack(anchor="w")
            ctk.CTkLabel(pad, text=value, font=FONT_BODY_BOLD, text_color=color).pack(anchor="w", pady=(2, 0))

    def refresh_all(self) -> None:
        """Refreshes metrics and all sub-views."""
        self._render_metrics()
        self.refresh_wage_disputes()
        self.refresh_noshow_disputes()
        self.refresh_strikes()
        self.refresh_users()

    # ==========================================================================
    # TAB 1: WAGE DISPUTES REVIEW
    # ==========================================================================
    def _build_wage_disputes_tab(self) -> None:
        tab = self.tab_wage

        top = ctk.CTkFrame(tab, fg_color="transparent")
        top.pack(fill="x", padx=8, pady=(8, 10))

        ctk.CTkLabel(
            top,
            text="Worker Non-Payment Claims: Verifying a wage theft complaint blacklists the employer permanently.",
            font=FONT_BODY,
            text_color=COLOR_MUTED_TEXT,
        ).pack(side="left")

        ctk.CTkButton(
            top,
            text="🔄 Refresh",
            width=90,
            height=32,
            font=FONT_SMALL_BOLD,
            fg_color=COLOR_SECONDARY,
            hover_color=COLOR_SECONDARY_HOVER,
            command=self.refresh_wage_disputes,
        ).pack(side="right")

        self.wage_scroll = ctk.CTkScrollableFrame(tab, fg_color="transparent")
        self.wage_scroll.pack(fill="both", expand=True, padx=4, pady=4)

        self.refresh_wage_disputes()

    def refresh_wage_disputes(self) -> None:
        for w in self.wage_scroll.winfo_children():
            w.destroy()

        complaints = database.get_all_complaints(complaint_type="non_payment")

        if not complaints:
            empty = ctk.CTkFrame(self.wage_scroll, fg_color=COLOR_CARD, corner_radius=12)
            empty.pack(fill="x", padx=16, pady=24)
            ctk.CTkLabel(
                empty,
                text="No wage-theft complaints have been submitted.",
                font=FONT_BODY,
                text_color=COLOR_MUTED_TEXT,
            ).pack(pady=20)
            return

        for c in complaints:
            self._render_wage_complaint_card(c)

    def _render_wage_complaint_card(self, c: Dict[str, Any]) -> None:
        card = ctk.CTkFrame(self.wage_scroll, fg_color=COLOR_CARD, corner_radius=12, border_width=1, border_color=COLOR_BORDER)
        card.pack(fill="x", padx=8, pady=8)

        content = ctk.CTkFrame(card, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=16, pady=12)

        # Header: ID, Title, Status
        top = ctk.CTkFrame(content, fg_color="transparent")
        top.pack(fill="x")

        ctk.CTkLabel(top, text=f"Wage Dispute #{c['complaint_id']} — Job: {c['job_title']}", font=FONT_CARD_TITLE, text_color=COLOR_TITLE_TEXT).pack(side="left")

        status = c["status"]
        status_colors = {
            "submitted": COLOR_WARNING,
            "under_review": "#0284c7",
            "verified": COLOR_DANGER,
            "dismissed": COLOR_MUTED_TEXT[1],
        }
        ctk.CTkLabel(
            top,
            text=f" {status.upper()} ",
            font=FONT_BADGE,
            fg_color=status_colors.get(status, COLOR_SECONDARY),
            text_color="#ffffff",
            corner_radius=6,
        ).pack(side="right")

        # Complainant vs Accused
        parties = ctk.CTkFrame(content, fg_color="transparent")
        parties.pack(fill="x", pady=(6, 4))

        comp_txt = f"Complainant (Worker): {c['complainant_name']} (📞 {c['complainant_phone']})"
        acc_txt = f"Accused (Employer): {c['accused_name']} (📞 {c['accused_phone']})"
        if c.get("accused_is_blacklisted", 0) == 1:
            acc_txt += " [BLACKLISTED]"

        ctk.CTkLabel(parties, text=comp_txt, font=FONT_BODY_BOLD, text_color="#059669").pack(anchor="w")
        ctk.CTkLabel(parties, text=acc_txt, font=FONT_BODY_BOLD, text_color=COLOR_DANGER).pack(anchor="w", pady=(1, 0))

        # Job specs & Agreed payment
        specs = f"Agreed Payment: ₹{c['agreed_payment']:.0f}  |  Job Locality: {c['job_locality']}  |  Filed: {c['created_at']}"
        ctk.CTkLabel(content, text=specs, font=FONT_SMALL, text_color=COLOR_MUTED_TEXT).pack(anchor="w", pady=(4, 2))

        # Statement
        stmt_frame = ctk.CTkFrame(content, fg_color=("rgba(0,0,0,0.03)", "rgba(255,255,255,0.04)"), corner_radius=6)
        stmt_frame.pack(fill="x", pady=(4, 8))
        ctk.CTkLabel(stmt_frame, text=f"Statement: \"{c['details']}\"", font=FONT_SMALL, wraplength=720, justify="left").pack(anchor="w", padx=10, pady=8)

        # Admin Actions
        if status in ("submitted", "under_review"):
            notes_frame = ctk.CTkFrame(content, fg_color="transparent")
            notes_frame.pack(fill="x", pady=(4, 0))

            notes_entry = ctk.CTkEntry(notes_frame, placeholder_text="Enter admin investigation notes...", height=32, font=FONT_SMALL)
            notes_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))

            # Dismiss Button
            ctk.CTkButton(
                notes_frame,
                text="Dismiss",
                font=FONT_SMALL_BOLD,
                width=80,
                height=32,
                fg_color=COLOR_SECONDARY,
                hover_color=COLOR_SECONDARY_HOVER,
                command=lambda cid=c["complaint_id"], ne=notes_entry: self._adjudicate_wage(cid, "dismissed", ne.get()),
            ).pack(side="left", padx=4)

            # Verify & Blacklist Employer Button
            ctk.CTkButton(
                notes_frame,
                text="Verify & Blacklist Employer",
                font=FONT_SMALL_BOLD,
                width=190,
                height=32,
                fg_color=COLOR_DANGER,
                hover_color=COLOR_DANGER_HOVER,
                command=lambda cid=c["complaint_id"], ne=notes_entry: self._adjudicate_wage(cid, "verified", ne.get()),
            ).pack(side="left", padx=4)

        else:
            if c.get("admin_notes"):
                ctk.CTkLabel(
                    content,
                    text=f"Resolution: {c['admin_notes']} (Reviewed: {c.get('reviewed_at', 'N/A')})",
                    font=FONT_SMALL_BOLD,
                    text_color=COLOR_PRIMARY,
                ).pack(anchor="w", pady=(2, 0))

    def _adjudicate_wage(self, complaint_id: int, decision: str, notes: str) -> None:
        user = self.app.session.current_user
        if not user:
            return

        try:
            res = database.review_complaint(
                complaint_id=complaint_id,
                new_status=decision,
                admin_id=user["user_id"],
                admin_notes=notes,
            )
            msg = f"Wage dispute #{complaint_id} marked as '{decision}'."
            if res.get("employer_blacklisted"):
                msg += "\nEmployer has been immediately BLACKLISTED and barred from posting jobs."

            self.show_alert("Dispute Adjudicated", msg)
            self.refresh_all()
        except ValueError as e:
            self.show_alert("Error", str(e), is_error=True)

    # ==========================================================================
    # TAB 2: NO-SHOW DISPUTES REVIEW
    # ==========================================================================
    def _build_noshow_disputes_tab(self) -> None:
        tab = self.tab_noshow

        top = ctk.CTkFrame(tab, fg_color="transparent")
        top.pack(fill="x", padx=8, pady=(8, 10))

        ctk.CTkLabel(
            top,
            text="Worker No-Show Claims: Verifying a no-show complaint issues an active strike against the worker. 3 strikes suspends the worker.",
            font=FONT_BODY,
            text_color=COLOR_MUTED_TEXT,
        ).pack(side="left")

        ctk.CTkButton(
            top,
            text="🔄 Refresh",
            width=90,
            height=32,
            font=FONT_SMALL_BOLD,
            fg_color=COLOR_SECONDARY,
            hover_color=COLOR_SECONDARY_HOVER,
            command=self.refresh_noshow_disputes,
        ).pack(side="right")

        self.noshow_scroll = ctk.CTkScrollableFrame(tab, fg_color="transparent")
        self.noshow_scroll.pack(fill="both", expand=True, padx=4, pady=4)

        self.refresh_noshow_disputes()

    def refresh_noshow_disputes(self) -> None:
        for w in self.noshow_scroll.winfo_children():
            w.destroy()

        complaints = database.get_all_complaints(complaint_type="no_show")

        if not complaints:
            empty = ctk.CTkFrame(self.noshow_scroll, fg_color=COLOR_CARD, corner_radius=12)
            empty.pack(fill="x", padx=16, pady=24)
            ctk.CTkLabel(
                empty,
                text="No worker no-show disputes have been submitted.",
                font=FONT_BODY,
                text_color=COLOR_MUTED_TEXT,
            ).pack(pady=20)
            return

        for c in complaints:
            self._render_noshow_complaint_card(c)

    def _render_noshow_complaint_card(self, c: Dict[str, Any]) -> None:
        card = ctk.CTkFrame(self.noshow_scroll, fg_color=COLOR_CARD, corner_radius=12, border_width=1, border_color=COLOR_BORDER)
        card.pack(fill="x", padx=8, pady=8)

        content = ctk.CTkFrame(card, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=16, pady=12)

        # Top row
        top = ctk.CTkFrame(content, fg_color="transparent")
        top.pack(fill="x")

        ctk.CTkLabel(top, text=f"No-Show Dispute #{c['complaint_id']} — Job: {c['job_title']}", font=FONT_CARD_TITLE, text_color=COLOR_TITLE_TEXT).pack(side="left")

        status = c["status"]
        status_colors = {
            "submitted": COLOR_WARNING,
            "under_review": "#0284c7",
            "verified": COLOR_DANGER,
            "dismissed": COLOR_MUTED_TEXT[1],
        }
        ctk.CTkLabel(
            top,
            text=f" {status.upper()} ",
            font=FONT_BADGE,
            fg_color=status_colors.get(status, COLOR_SECONDARY),
            text_color="#ffffff",
            corner_radius=6,
        ).pack(side="right")

        # Complainant vs Accused
        parties = ctk.CTkFrame(content, fg_color="transparent")
        parties.pack(fill="x", pady=(6, 4))

        comp_txt = f"Complainant (Employer): {c['complainant_name']} (📞 {c['complainant_phone']})"
        acc_txt = f"Accused (Worker): {c['accused_name']} (📞 {c['accused_phone']})"
        if c.get("accused_is_suspended", 0) == 1:
            acc_txt += " [SUSPENDED]"

        ctk.CTkLabel(parties, text=comp_txt, font=FONT_BODY_BOLD, text_color="#0284c7").pack(anchor="w")
        ctk.CTkLabel(parties, text=acc_txt, font=FONT_BODY_BOLD, text_color=COLOR_DANGER).pack(anchor="w", pady=(1, 0))

        # Statement
        stmt_frame = ctk.CTkFrame(content, fg_color=("rgba(0,0,0,0.03)", "rgba(255,255,255,0.04)"), corner_radius=6)
        stmt_frame.pack(fill="x", pady=(4, 8))
        ctk.CTkLabel(stmt_frame, text=f"Statement: \"{c['details']}\"", font=FONT_SMALL, wraplength=720, justify="left").pack(anchor="w", padx=10, pady=8)

        # Action Buttons
        if status in ("submitted", "under_review"):
            notes_frame = ctk.CTkFrame(content, fg_color="transparent")
            notes_frame.pack(fill="x", pady=(4, 0))

            notes_entry = ctk.CTkEntry(notes_frame, placeholder_text="Enter admin investigation notes...", height=32, font=FONT_SMALL)
            notes_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))

            ctk.CTkButton(
                notes_frame,
                text="Dismiss",
                font=FONT_SMALL_BOLD,
                width=80,
                height=32,
                fg_color=COLOR_SECONDARY,
                hover_color=COLOR_SECONDARY_HOVER,
                command=lambda cid=c["complaint_id"], ne=notes_entry: self._adjudicate_noshow(cid, "dismissed", ne.get()),
            ).pack(side="left", padx=4)

            ctk.CTkButton(
                notes_frame,
                text="Verify & Issue Strike",
                font=FONT_SMALL_BOLD,
                width=170,
                height=32,
                fg_color=COLOR_DANGER,
                hover_color=COLOR_DANGER_HOVER,
                command=lambda cid=c["complaint_id"], ne=notes_entry: self._adjudicate_noshow(cid, "verified", ne.get()),
            ).pack(side="left", padx=4)

        else:
            if c.get("admin_notes"):
                ctk.CTkLabel(
                    content,
                    text=f"Resolution: {c['admin_notes']} (Reviewed: {c.get('reviewed_at', 'N/A')})",
                    font=FONT_SMALL_BOLD,
                    text_color=COLOR_PRIMARY,
                ).pack(anchor="w", pady=(2, 0))

    def _adjudicate_noshow(self, complaint_id: int, decision: str, notes: str) -> None:
        user = self.app.session.current_user
        if not user:
            return

        try:
            res = database.review_complaint(
                complaint_id=complaint_id,
                new_status=decision,
                admin_id=user["user_id"],
                admin_notes=notes,
            )
            msg = f"No-show dispute #{complaint_id} marked as '{decision}'."
            if res.get("strike_issued"):
                msg += f"\nStrike issued against worker! Worker now has {res['active_strikes']} active strike(s)."
            if res.get("worker_suspended"):
                msg += "\n⚠️ Worker accumulated >= 3 strikes and has been AUTOMATICALLY SUSPENDED from applying for jobs."

            self.show_alert("Dispute Adjudicated", msg)
            self.refresh_all()
        except ValueError as e:
            self.show_alert("Error", str(e), is_error=True)

    # ==========================================================================
    # TAB 3: STRIKES & SANCTIONS CONSOLE
    # ==========================================================================
    def _build_strikes_tab(self) -> None:
        tab = self.tab_strikes

        top = ctk.CTkFrame(tab, fg_color="transparent")
        top.pack(fill="x", padx=8, pady=(8, 10))

        ctk.CTkLabel(
            top,
            text="Worker Strikes Management: Admins can reverse strikes. If active strikes drop below 3, suspension clears automatically.",
            font=FONT_BODY,
            text_color=COLOR_MUTED_TEXT,
        ).pack(side="left")

        ctk.CTkButton(
            top,
            text="🔄 Refresh",
            width=90,
            height=32,
            font=FONT_SMALL_BOLD,
            fg_color=COLOR_SECONDARY,
            hover_color=COLOR_SECONDARY_HOVER,
            command=self.refresh_strikes,
        ).pack(side="right")

        self.strikes_scroll = ctk.CTkScrollableFrame(tab, fg_color="transparent")
        self.strikes_scroll.pack(fill="both", expand=True, padx=4, pady=4)

        self.refresh_strikes()

    def refresh_strikes(self) -> None:
        for w in self.strikes_scroll.winfo_children():
            w.destroy()

        strikes = database.get_all_strikes()

        if not strikes:
            empty = ctk.CTkFrame(self.strikes_scroll, fg_color=COLOR_CARD, corner_radius=12)
            empty.pack(fill="x", padx=16, pady=24)
            ctk.CTkLabel(
                empty,
                text="No strikes have been recorded in the platform.",
                font=FONT_BODY,
                text_color=COLOR_MUTED_TEXT,
            ).pack(pady=20)
            return

        for st in strikes:
            self._render_strike_card(st)

    def _render_strike_card(self, st: Dict[str, Any]) -> None:
        card = ctk.CTkFrame(self.strikes_scroll, fg_color=COLOR_CARD, corner_radius=12, border_width=1, border_color=COLOR_BORDER)
        card.pack(fill="x", padx=8, pady=6)

        box = ctk.CTkFrame(card, fg_color="transparent")
        box.pack(fill="both", expand=True, padx=16, pady=12)

        top = ctk.CTkFrame(box, fg_color="transparent")
        top.pack(fill="x")

        is_active = st["is_active"] == 1
        status_text = "ACTIVE STRIKE" if is_active else "REVERSED"
        status_color = COLOR_DANGER if is_active else COLOR_MUTED_TEXT[1]

        title_text = f"Strike #{st['strike_id']} — Worker: {st['worker_name']} (📞 {st['worker_phone']})"
        ctk.CTkLabel(top, text=title_text, font=FONT_BODY_BOLD, text_color=COLOR_TITLE_TEXT).pack(side="left")

        ctk.CTkLabel(
            top,
            text=f" {status_text} ",
            font=FONT_BADGE,
            fg_color=status_color,
            text_color="#ffffff",
            corner_radius=6,
        ).pack(side="right")

        # Details
        info = f"Job: {st['job_title']}  |  Reason: {st['reason']}  |  Issued: {st['issued_at']}"
        ctk.CTkLabel(box, text=info, font=FONT_SMALL, text_color=COLOR_MUTED_TEXT).pack(anchor="w", pady=(4, 6))

        # Reversal Action
        if is_active:
            bot = ctk.CTkFrame(box, fg_color="transparent")
            bot.pack(fill="x", pady=(4, 0))

            susp_status = "⚠️ Worker is currently SUSPENDED" if st.get("worker_is_suspended", 0) == 1 else "Worker is Active"
            ctk.CTkLabel(bot, text=susp_status, font=FONT_SMALL_BOLD, text_color=COLOR_DANGER if st.get("worker_is_suspended", 0) == 1 else COLOR_SUCCESS).pack(side="left")

            ctk.CTkButton(
                bot,
                text="Reverse Strike",
                font=FONT_SMALL_BOLD,
                width=120,
                height=30,
                fg_color=COLOR_PRIMARY,
                hover_color=COLOR_PRIMARY_HOVER,
                command=lambda sid=st["strike_id"]: self._handle_reverse_strike(sid),
            ).pack(side="right")

    def _handle_reverse_strike(self, strike_id: int) -> None:
        user = self.app.session.current_user
        if not user:
            return

        try:
            res = database.reverse_strike(strike_id, admin_id=user["user_id"])
            msg = f"Strike #{strike_id} was successfully reversed."
            msg += f"\nWorker's remaining active strikes: {res['remaining_active_strikes']}."
            if res.get("suspension_cleared"):
                msg += "\n🎉 Worker suspension was AUTOMATICALLY CLEARED (Active strikes < 3)."

            self.show_alert("Strike Reversed", msg)
            self.refresh_all()
        except ValueError as e:
            self.show_alert("Error", str(e), is_error=True)

    # ==========================================================================
    # TAB 4: USER DIRECTORY
    # ==========================================================================
    def _build_users_tab(self) -> None:
        tab = self.tab_users

        top = ctk.CTkFrame(tab, fg_color="transparent")
        top.pack(fill="x", padx=8, pady=(8, 10))

        ctk.CTkLabel(
            top,
            text="Complete Platform User Directory and Account Status.",
            font=FONT_BODY,
            text_color=COLOR_MUTED_TEXT,
        ).pack(side="left")

        ctk.CTkButton(
            top,
            text="🔄 Refresh",
            width=90,
            height=32,
            font=FONT_SMALL_BOLD,
            fg_color=COLOR_SECONDARY,
            hover_color=COLOR_SECONDARY_HOVER,
            command=self.refresh_users,
        ).pack(side="right")

        self.users_scroll = ctk.CTkScrollableFrame(tab, fg_color="transparent")
        self.users_scroll.pack(fill="both", expand=True, padx=4, pady=4)

        self.refresh_users()

    def refresh_users(self) -> None:
        for w in self.users_scroll.winfo_children():
            w.destroy()

        users = database.get_all_users()

        for u in users:
            self._render_user_row(u)

    def _render_user_row(self, u: Dict[str, Any]) -> None:
        row = ctk.CTkFrame(self.users_scroll, fg_color=COLOR_CARD, corner_radius=8, border_width=1, border_color=COLOR_BORDER)
        row.pack(fill="x", padx=8, pady=4)

        inner = ctk.CTkFrame(row, fg_color="transparent")
        inner.pack(fill="x", padx=14, pady=10)

        left = ctk.CTkFrame(inner, fg_color="transparent")
        left.pack(side="left")

        ctk.CTkLabel(left, text=f"{u['name']} (📞 {u['phone']})", font=FONT_BODY_BOLD, text_color=COLOR_TITLE_TEXT).pack(anchor="w")
        ctk.CTkLabel(left, text=f"Role: {u['role'].capitalize()}  |  📍 {u['locality']}  |  Joined: {u['created_at']}", font=FONT_SMALL, text_color=COLOR_MUTED_TEXT).pack(anchor="w")

        right = ctk.CTkFrame(inner, fg_color="transparent")
        right.pack(side="right")

        if u.get("is_blacklisted", 0) == 1:
            ctk.CTkLabel(right, text=" BLACKLISTED ", font=FONT_BADGE, fg_color=COLOR_DANGER, text_color="#ffffff", corner_radius=6).pack(side="left", padx=4)

        if u.get("is_suspended", 0) == 1:
            ctk.CTkLabel(right, text=" SUSPENDED ", font=FONT_BADGE, fg_color=COLOR_DANGER, text_color="#ffffff", corner_radius=6).pack(side="left", padx=4)

        if u.get("is_blacklisted", 0) == 0 and u.get("is_suspended", 0) == 0:
            ctk.CTkLabel(right, text=" ACTIVE ", font=FONT_BADGE, fg_color=COLOR_SUCCESS, text_color="#ffffff", corner_radius=6).pack(side="left", padx=4)

