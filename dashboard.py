import dash
import dash_bootstrap_components as dbc
from dash import Input, Output,callback_context
from ctr.Database.connection import SqlConnector
from ctr.Util import logger
from ctr.Reporting.Dash import DashConstants, DashCards
from ctr.Reporting.DashValues import DashValues


# Loading datbase connection
db_connection = SqlConnector()
dash_values = DashValues(db_connection=db_connection)
dash_constants = DashConstants(db_connection=db_connection)
dash_cards = DashCards(dash_values=dash_values, dash_constants=dash_constants)


app = dash.Dash(external_stylesheets=[dbc.themes.BOOTSTRAP])
app.config.suppress_callback_exceptions = True

app.layout = dash_cards.get_layout()


@app.callback(
    Output(component_id='dashboard', component_property='children'),
    [Input(component_id='selectCompany', component_property='value'),
     Input(component_id='selectSpace', component_property='value'),
     Input(component_id='checkOverdue', component_property='value')]
)
def select_options(selected_company, selected_space, checked_overdue):
    """
    Parameters from frontend stored in filter-values for database query operations.

    :param selected_company:
    :param selected_space:
    :param checked_overdue:
    :return:
    """

    ctx = dash.callback_context
    if ctx.triggered:
        input_id = ctx.triggered[0]["prop_id"].split(".")[0]

        if input_id == "selectSpace":
            dash_values.set_filter("space", [selected_space])
        elif input_id == "selectCompany":
            dash_values.set_filter("company", [selected_company])
        elif input_id == "checkOverdue":
            dash_values.set_filter("overdue", checked_overdue)

    logger.info("Sent new result to Frontend")
    return dash_cards.get_chart_rows()


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
