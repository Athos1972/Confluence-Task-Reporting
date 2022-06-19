import dash_bootstrap_components as dbc
from dash import html, dcc
from datetime import date

from ctr.Database.connection import SqlConnector
from ctr.Reporting import Reporter as Reporter
from ctr.Util import logger, global_config


class DashPages:

    def __init__(self, dash_cards):
        self.dash_cards = dash_cards

    def get_layout(self, active_page):
        pages = {"/": self.get_tasks_layout,
                 "/tasks": self.get_tasks_layout,
                 "/stats": self.get_stats_layout}

        page_content = html.Div([
            dbc.NavbarSimple(
                children=[
                    dbc.NavItem(dcc.Link("Home", href="/", className="nav-link")),
                    dbc.NavItem(dcc.Link("Tasks' Reporting", href="/tasks", className="nav-link")),
                    dbc.NavItem(dcc.Link("Stats' Reporting", href="/stats", className="nav-link")),
                ],
                brand="Confluence Task Reporting",
                brand_href="#",
                color="dark",
                dark=True,
            ),
            pages[active_page]()
        ])
        return page_content

    def get_index_layout(self):
        # make an index page maybe?
        return "index"

    def get_tasks_layout(self):
        selectCompany = self.dash_cards.get_company_selector(call_type="Dropdown")
        selectSpace = self.dash_cards.get_space_selector(call_type="Dropdown")
        checkRadio = self.dash_cards.get_radio_selectors()
        checkOverdue = self.dash_cards.get_overdue_checkbox()
        checkDate = self.dash_cards.get_date_checkbox()

        layout = dbc.Container(
            children=[
                html.Div(id="callback_output", style={"display": "none"}),  # ignore
                # filters
                dbc.Row(
                    [dbc.Col([selectSpace], width=5),
                     dbc.Col([selectCompany], width=5),
                     dbc.Col([
                         #            dbc.Col([checkOverdue], width=12),
                         #            dbc.Col([checkDate], width=12),
                         checkRadio,
                     ], width=2)],
                    className="pt-3"
                ),
                # charts
                dbc.Row(self.dash_cards.get_tasks_chart_rows(),
                        id="dashboard"),
            ]
        )

        return layout

    def get_stats_layout(self):
        selectCompany = self.dash_cards.get_company_selector(call_type="Dropdown")
        selectSpace = self.dash_cards.get_space_selector(call_type="Dropdown")
        checkRadio = self.dash_cards.get_radio_selectors()

        layout = dbc.Container(
            children=[
                html.Div(id="callback_output", style={"display": "none"}),  # ignore

                dbc.Row(
                    [dbc.Col([selectSpace], width=6),
                     dbc.Col([selectCompany], width=6),
                     dbc.Col([
                         #            dbc.Col([checkOverdue], width=12),
                         #            dbc.Col([checkDate], width=12),
                         checkRadio,
                     ], width=2, className="d-none")],
                    className="pt-3"
                ),

                dbc.Row(self.dash_cards.get_stats_chart_rows(), id="dashboard"),
            ]
        )
        return layout
