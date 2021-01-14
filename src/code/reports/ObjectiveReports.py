from threading import Thread
from datetime import datetime
from os import path

from src import constants
from src.logs import logger
from src.code.utils.utils import analyze_images_test_results, add_filenames_to_data
from src.code.utils.excel_tools import export_to_excel_file

from src.gui.utils_gui import send_progress_to_gui, send_error_to_gui


def _generate_obj_report(templ_data: dict, report_templ_file: str, out_dir, gui_window=None, gui_event=None):
    logger.info("Creating object... ")

    new_report = ObjectiveReports(templ_data, report_templ_file, out_dir, gui_window, gui_event)

    logger.info("Creating Presentation... ")
    new_report.generate_report()

    del new_report


def generate_obj_report(templ_data: dict, report_templ_file: str, out_dir, gui_window=None, gui_event=None):
    obj_thread = Thread(target=_generate_obj_report,
                        args=(templ_data, report_templ_file, out_dir, gui_window, gui_event),
                        daemon=True)
    obj_thread.name = 'ObjectiveReportsGeneration'

    logger.info(f"Starting {obj_thread.name} Thread")
    obj_thread.start()

    # TODO: Kill thread after it is finished


# Static method
def skipped_cases_to_str(skipped_cases):
    output_str = ''

    for case in skipped_cases:
        try:
            parameter = f"> {case['param']}"
        except KeyError:
            parameter = ''

        output_str += f"Skipped: {case['test_type']} > {case['light_temp']} > {case['lux']} {parameter}\n"
        try:
            output_str += f"Results file: {case['results_file']}"
        except KeyError:
            pass

        output_str += f"Reason: {case['reason']}\n\n"

    return output_str.strip()


# Objective Reports class
class ObjectiveReports:
    def __init__(self, templ_data: dict, report_templ_file: str, out_dir, gui_window=None, gui_event=None):
        self.templ_data = templ_data
        self.out_dir = path.normpath(out_dir)
        self.report_name = path.basename(report_templ_file).split('.')[0]  # Name of report requirements

        self.gui_window = gui_window
        self.gui_event = gui_event
        self.progress = 0

        logger.debug("ObjectiveReports Initialized")

    def generate_report(self):
        if self.gui_window is not None and self.gui_event is not None:
            send_progress_to_gui(self.gui_window, self.gui_event, self.progress, 'Starting')

        self.progress += 10  # 10%
        send_progress_to_gui(self.gui_window, self.gui_event, self.progress, 'Adding filenames to data...')

        logger.debug(f'before file data: \n{self.templ_data}')
        add_filenames_to_data(self.templ_data, self.out_dir)
        logger.debug(f'after file data: \n{self.templ_data}')

        self.progress += 10  # 20%
        send_progress_to_gui(self.gui_window, self.gui_event, self.progress, 'Getting images analysis data...')

        # Use images analysis data and insert it into templ_data
        skipped_cases = analyze_images_test_results(self.templ_data)[1]

        logger.debug(f'With analysis: \n{self.templ_data}')

        report_filename = f"Report_{self.report_name}_{datetime.now().strftime('%Y%m%d-%H%M%S')}"

        excel_filename = report_filename + '.xlsx'
        excel_file_path = path.realpath(path.join(self.out_dir, path.pardir, excel_filename))

        self.progress += 70  # 90%
        send_progress_to_gui(self.gui_window, self.gui_event, self.progress, 'Generating report...')

        export_to_excel_file(self.templ_data, excel_file_path, add_images_bool=True)

        self.progress += 5  # 95%
        send_progress_to_gui(self.gui_window, self.gui_event, self.progress, 'Finishing...')

        # Done
        if len(skipped_cases) > 0:
            send_error_to_gui(self.gui_window, self.gui_event, "Cases errors:", skipped_cases_to_str(skipped_cases))

        self.progress += 5  # 100%
        send_progress_to_gui(self.gui_window, self.gui_event, self.progress, 'Done', 'new_file', excel_file_path)
