from datetime import datetime

import dash
import dash_bootstrap_components as dbc
from dash import Input, Output, html, dcc, callback_context, dash_table
from ctr.Database.connection import SqlConnector
import ctr.Reporting.Reporter as Reporter
import ctr.Exploring.Explorer as Explorer
import plotly.express as px

# Loading everything
db_connection = SqlConnector()
reporter = Reporter.TaskReporting(db_connection)
explorer = Explorer.TaskExploring(db_connection)

companies = [None] + explorer.get_companies()
spaces = [None] + explorer.get_spaces()
explorer.init_user_companies()

open_tasks_per_space = reporter.task_count_by_space()
open_overdue_tasks_per_space = reporter.task_overdue_count_by_space()
open_tasks_per_company = reporter.task_count_by_company()
open_overdue_tasks_per_company = reporter.task_overdue_count_by_company()
open_tasks_per_space_data = open_tasks_per_space
open_tasks_per_company_data = open_tasks_per_company

# DASH TABLE
PAGE_SIZE = 25
ACTIVE_PAGE = 1
grid_data = explorer.get_task_view()
MAX_PAGES = len(grid_data) // 25
page_links = grid_data["page_link"].values
page_names = grid_data["page_name"].values
internal_ids = grid_data["task_internal_id"].values

checked_tasks = []

task_selectors = []
page_hyperlinks = []
for i in range(len(page_names)):
    page_name = page_names[i]
    page_link = page_links[i]
    page_hyperlinks.append(html.A([page_name], href=page_link))
    task_selectors.append(dbc.Checkbox(
        id=f"select&{internal_ids[i]}",
        value=False, ))

grid_data = grid_data.drop(['page_link', 'task_internal_id', 'page_name'], axis=1)

grid_data["page_name"] = page_hyperlinks
grid_data["check"] = task_selectors

grid_data = grid_data.reset_index(drop=True)

filtered_grid = grid_data

space_overdue_tasks_card = dbc.Card(
    dbc.CardBody(
        [
            html.H4("Space's Overdue Tasks", className="card-title"),
            html.P(html.Center(html.Strong("-")),
                   className="card-text",
                   ),
        ]
    ),
    className="w-100",
)

company_overdue_tasks_card = dbc.Card(
    dbc.CardBody(
        [
            html.H4("Company's Overdue Tasks", className="card-title"),
            html.P(html.Center(html.Strong("-")),
                   className="card-text",
                   ),
        ]
    ),
    className="w-100"
)

app = dash.Dash(
    external_stylesheets=[dbc.themes.BOOTSTRAP],
)
app.config.suppress_callback_exceptions = True

active_space = None
active_company = None
overdue = False

selectSpace = dbc.InputGroup(
    [dbc.InputGroupText("Space"),
     dbc.Select(id="selectSpace", value=None, options=[{"label": space, "value": space} for space in spaces])],
    className="mb-3")

selectCompany = dbc.InputGroup(
    [dbc.InputGroupText("Company"),
     dbc.Select(id="selectCompany", value=None, options=[{"label": company, "value": company} for company in companies])],
    className="mb-3")

checkOverdue = dbc.InputGroup(
    [dbc.Checkbox(id="checkOverdue", value=False, label="Only Overdue")],
    className="mt-2")

OpenTasksPerSpaceFig = px.bar(data_frame=open_tasks_per_space_data, x='space', y='count', color='space',
                              hover_data=['space'])

OpenTasksPerCompanyFig = px.bar(data_frame=open_tasks_per_company_data, x='company', y='count', color='company',
                                hover_data=['company'])

app.layout = dbc.Container(
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
        dbc.Row(
            [
                dbc.Col([html.Strong("Open tasks per space graph")], className="text-center mt-3 pt-3", width=6),
                dbc.Col([html.Strong("Open tasks per company graph")], className="text-center mt-3 pt-3", width=6),
                dbc.Col([dcc.Graph(figure=OpenTasksPerSpaceFig)], width=6),
                dbc.Col([dcc.Graph(figure=OpenTasksPerCompanyFig)], width=6),
                dbc.Col([space_overdue_tasks_card], width=5),
                dbc.Col([company_overdue_tasks_card], width=5),
                dbc.Col([
                    dbc.Button(id="btn_send_reminder", children=["Send Reminder"], className="w-100 h-100", n_clicks=0)
                ], width=2),
                dbc.Col([
                    dbc.Table.from_dataframe(filtered_grid[:PAGE_SIZE], striped=True, bordered=True, hover=True),
                ], className="mt-3", width=12),
            ], id="dashboard"
        ),
        dbc.Pagination(id="pagination", min_value=1, max_value=MAX_PAGES, className="justify-content-center",
                       fully_expanded=False, first_last=True, previous_next=True)
    ]

)


@app.callback(
    Output("callback_output2", "children"),
    [Input(f"select&{internal_ids[i]}", "value")
     for i in range(ACTIVE_PAGE * PAGE_SIZE, min(ACTIVE_PAGE * (PAGE_SIZE + 1), len(internal_ids)))],
)
def check_task(*args):
    global checked_tasks, PAGE_SIZE, MAX_PAGES, ACTIVE_PAGE
    print("in")
    ctx = dash.callback_context
    input_id = ctx.triggered[0]["prop_id"].split(".")[0]
    print("Task.internal_id=" + input_id[7:])


@app.callback(
    Output("grid-table", "children"),
    [Input("pagination", "active_page")],
)
def change_page(page):
    global PAGE_SIZE, MAX_PAGES, ACTIVE_PAGE

    if page:
        ACTIVE_PAGE = page
        return [
            dbc.Table.from_dataframe(filtered_grid[(page - 1) * PAGE_SIZE:page * PAGE_SIZE], striped=True,
                                     bordered=True,
                                     hover=True)]
    return [
        dbc.Table.from_dataframe(filtered_grid[:PAGE_SIZE], striped=True, bordered=True, hover=True), ]


@app.callback(
    Output(component_id='dashboard', component_property='children'),
    [Input(component_id='selectCompany', component_property='value'),
     Input(component_id='selectSpace', component_property='value'),
     Input(component_id='checkOverdue', component_property='value')]
)
def select_options(selected_company, selected_space, checked_overdue):
    global active_space, active_company, overdue, open_tasks_per_space_data, open_tasks_per_space, \
        open_overdue_tasks_per_space, OpenTasksPerSpaceFig, space_overdue_tasks_card, company_overdue_tasks_card, \
        open_tasks_per_company_data, OpenTasksPerCompanyFig, ACTIVE_PAGE, PAGE_SIZE, filtered_grid, MAX_PAGES

    ctx = dash.callback_context
    if ctx.triggered:
        input_id = ctx.triggered[0]["prop_id"].split(".")[0]

        if input_id == "selectSpace":
            active_space = selected_space
            if len(str(selected_space)) > 0:
                overdue_count = \
                    open_overdue_tasks_per_space[(open_overdue_tasks_per_space.space == selected_space)].values[0][0]
                space_overdue_tasks_card = dbc.Card(
                    dbc.CardBody(
                        [
                            html.H4("Space's Overdue Tasks", className="card-title"),
                            html.P(html.Center(html.Strong(overdue_count)),
                                   className="card-text",
                                   ),
                        ]
                    ),
                    className="w-100"
                )
        elif input_id == "selectCompany":
            active_company = selected_company
            if len(str(selected_company)) > 0:
                overdue_count = \
                    open_overdue_tasks_per_company[(open_overdue_tasks_per_company.company == selected_company)].values[
                        0][
                        0]
                company_overdue_tasks_card = dbc.Card(
                    dbc.CardBody(
                        [
                            html.H4("Company's Overdue Tasks", className="card-title"),
                            html.P(html.Center(html.Strong(overdue_count)),
                                   className="card-text",
                                   ),
                        ]
                    ),
                    className="w-100",
                )
        elif input_id == "checkOverdue":
            overdue = not overdue
            if not overdue:
                open_tasks_per_space_data = open_tasks_per_space
                open_tasks_per_company_data = open_tasks_per_company
            else:
                open_tasks_per_space_data = open_overdue_tasks_per_space
                open_tasks_per_company_data = open_overdue_tasks_per_company

            OpenTasksPerSpaceFig = px.bar(data_frame=open_tasks_per_space_data, x='space', y='count', color='space',
                                          hover_data=['space'])
            OpenTasksPerCompanyFig = px.bar(data_frame=open_tasks_per_company_data, x='company', y='count',
                                            color='company',
                                            hover_data=['company'])

        filtered_grid = grid_data
        if selected_space:
            filtered_grid = filtered_grid[filtered_grid["page_space"] == selected_space]
            MAX_PAGES = len(filtered_grid) // PAGE_SIZE

        if selected_company:
            filtered_grid = filtered_grid[filtered_grid["user_company"] == selected_company]
            MAX_PAGES = len(filtered_grid) // PAGE_SIZE

        if overdue:
            filtered_grid = filtered_grid[filtered_grid["task_due_date"] < datetime.now()]

    return [
        dbc.Col([html.Strong("Open tasks per space graph")], className="text-center mt-3 pt-3", width=6),
        dbc.Col([html.Strong("Open tasks per company graph")], className="text-center mt-3 pt-3", width=6),
        dbc.Col([dcc.Graph(figure=OpenTasksPerSpaceFig)], width=6),
        dbc.Col([dcc.Graph(figure=OpenTasksPerCompanyFig)], width=6),
        dbc.Col([space_overdue_tasks_card], width=5),
        dbc.Col([company_overdue_tasks_card], width=5),
        dbc.Col([
            dbc.Button(id="btn_send_reminder", children=["Send Reminder"], className="w-100 h-100", n_clicks=0)
        ], width=2),
        dbc.Col([
            dbc.Table.from_dataframe(filtered_grid[(ACTIVE_PAGE - 1) * PAGE_SIZE:ACTIVE_PAGE * PAGE_SIZE], striped=True,
                                     bordered=True, hover=True),
        ], className="mt-3", width=12),
    ]


@app.callback(
    Output('callback_output', 'children'),
    Input('btn_send_reminder', 'n_clicks'),
)
def send_reminder(reminder_btn):
    changed_id = [p['prop_id'] for p in callback_context.triggered][0]

    # reminder_btn = 1, as not to spam. If the user chooses a space or a company, this counter is reset and therefore
    # can send another reminder to specific space or company through active_space, active_company
    if 'btn_send_reminder' in changed_id and reminder_btn == 1:
        print("Sent Reminder!")

    return ""


if __name__ == "__main__":
    app.run_server(debug=True)
