"""
Local Hire — Native Desktop Application Entry Point.
Initializes SQLite database, configures CustomTkinter theme, and manages view routing.
"""

import sys
import customtkinter as ctk

import database
import auth
from views.auth_view import AuthView
from views.worker_view import WorkerView
from views.employer_view import EmployerView
from views.admin_view import AdminView


class LocalHireApp(ctk.CTk):
    """Primary application controller for Local Hire."""

    def __init__(self) -> None:
        super().__init__()

        # Appearance & Theme configuration
        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("blue")

        # Window settings
        self.title("Local Hire — Direct Micro-Employment Platform (Kerala)")
        self.geometry("1180x800")
        self.minsize(980, 680)

        # Session reference
        self.session = auth.session

        # Main dynamic container frame where views are swapped
        self.container = ctk.CTkFrame(self, fg_color="transparent")
        self.container.pack(fill="both", expand=True)

        self.current_view: ctk.CTkFrame | None = None

        # Route to AuthView on startup
        self.show_auth_view()

    def clear_container(self) -> None:
        """Destroys current active view widgets."""
        if self.current_view:
            self.current_view.destroy()
            self.current_view = None

    def show_auth_view(self) -> None:
        """Loads the login and registration screen."""
        self.clear_container()
        self.current_view = AuthView(self.container, self)

    def on_login_success(self) -> None:
        """Routes user to their role-specific dashboard following authentication."""
        role = self.session.get_role()
        self.clear_container()

        if role == "worker":
            self.current_view = WorkerView(self.container, self)
        elif role == "employer":
            self.current_view = EmployerView(self.container, self)
        elif role == "admin":
            self.current_view = AdminView(self.container, self)
        else:
            self.show_auth_view()

    def logout(self) -> None:
        """Logs out current user, clears session, and returns to authentication screen."""
        self.session.logout()
        self.show_auth_view()


def main() -> None:
    # 1. Initialize SQLite Database Schema & Seed Data
    try:
        database.init_db()
    except Exception as e:
        print(f"[ERROR] Failed to initialize database: {e}", file=sys.stderr)
        sys.exit(1)

    # 2. Launch Desktop GUI
    app = LocalHireApp()
    app.mainloop()


if __name__ == "__main__":
    main()

