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
        pages = {"/": self.get_index_layout,
                 "/tasks": self.get_tasks_layout,
                 "/stats": self.get_stats_layout}

        page_content = html.Div([
            dbc.NavbarSimple(
                children=[
                    dbc.NavItem(dcc.Link("Home", href="/", className="nav-link")),
                    dbc.NavItem(dcc.Link("Tasks' Reporting", href="/tasks", className="nav-link")),
                    dbc.NavItem(dcc.Link("Stats' Reporting", href="/stats", className="nav-link")),
                    dbc.DropdownMenu(
                        children=[
                            dbc.DropdownMenuItem("More pages", header=True),
                            dbc.DropdownMenuItem("Page 2", href="#"),
                            dbc.DropdownMenuItem("Page 3", href="#"),
                        ],
                        nav=True,
                        in_navbar=True,
                        label="More",
                    ),
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
        return self.dash_cards.get_layout()

    def get_stats_layout(self):
        return "stats"
