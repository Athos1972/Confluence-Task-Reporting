from ctr.Database.connection import SqlConnector
from ctr.Reporting.Reporter import PageReporting
from ctr.Reporting.Reporter import UserReporting
from ctr.Reporting.DashValues import DashValues
from ctr.Util import logger
import dash_bootstrap_components as dbc
from dash import html, dcc, dash_table
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd


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

    @staticmethod
    def get_space_overdue_task_card(overdue_value=None):
        if not any(overdue_value):
            output_overdue_value = 0
        else:
            output_overdue_value = int(overdue_value['count'].sum())

        card = dbc.Card(
            dbc.CardBody(
                [
                    html.H5(html.Center("Space's Tasks"), className="card-title"),
                    html.P(html.Center(html.Strong(str(output_overdue_value))),
                           className="card-text",
                           ),
                ]
            ),
            color="light",
            className="w-100",
        )
        return card

    @staticmethod
    def get_company_overdue_task_card(overdue_value=None):
        if not any(overdue_value):
            output_overdue_value = 0
        else:
            output_overdue_value = int(overdue_value['count'].sum())
        card = dbc.Card(
            dbc.CardBody(
                [
                    html.H5(html.Center("Company's Tasks"), className="card-title"),
                    html.P(html.Center(html.Strong(output_overdue_value)),
                           className="card-text",
                           ),
                ]
            ),
            color="light",
            className="w-100"
        )
        return card

    @staticmethod
    def get_task_average_time_card(tasks_by_age_data=None, filter_date=False):
        if not any(tasks_by_age_data):
            tasks_by_age_data = {"age": 0}

        tasks_by_age_value = "-"
        if not filter_date:
            tasks_by_age_value = f"{int(tasks_by_age_data['age'].mean())} days"

        card = dbc.Card(
            # dbc.CardHeader("Average Task Age"),
            dbc.CardBody(
                [
                    html.H5(html.Center("Average Task Age"), className="card-title"),
                    html.P(html.Center(html.Strong(tasks_by_age_value)),
                           className="card-text",
                           ),
                ]
            ),
            color="light",
            className="w-100"
        )
        return card

    def get_space_selector(self, call_type="Select"):
        if call_type == "Dropdown":
            selector = dbc.InputGroup(
                [dbc.InputGroupText("Select space(s)", className="w-100"),
                 dcc.Dropdown(self.dash_constants.get_spaces()[1:], id="selectSpace", multi=True,
                              style={"flex-grow": "1"}, value=self.dash_values.filter_spaces)],
                className="mb-3 d-flex w-100")
            return selector
        elif call_type == "Select":
            selector = dbc.InputGroup(
                [dbc.InputGroupText("Space"),
                 dbc.Select(id="selectSpace",
                            value=None,
                            options=[{"label": space, "value": space} for space in self.dash_constants.get_spaces()])],
                className="mb-3")
            return selector

    def get_company_selector(self, call_type="Select"):
        if call_type == "Dropdown":
            selector = dbc.InputGroup(
                [dbc.InputGroupText("Select company(ies)", className="w-100"),
                 dcc.Dropdown(self.dash_constants.get_companies()[1:], id="selectCompany", multi=True,
                              style={'flex-grow': '1'}, value=self.dash_values.filter_companies)],
                className="mb-3 d-flex w-100")
        elif call_type == "Select":
            selector = dbc.InputGroup(
                [dbc.InputGroupText("Company"),
                 dbc.Select(id="selectCompany",
                            value=None,
                            options=[{"label": company, "value": company} for company in
                                     self.dash_constants.get_companies()])],
                className="mb-3")

        return selector

    @staticmethod
    def get_overdue_checkbox():
        element = \
            dbc.Checkbox(id="checkOverdue", value=False, label="Only Overdue", className="mt-2")

        return element

    SELECTORS = {"W/ due date" : 1, "Only overdue" : 2, "With due date" : 3}

    def get_radio_selectors(self):
        # element = \
        #     dcc.RadioItems([key for key in DashCards.SELECTORS.keys()], "No Filter", id="radioSelectors",
        #                      labelStyle={'display': 'block'}, inputStyle={"margin-right": "7px"})

        # return element

        selector = dbc.InputGroup(
                [dbc.InputGroupText("Filters", className="w-100"),
                 dcc.Dropdown([key for key in DashCards.SELECTORS.keys()], id="radioSelectors", multi=False,
                              style={"flex-grow": "1"}, value=self.dash_values.filter_overdue)],
                className="mb-3 d-flex w-100")

        return selector

    @staticmethod
    def get_date_checkbox():
        element = \
            dbc.Checkbox(id="checkDate", value=False, label="Only Overdue", className="mt-2")
        return element

    def get_open_tasks_per_space_fig(self):
        fig = px.bar(data_frame=self.dash_values.get_open_tasks_per_space().sort_values(by=["count"]),
                     x='space',
                     y='count',
                     labels={
                         "count": "Count",
                         "space": "Space"
                     },
                     color='space',
                     hover_data=['space'],
                     )

        fig.update_layout(
            margin=dict(l=20, r=20, t=20, b=20),
            showlegend=False
        )
        return fig

    def get_stats_per_space_fig(self):
        df = self.dash_values.get_task_stats_by_space()
        """
        fig = px.bar(data_frame=self.dash_values.get_task_stats_by_space(),
                     x='date',
                     y='count',
                     labels ={
                         "count" : "Count",
                         "date" : "Date"
                     },
                     color="date")"""

        fig = go.Figure(data=[
            go.Bar(name='Overdue', x=df["date"], y=df["overdue"],
                   marker=dict(color=["#EF553B" for row in df["total"].values])),
            go.Bar(name='Total', x=df["date"], y=df["total"] - df["overdue"],
                   marker=dict(color=["#636EFA" for row in df["total"].values])),
        ])

        fig.update_layout(
            margin=dict(l=20, r=20, t=20, b=20),
            showlegend=False,
            barmode="stack"
        )

        return fig

    def get_stats_per_user_fig(self):
        df = self.dash_values.get_task_stats_by_user()
        """
        fig = px.bar(data_frame=self.dash_values.get_task_stats_by_space(),
                     x='user',
                     y='count',
                     labels ={
                         "count" : "Count",
                         "user" : "User"
                     },
                     color="date")"""

        print(df)

        fig = go.Figure(data=[
            go.Bar(name='Overdue', x=df["user"], y=df["overdue"],
                   marker=dict(color=["#EF553B" for row in df["total"].values])),
            go.Bar(name='Total', x=df["user"], y=df["total"] - df["overdue"],
                   marker=dict(color=["#636EFA" for row in df["total"].values])),
        ])

        fig.update_layout(
            margin=dict(l=20, r=20, t=20, b=20),
            showlegend=False,
            barmode="stack"
        )

        return fig

    def get_open_tasks_per_company_fig(self):
        fig = px.bar(data_frame=self.dash_values.get_task_count_by_company().sort_values(by=["count"]),
                     x='company',
                     y='count',
                     labels={
                         "count": "Count",
                         "company": "Company"
                     },
                     color='company',
                     hover_data=['company'])

        fig.update_layout(
            margin=dict(l=20, r=20, t=20, b=20),
            showlegend=False
        )

        return fig

    @staticmethod
    def SetColor(x):
        """
        Set the color of the age graph. Minus values (days in the past) are red, today is blue,
        future due dates are green.
        :param x: Integer
        :return: Color name
        """
        y = float(x)
        if y < 0:
            return "red"
        elif y == 0:
            return "blue"
        elif y > 0:
            return "green"
        else:
            return "blue"

    def get_task_count_by_age_fig(self):
        df = self.dash_values.get_task_count_by_age()

        """
        fig = go.Figure()
        fig.add_trace(
            go.Scatter(
                x=df["age"],
                y=df["count"]
            ))

        fig.add_trace(
            go.Bar(
                x=df["age"],
                y=df["count"],
                marker=dict(color=list(map(self.SetColor, df["age"].values))),
            ))"""
        df["color"] = list(map(self.SetColor, df["age"].values))
        df["date"] = df["date"].astype(str) + " (" + df["age"] + ")"
        fig = px.histogram(df, x='date', marginal="box", color="color",
                           color_discrete_sequence=["#EF553B", "#636EFA", "#00CC96"],)

        fig.update_layout(
            margin=dict(l=20, r=20, t=20, b=20),
            bargap=0,
            showlegend=False,
        )
        return fig

    def get_datatable_element(self, format_of_output="datatable"):
        l_grid_data = self.dash_values.get_grid_data(format_of_output=format_of_output)
        table = dash_table.DataTable(id="grid-table-inner",
                                     columns=[{"name": i, "id": i, "presentation": "markdown"} for i in l_grid_data],
                                     data=l_grid_data.to_dict("records"),
                                     page_size=DashCards.PAGE_SIZE,
                                     sort_action="native",
                                     sort_mode="multi",
                                     filter_action="native",
                                     row_selectable="multi",
                                     # not a good idea: fill_width=False,
                                     style_header=
                                     {  # 'fontWeight': 'bold',
                                         'fontFamily': 'Arial',
                                         'border': 'thin lightgrey solid',
                                         'backgroundColor': 'rgb(100, 100, 100)',
                                         'color': 'white'
                                     },
                                     style_cell={
                                         'whiteSpace': 'pre-line'
                                     },
                                     # style_cell={
                                     #     'fontFamily': 'Open Sans',
                                     #     'textAlign': 'left',
                                     #     'whiteSpace': 'normal',
                                     #     'overflow': 'hidden',
                                     #     'textOverflow': 'ellipsis',
                                     #     'backgroundColor': 'Rgb(230, 230, 250)',
                                     # },
                                     # style_data_conditional=[
                                     #     {
                                     #         'if ': {'row_index': 'odd'},
                                     #         'backgroundColor': 'rgb(248, 248, 248)'
                                     #     },
                                     #     # {
                                     #     # 'if ': {'column_id': 'Company'},
                                     #     # 'backgroundColor': 'rgb(255, 255, 255)',
                                     #     # 'color': 'black',
                                     #     # # 'fontWeight': 'bold',
                                     #     # 'textAlign': 'center'
                                     #     # }
                                     # ],
                                     # fixed_rows={'headers': True, 'data': 0},
                                     # virtualization=True,
                                     style_data={
                                         'whiteSpace': 'normal',
                                         'height': 'auto',  # Wrap columns
                                     },
                                     #                          css=[{
                                     #                              'selector': '.dash-spreadsheet td div',
                                     #                              'rule': '''
                                     #     line-height: 15px;
                                     #     max-height: 30px; min-height: 30px; height: 30px;
                                     #     display: block;
                                     #     overflow-y: hidden;
                                     # '''
                                     #                          }],
                                     # style_table={
                                     #     'overflowX': 'auto',
                                     #     'width': '100%',
                                     #     'margin': 'auto'}
                                     )
        return table

    def get_datatable_column(self, format_of_output="datatable"):
        if format_of_output == "datatable":
            table = self.get_datatable_element(format_of_output=format_of_output)
            column = dbc.Col(table, className="mt-3", width=12, id="grid-table")
            return column
        elif format_of_output == "table":
            column = dbc.Col([
                dbc.Table.from_dataframe(
                    self.dash_values.get_grid_data(format_of_output=format_of_output)[:DashCards.PAGE_SIZE],
                    striped=True,
                    bordered=True,
                    hover=True,
                ),
            ], className="mt-3", width=12, id="grid-table",
            )
            return column

    def get_stats_chart_rows(self):
        try:
            structure = [
                dbc.Col([html.Strong("Total tasks and overdue tasks per day")], className="text-center mt-3 pt-3", width=12),
                dbc.Col([dcc.Graph(figure=self.get_stats_per_space_fig())], width=12),
            ]
        except Exception as ex:
            logger.critical(f"Exception during Structure Creation: {ex}")
            return None

        return structure

    def get_tasks_chart_rows(self):
        try:
            structure = [
                dbc.Col([html.Strong("Open tasks per space")], className="text-center mt-3 pt-3",
                        width=6),
                dbc.Col([html.Strong("Open tasks per company")], className="text-center mt-3 pt-3",
                        width=6),
                dbc.Col([dcc.Graph(figure=self.get_open_tasks_per_space_fig())], width=6),
                dbc.Col([dcc.Graph(figure=self.get_open_tasks_per_company_fig())], width=6),
                dbc.Col([html.Strong("Tasks distribution by age")], className="text-center mt-3 pt-3", width=12),
                dbc.Col([dcc.Graph(figure=self.get_task_count_by_age_fig())], width=12),
                dbc.Col([html.Strong("Total tasks and overdue tasks per user")], className="text-center mt-3 pt-3", width=12),
                dbc.Col([dcc.Graph(figure=self.get_stats_per_user_fig())], width=12),
                dbc.Col([html.Div(html.Center(""))], width=12),
                dbc.Col([self.get_space_overdue_task_card(self.dash_values.get_open_tasks_per_space())], width=3),
                dbc.Col([self.get_company_overdue_task_card(self.dash_values.get_task_count_by_company())], width=3),
                dbc.Col(
                    [self.get_task_average_time_card(self.dash_values.get_tasks_age(), self.dash_values.filter_date)],
                    width=3),
                dbc.Col([
                    dbc.Button(id="btn_send_reminder", children=["Send Reminder"], className="w-100 h-40",
                               n_clicks=0),
                    dbc.Button(id="btn_download_selected", children=["Download selection"], className="w-100 h-40",
                               n_clicks=0, style={"margin-top": "10px"}),
                    dcc.Download(id="download_file")
                ], width=3),
                self.get_datatable_column(),
            ]
        except Exception as ex:
            logger.critical(f"Exception during Structure Creation: {ex}")
            return None

        return structure