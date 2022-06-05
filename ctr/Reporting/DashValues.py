import dash_bootstrap_components as dbc
from dash import html
from datetime import date

from ctr.Database.connection import SqlConnector
from ctr.Reporting import Reporter as Reporter


class DashValues:
    def __init__(self, db_connection: SqlConnector):
        self.db_connection = db_connection
        self.reporter = Reporter.TaskReporting(db_connection=self.db_connection)
        self.max_pages = None
        self.grid_data = []

    def get_max_pages(self):
        return self.max_pages

    def get_open_tasks_per_space(self, overdue=False):
        if not overdue:
            return self.reporter.task_count_by_space()
        else:
            return self.reporter.task_overdue_count_by_space()

    def get_task_count_by_company(self, overdue=False):
        if not overdue:
            return self.reporter.task_count_by_company()
        else:
            return self.reporter.task_overdue_count_by_company()

    def get_tasks_age(self, overdue=False):
        if overdue:
            return self.reporter.overdue_tasks_by_age_and_space()
        else:
            return self.reporter.tasks_by_age_and_space()

    def get_task_view(self):
        return self.reporter.get_task_view()

    def get_grid_data(self, spaces_to_filter=None, companies_to_filter=None, only_overdue=False):
        if not any(self.grid_data):
            self.grid_data = self.get_task_view()

        grid_data = self.grid_data

        page_links = grid_data["Page"].values
        page_names = grid_data["page_name"].values
        internal_ids = grid_data["task_internal_id"].values

        task_selectors = []
        page_hyperlinks = []
        for i in range(len(page_names)):
            page_name = page_names[i]
            page_link = page_links[i]
            page_hyperlinks.append(html.A([page_name], href=page_link))
            task_selectors.append(dbc.Checkbox(
                id=f"select&{internal_ids[i]}",
                value=False, ))

        grid_data = grid_data.drop(['Page', 'task_internal_id', 'page_name'], axis=1)

        grid_data["Page"] = page_hyperlinks
        grid_data["+/-"] = task_selectors

        grid_data = grid_data.reset_index(drop=True)

        if spaces_to_filter:
            grid_data = grid_data[grid_data["Space"] in spaces_to_filter]

        if companies_to_filter:
            grid_data = grid_data[grid_data["Company"] in companies_to_filter]

        if only_overdue:
            grid_data = grid_data[grid_data["Reminder"] < date.now()]

        self.max_pages = len(grid_data) // 25

        return grid_data
