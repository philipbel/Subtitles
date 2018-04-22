from PyQt5.QtCore import QRunnable, QObject
from PyQt5.Qt import pyqtSlot, pyqtSignal, QErrorMessage
import traceback
from log import logger

#
# From https://martinfitzpatrick.name/article/multithreading-pyqt-applications-with-qthreadpool/
#


class ErrorDetails(object):
    def __init__(self, exception, error_message, details):
        self.exception = exception
        self.error_message = error_message
        self.details = details


class WorkerSignals(QObject):
    success = pyqtSignal(object)
    error = pyqtSignal(ErrorDetails)

    def __init__(self):
        super().__init__()


class Worker(QRunnable):
    def __init__(self, func, *args, **kwargs):
        super().__init__()
        self.func = func
        self.args = args
        self.kwargs = kwargs
        self.on = WorkerSignals()
        # self.setAutoDelete(False)

    @pyqtSlot()
    def run(self):
        logger.debug("Running")
        try:
            logger.debug("Invoking func, args={}, kwargs={}".format(
                self.args, self.kwargs
            ))
            result = self.func(*self.args, **self.kwargs)
        except Exception as e:
            logger.error("Got exception from func: {}".format(e))
            details = ErrorDetails(exception=e,
                                   error_message=str(e),
                                   details=traceback.format_exc())
            self.on.error.emit(details)
        else:
            logger.debug("func finished")
            try:
                self.on.success.emit(result)
            except Exception as e:
                logger.error("Success function exception: {}".format(e))
        logger.debug("Worker returning")

    def __del__(self):
        logger.debug("")

    def getErrorFunc(self, message):
        def error_func(error_details):
            # TODO: Display the error message to the user
            msg = "Error: {}, {}\n{}".format(
                message,
                error_details.error_message,
                error_details.details)
            logger.error(msg)
            QErrorMessage.qtHandler().showMessage(msg)
        return error_func
