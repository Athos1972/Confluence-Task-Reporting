import dash_bootstrap_components as dbc
from dash import html
from datetime import date

from ctr.Database.connection import SqlConnector
from ctr.Reporting import Reporter as Reporter
from ctr.Util import logger, global_config


class DashValues:
    def __init__(self, db_connection: SqlConnector):
        self.db_connection = db_connection
        self.reporter = Reporter.TaskReporting(db_connection=self.db_connection)
        self.max_pages = None
        self.grid_data = []
        self.filter_overdue = False
        self.filter_spaces = None
        self.filter_companies = None
        self.filter_date = False

    def set_filter(self, filter_type, filter_value):
        if filter_type == "overdue":
            self.filter_overdue = filter_value
            return

        if filter_type == "date":
            # 0 : No Filter
            # 1 : With Due Date
            # 2 : With No Date
            self.filter_date = filter_value
            return

        if filter_type == "space":
            self.filter_spaces = filter_value
            return
            
        if filter_type == "company":
            self.filter_companies = filter_value
            return

        logger.critical(f"called with filter_type = {filter_type}. Not implemented!")

    def get_max_pages(self):
        return self.max_pages

    def get_open_tasks_per_space(self):
        return self.reporter.task_count_by_space(filter_spaces=self.filter_spaces,
                                                 filter_overdue=self.filter_overdue,
                                                 filter_date=self.filter_date,
                                                 filter_companies=self.filter_companies)

    def get_task_count_by_company(self):
        return self.reporter.task_count_by_company(filter_companies=self.filter_companies,
                                                   filter_overdue=self.filter_overdue,
                                                   filter_spaces=self.filter_spaces,
                                                   filter_date=self.filter_date)

    def get_task_stats_by_space(self):
        return self.reporter.tasks_stats_by_space(filter_companies=self.filter_companies,
                                                  filter_spaces=self.filter_spaces)

    def get_task_stats_by_user(self):
        return self.reporter.tasks_stats_by_user(filter_companies=self.filter_companies,
                                                  filter_spaces=self.filter_spaces,
                                                  filter_overdue=self.filter_overdue,
                                                  filter_date=self.filter_date)

    def get_tasks_age(self):
        x = self.reporter.tasks_by_age_and_space(filter_overdue=self.filter_overdue,
                                                 filter_date=self.filter_date)
        return x

    def get_task_count_by_age(self):
        return self.reporter.task_count_by_age(filter_companies=self.filter_companies,
                                               filter_spaces=self.filter_spaces,
                                               filter_overdue=self.filter_overdue)

    def get_task_view(self):
        return self.reporter.get_tasks_view()

    def get_grid_data(self, format_of_output="table"):
        """
        :param format_of_output: "table" for HTML-Table (=default) or "datatable" for data_table-Link format
        :return:
        """
        if not any(self.grid_data):
            self.grid_data = self.get_task_view()

        grid_data = self.grid_data

        page_links = grid_data["Page"].values
        page_names = grid_data["page_name"].values
        internal_ids = grid_data["task_internal_id"].values

        task_selectors = []
        page_hyperlinks = []
        for i in range(len(page_names)):
            hyper_link = f"{global_config.get_config('CONF_BASE_URL')}{page_links[i]}"
            if format_of_output == "table":
                # build page link column
                page_name = page_names[i]
                page_link = page_links[i]
                page_hyperlinks.append(html.A([page_name],
                                              href=hyper_link))
                task_selectors.append(dbc.Checkbox(
                    id=f"select&{internal_ids[i]}",
                    value=False, ))
            elif format_of_output == "datatable":
                page_hyperlinks.append(f"[{page_names[i]}]({hyper_link})")
                task_selectors.append(False)
            else:
                logger.critical(f"Format of output-table unknown: {format_of_output}. Page-names will be empty.")
            # Build task selector cell/column

        grid_data = grid_data.drop(['Page', 'task_internal_id', 'page_name', "Second", "Reminder"], axis=1)

        grid_data["Page"] = page_hyperlinks

        if format_of_output == "table":
            grid_data["+/-"] = task_selectors

        grid_data = grid_data.reset_index(drop=True)

        if self.filter_spaces:
            grid_data = grid_data[grid_data["Space"].isin(self.filter_spaces)]

        if self.filter_companies:
            grid_data = grid_data[grid_data["Company"].isin(self.filter_companies)]

        if self.filter_overdue:
            grid_data = grid_data[grid_data["Due"] < date.today()]

        if self.filter_date == 1:
            grid_data = grid_data[grid_data["Due"].isna()]

        if self.filter_date == 2:
            grid_data = grid_data[grid_data["Due"].notna()]

        self.max_pages = len(grid_data) // 25

        return grid_data
