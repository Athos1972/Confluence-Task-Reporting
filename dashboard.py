import dash
import dash_bootstrap_components as dbc
from dash import Input, Output, State, html, dcc
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
open_tasks_per_space = reporter.task_count_by_space()
open_overdue_tasks_per_space = reporter.task_overdue_count_by_space()

open_tasks_per_space_data = open_tasks_per_space

print(open_overdue_tasks_per_space, open_tasks_per_space)

app = dash.Dash(
    external_stylesheets=[dbc.themes.BOOTSTRAP],

)

active_space = ""
active_company = ""
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

OpenTasksPerSpaceFig = px.bar(data_frame=open_tasks_per_space_data, x='space', y='count', color='space', hover_data=['space'])

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
            [dbc.Col([dcc.Graph(figure=OpenTasksPerSpaceFig)], width=6),]
        ),
    ]
)


@app.callback(
    Output(component_id='callback_output', component_property='children'),
    [Input(component_id='selectCompany', component_property='value'),
     Input(component_id='selectSpace', component_property='value'),
     Input(component_id='checkOverdue', component_property='value')]
)
def select_options(selected_company, selected_space, checked_overdue):
    global active_space, active_company, overdue, open_tasks_per_space, open_tasks_per_space_data, open_overdue_tasks_per_space

    ctx = dash.callback_context
    if ctx.triggered:
        input_id = ctx.triggered[0]["prop_id"].split(".")[0]

        if input_id == "selectSpace":
            active_space = selected_space
        elif input_id == "selectCompany":
            active_company = selected_company
        elif input_id == "checkOverdue":
            overdue = not overdue
            if overdue:
                open_tasks_per_space_data = open_overdue_tasks_per_space
            else:
                open_tasks_per_space_data = open_tasks_per_space

    return ""


if __name__ == "__main__":
    # OpenTasksPerSpace = reporter.task_count_by_space()

    app.run_server(debug=True)
