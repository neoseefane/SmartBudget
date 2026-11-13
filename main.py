from __future__ import annotations

import csv
from datetime import date
from pathlib import Path

import flet as ft

from models.budget import Budget
from models.transaction import Transaction
from services.storage import StorageService

APP_DIR = Path(__file__).resolve().parent
DB_PATH = APP_DIR / "smartbudget.db"

NAV_ITEMS = [
    ("Dashboard", ft.Icons.DASHBOARD_OUTLINED),
    ("Transactions", ft.Icons.SWAP_HORIZ),
    ("Budgets", ft.Icons.ACCOUNT_BALANCE_WALLET_OUTLINED),
    ("Reports", ft.Icons.INSERT_CHART_OUTLINED),
    ("Settings", ft.Icons.SETTINGS_OUTLINED),
]

BG = "#F5F7FB"
CARD = "#FFFFFF"
INK = "#172033"
MUTED = "#718096"
GREEN = "#159B72"
RED = "#D9534F"
BLUE = "#4263EB"
PURPLE = "#805AD5"

def money(value: float) -> str:
    return f"R{value:,.2f}"

def main(page: ft.Page):
    store = StorageService(DB_PATH)
    selected_view = {"name": "Dashboard"}
    page.title = "Smart Budget | Personal Finance"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.bgcolor = BG
    page.padding = 0
    page.window_min_width = 900
    page.window_min_height = 650
    page.theme = ft.Theme(color_scheme_seed=GREEN, use_material3=True)

    content = ft.Container(expand=True, padding=28)
    nav_column = ft.Column(spacing=7)
    nav_buttons = {}

    def notify(message: str, color: str = GREEN):
        page.snack_bar = ft.SnackBar(
            content=ft.Text(message, color="#FFFFFF"),
            bgcolor=color,
        )
        page.show_dialog(page.snack_bar)

    def card(content_control, padding=20, expand=True):
        return ft.Container(
            content=content_control,
            bgcolor=CARD,
            border_radius=16,
            padding=padding,
            expand=expand,
            border=ft.Border.all(1, "E9EDF4")
        )

    def section_title(title: str, subtitle: str = ""):
        return ft.Column(
            [
                ft.Text(title, size=25, weight=ft.FontWeight.BOLD, color=INK),
                ft.Text(subtitle, size=20, color=MUTED) if subtitle else ft.Container(),
            ],
            spacing=4
        )

    def stat_card(label, value, icon, accent, helper):
        return ft.Container(
            content=ft.Row(
                [
                    ft.Column(
                        [
                            ft.Text(label, color=MUTED, size=12),
                            ft.Text(value, color=INK, size=23, weight=ft.FontWeight.BOLD),
                            ft.Text(helper, color=MUTED, size=11)
                        ],
                        spacing=5,
                        expand=True,
                    ),
                    ft.Container(
                        content=ft.Icon(icon, color=accent, size=22),
                        bgcolor=accent + "18",
                        border_radius=12,
                        padding=12,
                    ),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            ),
            bgcolor=CARD,
            border=ft.Border.all(1, "E9EDF4"),
            border_radius=16,
            padding=18,
            expand=True,
        )

    def transaction_row(item: Transaction, show_actions=True):
        sign = "+" if item.kind == "Income" else "-"
        color = GREEN if item.kind == "Income" else RED
        leading_icon = ft.Icons.SOUTH_WEST if item.kind == "Income" else ft.Icons.NORTH_EAST
        cells = [
            ft.Container(
                content=ft.Icon(leading_icon, color=color, size=18),
                bgcolor=color + "18",
                border_radius=10,
                padding=9
            ),
            ft.Column(
                [
                    ft.Text(item.title, weight=ft.FontWeight.W_600, color=INK, size=13),
                    ft.Text(f"{item.category} • {item.transaction_date}", color=MUTED, size=11)
                ],
                spacing=3,
                expand=True,
            ),
            ft.Text(f"{sign}{money(item.amount)}", color=color, weight=ft.FontWeight.BOLD, size=13),
        ]
        if show_actions:
            cells.append(
                ft.PopupMenuButton(
                    icon=ft.Icons.MORE_HORIZ,
                    items=[
                        ft.PopupMenuItem(content="Edit", on_click=lambda e, tx=item: open_transaction_dialog(tx)),
                        ft.PopupMenuItem(content="Delete", on_click=lambda e, tx=item: confirm_delete(tx)),
                    ],
                )
            )
        return ft.Container(
            content=ft.Row(cells, alignment=ft.MainAxisAlignment.SPACE_BETWEEN, vertical_alignment=ft.CrossAxisAlignment.CENTER),
            padding=ft.Padding.symmetric(vertical=10),
            border=ft.Border.only(bottom=ft.BorderSide(1, "#F0F2F6")),
        )

    def current_totals():
        rows = store.list_transactions()
        income = sum(t.amount for t in rows if t.kind == "Income")
        expenses = sum(t.amount for t in rows if t.kind == "Expense")
        return income, expenses, income - expenses

    def refresh():
        render_view(selected_view["name"])

    def set_view(name: str):
        selected_view["name"] = name

        for item_name, button in nav_buttons.items():
            active = item_name == name
            button.bgcolor = "#E8F6F1" if active else None
            button.content.controls[0].color = GREEN if active else "#8A94A6"
            button.content.controls[1].color = GREEN if active else "#596579"
            button.content.controls[1].weight = ft.FontWeight.BOLD if active else ft.FontWeight.NORMAL
        render_view(name)
        page.update()

    def open_transaction_dialog(existing: Transaction | None = None):
        title_field = ft.TextField(label="Description", value=existing.title if existing else "", autofocus=True)
        amount_field = ft.TextField(label="Amount (ZAR)", value=str(existing.amount) if existing else "", keyboard_type=ft.KeyboardType.NUMBER)
        kind_field = ft.TextField(label="Type (Income or Expense)", value=existing.kind if existing else "Expense")
        category_field = ft.TextField(label="Category", value=existing.category if existing else "Food")
        date_field = ft.TextField(label="Date (YYYY-MM-DD)",
                                  value=existing.transaction_date if existing else date.today().isoformat())
        note_field = ft.TextField(label="Notes (optional)", value=existing.note if existing else "", multiline=True,
                                  min_lines=1, max_lines=2)
        error_text = ft.Text("", color=RED, size=11)

        def save(e):
            try:
                title = title_field.value.strip()
                amount = float(amount_field.value)
                kind = kind_field.value.strip().title()
                category = category_field.value.strip()
                tx_date = date.fromisoformat(date_field.value.strip()).isoformat()
                if not title or not category:
                    raise ValueError("Description and category are required.")
                if amount <= 0:
                    raise ValueError("Amount must be greater than zero.")
                if kind not in ("Income", "Expense"):
                    raise ValueError("Type must be Income or Expense.")
                tx = Transaction(
                    id=existing.id if existing else None,
                    title=title,
                    amount=amount,
                    kind=kind,
                    category=category,
                    transaction_date=tx_date,
                    note=note_field.value.strip(),
                )
                store.save_transaction(tx)
                page.pop_dialog()
                notify("Transaction updated." if existing else "Transaction added.")
                refresh()
            except (ValueError, TypeError) as ex:
                error_text.value = str(ex) if str(ex) else "Please enter a valid amount."
                page.update()

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Edit transaction" if existing else "Add transaction"),
            content=ft.Container(
                width=420,
                content=ft.Column(
                    [title_field, amount_field, kind_field, category_field, date_field, note_field, error_text],
                    tight=True,
                    scroll=ft.ScrollMode.AUTO,
                ),
            ),
            actions=[
                ft.TextButton("Cancel", on_click=lambda e: page.pop_dialog()),
                ft.FilledButton("Save transaction", on_click=save, bgcolor=GREEN),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        page.show_dialog(dialog)

    def confirm_delete(item: Transaction):
        def delete(e):
            store.delete_transaction(item.id)
            page.pop_dialog()
            notify("Transaction deleted.", RED)
            refresh()

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Delete transaction?"),
            content=ft.Text(f"'{item.title}' will be permanently removed."),
            actions=[
                ft.TextButton("Cancel", on_click=lambda e: page.pop_dialog()),
                ft.FilledButton("Delete", bgcolor=RED, on_click=delete),
            ]
        )
        page.show_dialog(dialog)

    def open_budget_dialog():
        category_field = ft.TextField(
            label="Budget category",
            hint_text="e.g. Groceries",
        )

        limit_field = ft.TextField(
            label="Monthly limit (ZAR)",
            keyboard_type=ft.KeyboardType.NUMBER,
        )

        error_text = ft.Text("", color=RED, size=11)

        def save(e):
            try:
                category = (category_field.value or "").strip()
                limit = float(limit_field.value or 0)

                if not category or limit <= 0:
                    raise ValueError(
                        "Enter a category and a positive budget amount."
                    )

                store.save_budget(
                    Budget(
                        id=None,
                        category=category,
                        monthly_limit=limit,
                    )
                )

                page.pop_dialog()
                notify("Budget saved.")
                refresh()

            except (ValueError, TypeError) as ex:
                error_text.value = str(ex) or "Enter a valid amount."
                page.update()

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Create monthly budget"),
            content=ft.Column(
                [category_field, limit_field, error_text],
                tight=True,
                width=360,
            ),
            actions=[
                ft.TextButton(
                    "Cancel",
                    on_click=lambda e: page.pop_dialog(),
                ),
                ft.FilledButton(
                    "Save budget",
                    bgcolor=GREEN,
                    on_click=save,
                ),
            ],
        )

        page.show_dialog(dialog)

    def render_dashboard():
        income, expenses, balance = current_totals()
        rows = store.list_transactions()[:5]
        budgets = store.list_budgets()
        expense_ratio = expenses / income if income > 0 else 0
        top = ft.Row(
            [
                section_title("Good day ", "Here is your financial overview."),
                ft.Container(expand=True),
                ft.FilledButton("＋  Add transaction", on_click=lambda e: open_transaction_dialog(),
                                bgcolor=GREEN),
            ],
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )
        stats = ft.ResponsiveRow(
            [
                ft.Container(
                    content=stat_card("Total balance", money(balance), ft.Icons.ACCOUNT_BALANCE_WALLET, GREEN,
                                      "Income minus expenses"), col={"sm": 12, "md": 6, "lg": 3}),
                ft.Container(content=stat_card("Total income", money(income), ft.Icons.TRENDING_UP, BLUE,
                                               "All recorded income"), col={"sm": 12, "md": 6, "lg": 3}),
                ft.Container(content=stat_card("Total expenses", money(expenses), ft.Icons.TRENDING_DOWN, RED,
                                               "All recorded expenses"), col={"sm": 12, "md": 6, "lg": 3}),
                ft.Container(
                    content=stat_card("Active budgets", str(len(budgets)), ft.Icons.PIE_CHART_OUTLINE, PURPLE,
                                      "Monthly spending plans"), col={"sm": 12, "md": 6, "lg": 3}),
            ],
            run_spacing=12,
            spacing=12,
        )
        recent_content = ft.Column(
            [
                ft.Row([ft.Text("Recent transactions", size=16, weight=ft.FontWeight.BOLD, color=INK),
                        ft.Container(expand=True),
                        ft.TextButton("View all", on_click=lambda e: set_view("Transactions"))]),
                *([transaction_row(t) for t in rows] if rows else [
                    ft.Text("No transactions yet. Add your first transaction to get started.", color=MUTED,
                            size=12)]),
            ],
            spacing=4,
        )
        budget_content = [ft.Text("Budget snapshot", size=16, weight=ft.FontWeight.BOLD, color=INK)]
        if budgets:
            for budget in budgets[:4]:
                spent = store.category_expenses(budget.category)
                ratio = min(spent / budget.monthly_limit, 1) if budget.monthly_limit else 0
                budget_content.append(
                    ft.Column(
                        [
                            ft.Row([ft.Text(budget.category, weight=ft.FontWeight.W_600, size=12),
                                    ft.Container(expand=True),
                                    ft.Text(f"{money(spent)} / {money(budget.monthly_limit)}", size=11,
                                            color=MUTED)]),
                            ft.ProgressBar(value=ratio, color=GREEN if ratio < .8 else RED, bgcolor="#EDF0F5",
                                           bar_height=7),
                        ],
                        spacing=6,
                    )
                )
        else:
            budget_content.append(
                ft.Text("Create a budget to track your spending limits.", color=MUTED, size=12))
            budget_content.append(ft.TextButton("Create a budget", on_click=lambda e: open_budget_dialog()))
        content.content = ft.Column(
            [top, stats, ft.ResponsiveRow([
                ft.Container(content=card(recent_content), col={"sm": 12, "lg": 7}),
                ft.Container(content=card(ft.Column(budget_content, spacing=14)), col={"sm": 12, "lg": 5}),
            ], spacing=14, run_spacing=14)],
            spacing=20,
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        )

    def render_transactions():
        search = ft.TextField(
            hint_text="Search description or category...",
            prefix_icon=ft.Icons.SEARCH,
            dense=True,
            width=300,
            on_change=lambda e: update_transaction_list(e.control.value),
        )
        filter_field = ft.TextField(
            label="Filter type: All, Income or Expense",
            value="All",
            width=220,
            dense=True,
            on_change=lambda e: update_transaction_list(search.value, e.control.value),
        )
        list_column = ft.Column(spacing=0)

        def update_transaction_list(query="", kind="All"):
            list_column.controls.clear()
            rows = store.list_transactions()
            q = (query or "").lower().strip()
            kind = (kind or "All").title()
            if kind not in ("All", "Income", "Expense"):
                kind = "All"
            rows = [t for t in rows if (q in t.title.lower() or q in t.category.lower()) and (kind == "All" or t.kind == kind)]
            if rows:
                list_column.controls.extend([transaction_row(t) for t in rows])
            else:
                list_column.controls.append(ft.Container(ft.Text("No matching transactions found.", color=MUTED), padding=20))
            page.update()

        update_transaction_list()
        content.content = ft.Column(
            [
                ft.Row([section_title("Transactions", "Manage your income and expenses."), ft.Container(expand=True), ft.FilledButton("＋  Add transaction", on_click=lambda e: open_transaction_dialog(), bgcolor=GREEN)]),
                card(ft.Column([
                    ft.Row([search, filter_field], wrap=True),
                    ft.Divider(color="#EEF0F4"),
                    list_column,
                ], spacing=12)),
            ],
            spacing=20,
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        )

    def render_budgets():
        budgets = store.list_budgets()
        budget_cards = []
        for budget in budgets:
            spent = store.category_expenses(budget.category)
            remaining = budget.monthly_limit - spent
            ratio = min(spent / budget.monthly_limit, 1) if budget.monthly_limit else 0
            budget_cards.append(
                ft.Container(
                    content=ft.Column([
                        ft.Row([
                            ft.Column([ft.Text(budget.category, size=16, weight=ft.FontWeight.BOLD, color=INK), ft.Text("Monthly spending limit", size=11, color=MUTED)], spacing=3, expand=True),
                            ft.Text(money(budget.monthly_limit), size=16, weight=ft.FontWeight.BOLD, color=INK),
                        ]),
                        ft.ProgressBar(value=ratio, color=GREEN if ratio < .8 else RED, bgcolor="#EDF0F5", bar_height=9),
                        ft.Row([
                            ft.Text(f"Spent: {money(spent)}", color=MUTED, size=11),
                            ft.Container(expand=True),
                            ft.Text(f"{'Remaining' if remaining >= 0 else 'Over budget'}: {money(abs(remaining))}", color=GREEN if remaining >= 0 else RED, size=11, weight=ft.FontWeight.BOLD),
                        ]),
                    ], spacing=12),
                    bgcolor=CARD,
                    border=ft.Border.all(1, "#E9EDF4"),
                    border_radius=15,
                    padding=18,
                )
            )
        if not budget_cards:
            budget_cards = [card(ft.Column([ft.Icon(ft.Icons.SAVINGS_OUTLINED, size=34, color=MUTED), ft.Text("No budgets created yet", weight=ft.FontWeight.BOLD), ft.Text("Set a monthly spending limit for a category.", color=MUTED, size=12)], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=8), padding=30)]
        content.content = ft.Column(
            [
                ft.Row([section_title("Budgets", "Set limits and keep your spending on track."), ft.Container(expand=True), ft.FilledButton("＋  Create budget", bgcolor=GREEN, on_click=lambda e: open_budget_dialog())]),
                *budget_cards,
            ],
            spacing=16,
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        )

    def render_reports():
        income, expenses, balance = current_totals()
        categories = store.expenses_by_category()
        max_value = max(categories.values(), default=1)
        bars = []

        for category, amount in sorted(categories.items(), key=lambda pair: pair[1], reverse=True):
            bars.append(
                ft.Column([
                    ft.Row([ft.Text(category, size=12, color=INK), ft.Container(expand=True), ft.Text(money(amount), size=12, weight=ft.FontWeight.BOLD)]),
                    ft.ProgressBar(value=amount / max_value if max_value else 0, color=BLUE, bgcolor="#EDF0F5", bar_height=10),
                ], spacing=6)
            )

        if not bars:
            bars = [ft.Text("Add expense transactions to see your category breakdown.", color=MUTED, size=12)]
        content.content = ft.Column(
            [
                section_title("Reports & insights", "A simple view of your recorded financial activity."),
                ft.ResponsiveRow([
                    ft.Container(content=stat_card("Income", money(income), ft.Icons.TRENDING_UP, BLUE, "Recorded income"), col={"sm": 12, "md": 4}),
                    ft.Container(content=stat_card("Expenses", money(expenses), ft.Icons.TRENDING_DOWN, RED, "Recorded expenses"), col={"sm": 12, "md": 4}),
                    ft.Container(content=stat_card("Net balance", money(balance), ft.Icons.ACCOUNT_BALANCE, GREEN, "Income less expenses"), col={"sm": 12, "md": 4}),
                ], spacing=12, run_spacing=12),
                card(ft.Column([ft.Text("Expenses by category", size=16, weight=ft.FontWeight.BOLD, color=INK), *bars], spacing=16)),
                card(ft.Column([
                    ft.Text("Financial health tips", size=16, weight=ft.FontWeight.BOLD, color=INK),
                    ft.Text("• Review your largest spending categories regularly.", color=MUTED, size=12),
                    ft.Text("• Set realistic monthly budgets before the month begins.", color=MUTED, size=12),
                    ft.Text("• Record transactions consistently to keep reports useful.", color=MUTED, size=12),
                ], spacing=8)),
            ],
            spacing=18,
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        )

    def render_settings():
        def export_csv(e):
            rows = store.list_transactions()
            export_path = APP_DIR / "transactions_export.csv"
            with export_path.open("w", newline="", encoding="utf-8") as handle:
                writer = csv.writer(handle)
                writer.writerow(["id", "description", "amount", "type", "category", "date", "note"])
                for tx in rows:
                    writer.writerow([tx.id, tx.title, tx.amount, tx.kind, tx.category, tx.transaction_date, tx.note])
            notify(f"Export saved to {export_path.name}")

        content.content = ft.Column(
            [
                section_title("Settings", "Application information and data tools."),
                card(ft.Column([
                    ft.Text("Application profile", size=16, weight=ft.FontWeight.BOLD, color=INK),
                    ft.ListTile(leading=ft.Icon(ft.Icons.PERSON_OUTLINE), title=ft.Text("Application"), subtitle=ft.Text("SmartBudget Personal Finance Manager")),
                    ft.ListTile(leading=ft.Icon(ft.Icons.PALETTE_OUTLINED), title=ft.Text("Default currency"), subtitle=ft.Text("South African Rand (ZAR)")),
                    ft.ListTile(leading=ft.Icon(ft.Icons.STORAGE_OUTLINED), title=ft.Text("Storage"), subtitle=ft.Text("Local SQLite database (smartbudget.db)")),
                ], spacing=4)),
                card(ft.Column([
                    ft.Text("Data management", size=16, weight=ft.FontWeight.BOLD, color=INK),
                    ft.Text("Export your transactions to a CSV file for use in spreadsheet applications.", color=MUTED, size=12),
                    ft.FilledButton("Export transactions to CSV", icon=ft.Icons.DOWNLOAD, on_click=export_csv, bgcolor=GREEN),
                ], spacing=12)),
                card(ft.Column([
                    ft.Text("About SmartBudget", size=16, weight=ft.FontWeight.BOLD, color=INK),
                    ft.Text("A FNB App Academy Unit 6 capstone project demonstrating Python, Object-Oriented Programming, persistent storage, multi-view Flet UI design and software testing.", color=MUTED, size=12),
                    ft.Text("Version 1.0 • Educational project", color=MUTED, size=11),
                ], spacing=8)),
            ],
            spacing=18,
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        )

    def render_view(name: str):
        if name == "Dashboard":
            render_dashboard()
        elif name == "Transactions":
            render_transactions()
        elif name == "Budgets":
            render_budgets()
        elif name == "Reports":
            render_reports()
        else:
            render_settings()
        page.update()

    for label, icon in NAV_ITEMS:
        button = ft.Container(
            content=ft.Row([
                ft.Icon(icon, color="#8A94A6", size=19),
                ft.Text(label, color="#596579", size=13),
            ], spacing=13),
            padding=ft.Padding.symmetric(horizontal=14, vertical=12),
            border_radius=10,
            on_click=lambda e, name=label: set_view(name),
            ink=True,
        )
        nav_buttons[label] = button
        nav_column.controls.append(button)

    sidebar = ft.Container(
        width=225,
        bgcolor="#FFFFFF",
        padding=ft.Padding.symmetric(horizontal=16, vertical=24),
        border=ft.Border.only(right=ft.BorderSide(1, "#E9EDF4")),
        content=ft.Column([
            ft.Row([
                ft.Container(content=ft.Icon(ft.Icons.ACCOUNT_BALANCE_WALLET, color="#FFFFFF", size=21), bgcolor=GREEN, border_radius=11, padding=10),
                ft.Column([ft.Text("SmartBudget", weight=ft.FontWeight.BOLD, size=17, color=INK), ft.Text("PERSONAL FINANCE", size=9, color=MUTED, weight=ft.FontWeight.BOLD)], spacing=1),
            ], spacing=10),
            ft.Container(height=25),
            ft.Text("WORKSPACE", size=10, color="#A0A8B6", weight=ft.FontWeight.BOLD),
            nav_column,
            ft.Container(expand=True),
            ft.Container(
                content=ft.Column([
                    ft.Icon(ft.Icons.LIGHTBULB_OUTLINE, color=GREEN, size=21),
                    ft.Text("Small steps add up.", size=12, weight=ft.FontWeight.BOLD, color=INK),
                    ft.Text("Track your spending and build better money habits.", size=10, color=MUTED),
                ], spacing=7),
                bgcolor="#F0F8F5",
                border_radius=12,
                padding=13,
            ),
            ft.Text("SmartBudget • 2026", size=10, color="#A0A8B6"),
        ], expand=True),
    )

    header = ft.Container(
        content=ft.Row([
            ft.Text("Personal Finance Workspace", color=MUTED, size=12),
            ft.Container(expand=True),
            ft.CircleAvatar(content=ft.Text("SB", color="#FFFFFF", size=11), bgcolor=GREEN, radius=17),
            ft.Text("My account", size=12, color=INK, weight=ft.FontWeight.W_600),
        ]),
        padding=ft.Padding.symmetric(horizontal=28, vertical=14),
        bgcolor="#FFFFFF",
        border=ft.Border.only(bottom=ft.BorderSide(1, "#E9EDF4")),
    )

    page.add(
        ft.Row(
            [
                sidebar,
                ft.Column([header, content], expand=True, spacing=0),
            ],
            expand=True,
            spacing=0,
            vertical_alignment=ft.CrossAxisAlignment.STRETCH,
        )
    )
    set_view("Dashboard")

if __name__ == "__main__":
    ft.run(main)