import dash
import dash_bootstrap_components as dbc
from dash import Input, Output,callback_context
from ctr.Database.connection import SqlConnector
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

app = dash.Dash(external_stylesheets=[dbc.themes.BOOTSTRAP])
app.config.suppress_callback_exceptions = True

app.layout = dash_cards.get_layout()


@app.callback(
    Output(component_id='dashboard', component_property='children'),
    [Input(component_id='selectCompany', component_property='value'),
     Input(component_id='selectSpace', component_property='value'),
     Input(component_id='checkOverdue', component_property='value'),
     Input(component_id='checkDate', component_property='value')]
)
def select_options(selected_company, selected_space, checked_overdue, checked_date):
    """
    Parameters from frontend stored in filter-values for database query operations.

    :param selected_company:
    :param selected_space:
    :param checked_overdue:
    :param checked_date
    :return:
    """

    ctx = dash.callback_context
    if ctx.triggered:
        input_id = ctx.triggered[0]["prop_id"].split(".")[0]

        if input_id == "selectSpace":
            dash_values.set_filter("space", selected_space)
        elif input_id == "selectCompany":
            print(selected_company)
            dash_values.set_filter("company", selected_company)
        elif input_id == "checkOverdue":
            dash_values.set_filter("overdue", checked_overdue)
        elif input_id == "checkDate":
            dash_values.set_filter("date", checked_date)

    logger.info("Sent new result to Frontend")
    return dash_cards.get_chart_rows()


@app.callback(
    Output('callback_output', 'children'),
    Input('btn_send_reminder', 'n_clicks'),
)
def send_reminder(reminder_btn):
    changed_id = [p['prop_id'] for p in callback_context.triggered][0]

    # reminder_btn = 1, as not to spam. If the user_tasks chooses a space or a company, this counter is reset and therefore
    # can send another reminder to specific space or company through active_space, active_company
    if 'btn_send_reminder' in changed_id and reminder_btn == 1:
        print("Sent Reminder!")

    return ""


# @app.callback(
#     Output('datatable-row-ids-container', 'children'),
#     Input('datatable-row-ids', 'derived_virtual_row_ids'),
#     Input('datatable-row-ids', 'selected_row_ids'),
#     Input('datatable-row-ids', 'active_cell'))
# def update_graphs(row_ids, selected_row_ids, active_cell):
#     return
    # # JUST AN EXAMPLE IMPLEMENTATION - NEEDS TO BE ADJUSTED TO Confluence-Task-Reporting!
    # # SOURCE: https://dash.plotly.com/datatable/interactivity
    #
    # # When the table is first rendered, `derived_virtual_data` and
    # # `derived_virtual_selected_rows` will be `None`. This is due to an
    # # idiosyncrasy in Dash (unsupplied properties are always None and Dash
    # # calls the dependent callbacks when the component is first rendered).
    # # So, if `rows` is `None`, then the component was just rendered
    # # and its value will be the same as the component's dataframe.
    # # Instead of setting `None` in here, you could also set
    # # `derived_virtual_data=df.to_rows('dict')` when you initialize
    # # the component.
    # selected_id_set = set(selected_row_ids or [])
    #
    # if row_ids is None:
    #     dff = df
    #     # pandas Series works enough like a list for this to be OK
    #     row_ids = df['id']
    # else:
    #     dff = df.loc[row_ids]
    #
    # active_row_id = active_cell['row_id'] if active_cell else None
    #
    # colors = ['#FF69B4' if id == active_row_id
    #           else '#7FDBFF' if id in selected_id_set
    #           else '#0074D9'
    #           for id in row_ids]
    #
    # return [
    #     dcc.Graph(
    #         id=column + '--row-ids',
    #         figure={
    #             'data': [
    #                 {
    #                     'x': dff['country'],
    #                     'y': dff[column],
    #                     'type': 'bar',
    #                     'marker': {'color': colors},
    #                 }
    #             ],
    #             'layout': {
    #                 'xaxis': {'automargin': True},
    #                 'yaxis': {
    #                     'automargin': True,
    #                     'title': {'text': column}
    #                 },
    #                 'height': 250,
    #                 'margin': {'t': 10, 'l': 10, 'r': 10},
    #             },
    #         },
    #     )
    #     # check if column exists - user_tasks may have deleted it
    #     # If `column.deletable=False`, then you don't
    #     # need to do this check.
    #     for column in ['pop', 'lifeExp', 'gdpPercap'] if column in dff
    # ]

if __name__ == "__main__":
    app.run_server(debug=True)
