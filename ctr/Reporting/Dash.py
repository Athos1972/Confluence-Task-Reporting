from ctr.Database.connection import SqlConnector
from ctr.Reporting.Reporter import PageReporting
from ctr.Reporting.Reporter import UserReporting
from ctr.Reporting.DashValues import DashValues
import dash_bootstrap_components as dbc
from dash import html, dcc
import plotly.express as px


class DashConstants:
    def __init__(self, db_connection: SqlConnector):
        self.db_connection = db_connection
        self.user_reporting = UserReporting(db_connection=self.db_connection)
        self.page_reporting = PageReporting(db_connection=self.db_connection)

    def get_companies(self):
        return [None] + self.user_reporting.get_companies()

    def get_spaces(self):
        return [None] + self.page_reporting.get_spaces()


class DashCards:
    PAGE_SIZE = 25

    def __init__(self, dash_values: DashValues, dash_constants: DashConstants):
        self.dash_values = dash_values
        self.dash_constants = dash_constants

    def get_space_overdue_task_card(self, overdue_value=None):
        if not overdue_value:
            overdue_value = "-"

        card = dbc.Card(
            dbc.CardBody(
                [
                    html.H4("Space's Overdue Tasks", className="card-title"),
                    html.P(html.Center(html.Strong(overdue_value)),
                           className="card-text",
                           ),
                ]
            ),
            color="light",
            className="w-100",
        )
        return card

    def get_company_overdue_task_card(self, overdue_value=None):
        if not overdue_value:
            overdue_value = "-"
        card = dbc.Card(
            dbc.CardBody(
                [
                    html.H4("Company's Overdue Tasks", className="card-title"),
                    html.P(html.Center(html.Strong(overdue_value)),
                           className="card-text",
                           ),
                ]
            ),
            color="dark", inverse=True,
            className="w-100"
        )
        return card

    def get_task_average_time_card(self, tasks_by_age_data=None):
        if not any(tasks_by_age_data):
            tasks_by_age_data = {"age": 0}
        card = dbc.Card(
            dbc.CardBody(
                [
                    html.H4("Average Task Age", className="card-title"),
                    html.P(html.Center(html.Strong(f"{int(tasks_by_age_data['age'].mean())} days")),
                           className="card-text",
                           ),
                ]
            ),
            className="w-100"
        )
        return card

    def get_space_selector(self):
        selector = dbc.InputGroup(
            [dbc.InputGroupText("Space"),
             dbc.Select(id="selectSpace",
                        value=None,
                        options=[{"label": space, "value": space} for space in self.dash_constants.get_spaces()])],
            className="mb-3")

        return selector

    def get_company_selector(self):
        selector = dbc.InputGroup(
            [dbc.InputGroupText("Company"),
             dbc.Select(id="selectCompany",
                        value=None,
                        options=[{"label": company, "value": company} for company in
                                 self.dash_constants.get_companies()])],
            className="mb-3")

        return selector

    def get_overdue_checkbox(self):
        element = dbc.InputGroup(
            [dbc.Checkbox(id="checkOverdue", value=False, label="Only Overdue")],
            className="mt-2")
        return element

    def get_open_tasks_per_space_fig(self, overdue=False):
        fig = px.bar(data_frame=self.dash_values.get_open_tasks_per_space(overdue=overdue),
                     x='space',
                     y='count',
                     color='space',
                     hover_data=['space'])
        return fig

    def get_open_tasks_per_company_fig(self, overdue=False):
        fig = px.bar(data_frame=self.dash_values.get_task_count_by_company(overdue=overdue),
                     x='company',
                     y='count',
                     color='company',
                     hover_data=['company'])
        return fig

    def get_datatable_column(self):
        from dash import dash_table
        table = dash_table.DataTable(id="grid-table-inner",
                                     columns=[
                                         {"name": i, "id": i} for i in self.dash_values.get_grid_data()],
                                     data=self.dash_values.get_grid_data().to_dict("records"),
                                     page_size=DashCards.PAGE_SIZE,
                                     sort_action="native",
                                     sort_mode="multi")
        column = dbc.Col([table], className="mt-3", width=12, id="grid-table")
        return column

        column = dbc.Col([
            dbc.Table.from_dataframe(self.dash_values.get_grid_data()[:DashCards.PAGE_SIZE],
                                     striped=True,
                                     bordered=True,
                                     hover=True,

                                     ),
        ], className="mt-3", width=12, id="grid-table",
        )
        return column

    def get_chart_rows(self, spaces, companies, overdue):
        return [
            dbc.Col([html.Strong("Open tasks per space")], className="text-center mt-3 pt-3",
                    width=6),
            dbc.Col([html.Strong("Open tasks per company")], className="text-center mt-3 pt-3",
                    width=6),
            dbc.Col([dcc.Graph(figure=self.get_open_tasks_per_space_fig())], width=6),
            dbc.Col([dcc.Graph(figure=self.get_open_tasks_per_company_fig())], width=6),
            dbc.Col([self.get_space_overdue_task_card()], width=3),
            dbc.Col([self.get_company_overdue_task_card()], width=3),
            dbc.Col([self.get_task_average_time_card(self.dash_values.get_tasks_age(overdue=True))], width=3),
            dbc.Col([
                dbc.Button(id="btn_send_reminder", children=["Send Reminder"], className="w-100 h-100",
                           n_clicks=0)
            ], width=3),
            self.get_datatable_column(),
            # className="mt-3", width = 12
        ]

    def get_layout(self, spaces, companies, overdue):
        selectCompany = self.get_company_selector()
        selectSpace = self.get_space_selector()
        checkOverdue = self.get_overdue_checkbox()

        layout = dbc.Container(
            children=[
                html.Div(id="callback_output", style={"display": "none"}),  # ignore
                html.Div(id="callback_output2", style={"display": "none"}),  # ignore
                # filters
                dbc.Row(
                    [dbc.Col([selectSpace], width=5),
                     dbc.Col([selectCompany], width=5),
                     dbc.Col([checkOverdue], width=2)],
                    className="pt-3"
                ),
                # charts
                dbc.Row(self.get_chart_rows(spaces=spaces, companies=companies, overdue=overdue),
                        id="dashboard"),
                dbc.Pagination(id="pagination",
                               min_value=1,
                               max_value=self.dash_values.get_max_pages(),
                               className="justify-content-center",
                               fully_expanded=False,
                               first_last=True,
                               previous_next=True)
            ]

        )
        return layout
