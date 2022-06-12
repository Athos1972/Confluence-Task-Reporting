from ctr.Database.connection import SqlConnector
from ctr.Reporting.Reporter import PageReporting
from ctr.Reporting.Reporter import UserReporting
from ctr.Reporting.DashValues import DashValues
from ctr.Util import logger
import dash_bootstrap_components as dbc
from dash import html, dcc, dash_table
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
    def get_task_average_time_card(tasks_by_age_data=None):
        if not any(tasks_by_age_data):
            tasks_by_age_data = {"age": 0}
        card = dbc.Card(
            # dbc.CardHeader("Average Task Age"),
            dbc.CardBody(
                [
                    html.H5(html.Center("Average Task Age"), className="card-title"),
                    html.P(html.Center(html.Strong(f"{int(tasks_by_age_data['age'].mean())} days")),
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
            # FIXME: Works but looks terrible. The DIV should look nicer. Also no callback implemented yet.
            selector = html.Div([
                "Select space(s)",
                dcc.Dropdown(self.dash_constants.get_spaces()[1:], id="space_selector", multi=True), ])
            return selector
        elif call_type == "Select":
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

    @staticmethod
    def get_overdue_checkbox():
        element = dbc.InputGroup(
            [dbc.Checkbox(id="checkOverdue", value=False, label="Only Overdue")],
            className="mt-2")
        return element

    def get_open_tasks_per_space_fig(self):
        fig = px.bar(data_frame=self.dash_values.get_open_tasks_per_space(),
                     x='space',
                     y='count',
                     color='space',
                     hover_data=['space'])
        return fig

    def get_open_tasks_per_company_fig(self):
        fig = px.bar(data_frame=self.dash_values.get_task_count_by_company(),
                     x='company',
                     y='count',
                     color='company',
                     hover_data=['company'])
        return fig

    def get_datatable_element(self, format_of_output="datatable"):
        l_grid_data = self.dash_values.get_grid_data(format_of_output=format_of_output)
        table = dash_table.DataTable(id="grid-table-inner",
                                     columns=[{"name": i, "id": i, "presentation": "markdown"} for i in l_grid_data],
                                     data=l_grid_data.to_dict("records"),
                                     page_size=DashCards.PAGE_SIZE,
                                     sort_action="native",
                                     sort_mode="multi",
                                     row_selectable="multi",
                                     # not a good idea: fill_width=False,
                                     style_header=
                                     {  # 'fontWeight': 'bold',
                                         'fontFamily': 'Arial',
                                         'border': 'thin lightgrey solid',
                                         'backgroundColor': 'rgb(100, 100, 100)',
                                         'color': 'white'
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

    def get_chart_rows(self):
        try:
            structure = [
                dbc.Col([html.Strong("Open tasks per space")], className="text-center mt-3 pt-3",
                        width=6),
                dbc.Col([html.Strong("Open tasks per company")], className="text-center mt-3 pt-3",
                        width=6),
                dbc.Col([dcc.Graph(figure=self.get_open_tasks_per_space_fig())], width=6),
                dbc.Col([dcc.Graph(figure=self.get_open_tasks_per_company_fig())], width=6),
                dbc.Col([self.get_space_overdue_task_card(self.dash_values.get_open_tasks_per_space())], width=3),
                dbc.Col([self.get_company_overdue_task_card(self.dash_values.get_task_count_by_company())], width=3),
                dbc.Col([self.get_task_average_time_card(self.dash_values.get_tasks_age())], width=3),
                dbc.Col([
                    dbc.Button(id="btn_send_reminder", children=["Send Reminder"], className="w-100 h-60",
                               n_clicks=0)
                ], width=3),
                self.get_datatable_column(),
            ]
        except Exception as ex:
            logger.critical(f"Exception during Structure Creation: {ex}")
            return None

        return structure

    def get_layout(self):
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
                dbc.Row(self.get_chart_rows(),
                        id="dashboard"),
                # dbc.Row(self.get_datatable_column())
                # dbc.Pagination(id="pagination",
                #                min_value=1,
                #                max_value=self.dash_values.get_max_pages(),
                #                className="justify-content-center",
                #                fully_expanded=False,
                #                first_last=True,
                #                previous_next=True)
            ]

        )

        return layout
