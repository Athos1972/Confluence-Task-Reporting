import dash
import dash_bootstrap_components as dbc
from dash import Input, Output, callback_context, dcc, html
from ctr.Database.connection import SqlConnector
from ctr.Reporting.DashPages import DashPages
from ctr.Util import logger
from ctr.Util.Util import Util
from ctr.Reporting.Dash import DashConstants, DashCards
from ctr.Reporting.DashValues import DashValues


# Loading database connection
db_connection = SqlConnector()
Util.load_env_file()
dash_values = DashValues(db_connection=db_connection)
dash_constants = DashConstants(db_connection=db_connection)
dash_cards = DashCards(dash_values=dash_values, dash_constants=dash_constants)
dash_pages = DashPages(dash_cards=dash_cards)

ACTIVE_ROUTE = "/"

app = dash.Dash(external_stylesheets=[dbc.themes.BOOTSTRAP])
app.config.suppress_callback_exceptions = True

app.layout = html.Div([
    # represents the browser address bar and doesn't render anything
    dcc.Location(id='url', refresh=False),

    # content will be rendered in this element
    html.Div(id='page-content')
])


@app.callback(Output('page-content', 'children'),
              [Input('url', 'pathname')])
def display_page(pathname):
    global ACTIVE_ROUTE
    ACTIVE_ROUTE = pathname
    return dash_pages.get_layout(pathname)

@app.callback(
    Output(component_id='dashboard', component_property='children'),
    [Input(component_id='selectCompany', component_property='value'),
     Input(component_id='selectSpace', component_property='value'),
     Input(component_id='radioSelectors', component_property='value'),],
    prevent_initial_call=True
)
def select_options(selected_company, selected_space, radio_selector):
    """
    Parameters from frontend stored in filter-values for database query operations.

    :param selected_company:
    :param selected_space:
    :param checked_overdue:
    :param checked_date
    :return:
    """
    global ACTIVE_ROUTE

    route_to_row = {"/" : dash_cards.get_tasks_chart_rows,
                "/tasks": dash_cards.get_tasks_chart_rows,
                    "/stats": dash_cards.get_stats_chart_rows}
    selectors = DashCards.SELECTORS
    ctx = dash.callback_context
    if ctx.triggered:
        input_id = ctx.triggered[0]["prop_id"].split(".")[0]

        if input_id == "selectSpace":
            dash_values.set_filter("space", selected_space)
        elif input_id == "selectCompany":
            print(selected_company)
            dash_values.set_filter("company", selected_company)
        elif input_id == "radioSelectors":
            if selectors[radio_selector] == 2:
                dash_values.set_filter("overdue", True)
                dash_values.set_filter("date", False)
            elif selectors[radio_selector] == 1:
                dash_values.set_filter("overdue", False)
                dash_values.set_filter("date", True)
            else:
                dash_values.set_filter("overdue", False)
                dash_values.set_filter("date", False)

    logger.info("Sent new result to Frontend")
    return route_to_row[ACTIVE_ROUTE]()


@app.callback(
    Output('callback_output', 'children'),
    [Input('btn_send_reminder', 'n_clicks')],
    prevent_initial_call=True
)
def process_buttons(btn):
    changed_id = [p['prop_id'] for p in callback_context.triggered][0]
    # reminder_btn = 1, as not to spam. If the user_tasks chooses a space or a company,
    # this counter is reset and therefore can send another reminder to specific space or
    # company through active_space, active_company
    if 'btn_send_reminder' in changed_id and btn == 1:
        print("Sent Reminder!")

    return ""


@app.callback(
    Output('download_file', 'data'),
    Input("btn_download_selected", "n_clicks"),
    prevent_initial_call=True
)
def process_download(n_clicks):
    return dcc.send_data_frame(dash_values.get_grid_data().to_excel, "myexcel.xlsx")


if __name__ == "__main__":
    app.run_server(debug=True)
