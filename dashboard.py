from datetime import date

import dash
import dash_bootstrap_components as dbc
import numpy as np
from dash import Input, Output, html, dcc, callback_context, dash_table
from ctr.Database.connection import SqlConnector
import ctr.Reporting.Reporter as Reporter
from ctr.Reporting.Reporter import PageReporting
from ctr.Reporting.Reporter import UserReporting
from ctr.Reporting.Dash import DashConstants, DashCards
from ctr.Reporting.DashValues import DashValues

import plotly.express as px

# Loading everything
db_connection = SqlConnector()
reporter = Reporter.TaskReporting(db_connection)
user_reporter = UserReporting(db_connection=db_connection)
page_reporter = PageReporting(db_connection=db_connection)
dash_values = DashValues(db_connection=db_connection)
dash_constants = DashConstants(db_connection=db_connection)
dash_cards = DashCards(dash_values=dash_values, dash_constants=dash_constants)

# Get static values
companies = dash_constants.get_companies() # [None] + user_reporter.get_companies()
spaces = dash_constants.get_spaces()  # [None] + page_reporter.get_spaces()

# Get all base values
open_tasks_per_space = dash_values.get_open_tasks_per_space() # reporter.task_count_by_space()
open_overdue_tasks_per_space = dash_values.get_open_tasks_per_space(overdue=True)  # reporter.task_overdue_count_by_space()
open_tasks_per_company = dash_values.get_task_count_by_company()  # reporter.task_count_by_company()
open_overdue_tasks_per_company = dash_values.get_task_count_by_company(overdue=True)  # reporter.task_overdue_count_by_company()
overdue_tasks_age = dash_values.get_tasks_age(overdue=True)  # reporter.overdue_tasks_by_age_and_space()
tasks_age = dash_values.get_tasks_age(overdue=False)         #reporter.tasks_by_age_and_space()

open_tasks_per_space_data = open_tasks_per_space
open_tasks_per_company_data = open_tasks_per_company
tasks_by_age_data = tasks_age

# DASH TABLE
PAGE_SIZE = DashCards.PAGE_SIZE
ACTIVE_PAGE = 1
checked_tasks = []
filtered_grid = dash_values.get_grid_data()    # grid_data
MAX_PAGES = dash_values.get_max_pages()

space_overdue_tasks_card = dash_cards.get_space_overdue_task_card()
company_overdue_tasks_card = dash_cards.get_company_overdue_task_card()
task_average_time_card = dash_cards.get_task_average_time_card(dash_values.get_tasks_age(overdue=False))


app = dash.Dash(
    external_stylesheets=[dbc.themes.BOOTSTRAP],
)
app.config.suppress_callback_exceptions = True

active_space = None
active_company = None
overdue = False

# selectSpace = dash_cards.get_space_selector()
# selectCompany = dash_cards.get_company_selector()
# checkOverdue = dash_cards.get_overdue_checkbox()
OpenTasksPerSpaceFig = dash_cards.get_open_tasks_per_space_fig()
OpenTasksPerCompanyFig = dash_cards.get_open_tasks_per_company_fig()

app.layout = dash_cards.get_layout(None, None, False)
internal_ids = dash_values.get_task_view()["task_internal_id"].values

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
        open_tasks_per_company_data, OpenTasksPerCompanyFig, ACTIVE_PAGE, PAGE_SIZE, filtered_grid, MAX_PAGES, \
        tasks_by_age_data, task_average_time_card

    ctx = dash.callback_context
    if ctx.triggered:
        input_id = ctx.triggered[0]["prop_id"].split(".")[0]

        if input_id == "selectSpace":
            active_space = selected_space
            if overdue:
                tasks_by_age_data = overdue_tasks_age
            else:
                tasks_by_age_data = tasks_age
            if len(str(selected_space)) > 0:
                overdue_count = \
                    open_overdue_tasks_per_space[(open_overdue_tasks_per_space.space == selected_space)].values[0][0]
                space_overdue_tasks_card = dash_cards.get_space_overdue_task_card(overdue_count)
                tasks_by_age_data = tasks_by_age_data[tasks_by_age_data["page_space"] == selected_space]
            else:
                space_overdue_tasks_card = dash_cards.get_space_overdue_task_card()
        elif input_id == "selectCompany":
            active_company = selected_company
            if len(str(selected_company)) > 0:
                overdue_count = \
                    open_overdue_tasks_per_company[(open_overdue_tasks_per_company.company == selected_company)].values[
                        0][
                        0]
                company_overdue_tasks_card = dash_cards.get_company_overdue_task_card(overdue_value=overdue_count)
            else:
                company_overdue_tasks_card = dash_cards.get_company_overdue_task_card()
        elif input_id == "checkOverdue":
            overdue = not overdue
            open_tasks_per_space_data = dash_values.get_open_tasks_per_space(overdue=overdue)
            open_tasks_per_company_data = dash_values.get_task_count_by_company(overdue=overdue)
            OpenTasksPerSpaceFig = dash_cards.get_open_tasks_per_space_fig(overdue=overdue)
            OpenTasksPerCompanyFig = dash_cards.get_open_tasks_per_company_fig(overdue=overdue)
            tasks_by_age_data = dash_values.get_tasks_age(overdue=overdue)
            if len(str(active_space)) > 0:
                tasks_by_age_data = tasks_by_age_data[tasks_by_age_data["page_space"] == active_space]

        filtered_grid = dash_values.get_grid_data(spaces_to_filter=selected_space,
                                                  companies_to_filter=selected_company,
                                                  only_overdue=overdue)

        if len(tasks_by_age_data) == 0:
            task_average_time_card = dash_cards.get_task_average_time_card()
        else:
            task_average_time_card = dash_cards.get_task_average_time_card(tasks_by_age_data=tasks_by_age_data)

    return dash_cards.get_chart_rows(spaces=selected_space, companies=selected_company, overdue=overdue)


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
