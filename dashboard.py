import dash
import dash_bootstrap_components as dbc
from dash import Input, Output, html, dcc, callback_context
from ctr.Database.connection import SqlConnector
import ctr.Reporting.Reporter as Reporter
import ctr.Exploring.Explorer as Explorer
import plotly.express as px

# Loading everything
db_connection = SqlConnector()
reporter = Reporter.TaskReporting(db_connection)
explorer = Explorer.TaskExploring(db_connection)

companies = explorer.get_companies()
spaces = explorer.get_spaces()
explorer.init_user_companies()

open_tasks_per_space = reporter.task_count_by_space()
open_overdue_tasks_per_space = reporter.task_overdue_count_by_space()
open_tasks_per_company = reporter.task_count_by_company()
open_overdue_tasks_per_company = reporter.task_overdue_count_by_company()
open_tasks_per_space_data = open_tasks_per_space
open_tasks_per_company_data = open_tasks_per_company

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

active_space = None
active_company = None
overdue = False

selectSpace = dbc.InputGroup(
    [dbc.InputGroupText("Space"),
     dbc.Select(id="selectSpace", options=[{"label": space, "value": space} for space in spaces])],
    className="mb-3")

selectCompany = dbc.InputGroup(
    [dbc.InputGroupText("Company"),
     dbc.Select(id="selectCompany", options=[{"label": company, "value": company} for company in companies])],
    className="mb-3")

checkOverdue = dbc.InputGroup(
    [dbc.Checkbox(id="checkOverdue", label="Only Overdue")],
    className="mt-2")

OpenTasksPerSpaceFig = px.bar(data_frame=open_tasks_per_space_data, x='space', y='count', color='space',
                              hover_data=['space'])

OpenTasksPerCompanyFig = px.bar(data_frame=open_tasks_per_company_data, x='company', y='count', color='company',
                                hover_data=['company'])

app.layout = dbc.Container(
    children=[
        html.Div(id="callback_output", style={"display": "none"}),  # ignore
        # filters
        dbc.Row(
            [dbc.Col([selectSpace], width=5),
             dbc.Col([selectCompany], width=5),
             dbc.Col([checkOverdue], width=2)],
            className="pt-3"
        ),
        # charts
        dbc.Row(
            [], id="dashboard"
        ),
    ]
)


@app.callback(
    Output(component_id='dashboard', component_property='children'),
    [Input(component_id='selectCompany', component_property='value'),
     Input(component_id='selectSpace', component_property='value'),
     Input(component_id='checkOverdue', component_property='value')]
)
def select_options(selected_company, selected_space, checked_overdue):
    global active_space, active_company, overdue, open_tasks_per_space_data, open_tasks_per_space, \
        open_overdue_tasks_per_space, OpenTasksPerSpaceFig, space_overdue_tasks_card, company_overdue_tasks_card, \
        open_tasks_per_company_data, OpenTasksPerCompanyFig

    ctx = dash.callback_context
    if ctx.triggered:
        input_id = ctx.triggered[0]["prop_id"].split(".")[0]

        if input_id == "selectSpace":
            active_space = selected_space
            overdue_count = open_overdue_tasks_per_space[(open_overdue_tasks_per_space.space == selected_space)].values[0][0]
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
            overdue_count = open_overdue_tasks_per_company[(open_overdue_tasks_per_company.company == selected_company)].values[0][0]
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
            OpenTasksPerCompanyFig = px.bar(data_frame=open_tasks_per_company_data, x='company', y='count', color='company',
                                          hover_data=['company'])

    return [
        dbc.Col([html.Strong("Open tasks per space graph")], className="text-center mt-3 pt-3", width=6),
        dbc.Col([html.Strong("Open tasks per company graph")], className="text-center mt-3 pt-3", width=6),
        dbc.Col([dcc.Graph(figure=OpenTasksPerSpaceFig)], width=6),
        dbc.Col([dcc.Graph(figure=OpenTasksPerCompanyFig)], width=6),
        dbc.Col([space_overdue_tasks_card], width=5),
        dbc.Col([company_overdue_tasks_card], width=5),
        dbc.Col([
            dbc.Button(id="btn_send_reminder", children=["Send Reminder"], className="w-100 h-100", n_clicks=0)
        ], width=2)
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
    # OpenTasksPerSpace = reporter.task_count_by_space()

    app.run_server(debug=True)
