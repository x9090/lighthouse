import os
import logging

from lighthouse.util.qt import *
from lighthouse.painting import CoveragePainter
from lighthouse.director import CoverageDirector
from lighthouse.coverage import DatabaseCoverage
from lighthouse.metadata import DatabaseMetadata

from lighthouse.util.disassembler import disassembler, DisassemblerContextAPI

logger = logging.getLogger("Lighthouse.Context")

#------------------------------------------------------------------------------
# Lighthouse Session Context
#------------------------------------------------------------------------------

class LighthouseContext(object):
    """
    A database/binary-unique instance of Lighthouse and its subsystems.
    """

    def __init__(self, core, dctx):
        disassembler[self] = DisassemblerContextAPI(dctx)
        self.core = core
        self.dctx = dctx
        self._started = False

        # the database metadata cache
        self.metadata = DatabaseMetadata(self)

        # the coverage engine
        self.director = CoverageDirector(self.metadata, self.core.palette)

        # the coverage painter
        self.painter = CoveragePainter(self, self.director, self.core.palette)

        # the coverage overview widget
        self.coverage_overview = None

        # the directory to start the coverage file dialog in
        self._last_directory = None

    @property
    def palette(self):
        return self.core.palette

    def start(self):
        """
        One-time activation a Lighthouse context and its subsystems.
        """
        if self._started:
            return
        self.core.palette.warmup()
        self.metadata.start()
        self.director.start()
        self.painter.start()

        # TODO/BINJA remove this ASAP, or find a better workaround... I hate having this here
        if disassembler.NAME == "BINJA":
            disassembler.hide_dockable("Feature Map")

        self._started = True

    def terminate(self):
        """
        Spin down any session subsystems before the session is deleted.
        """
        self.painter.terminate()
        self.director.terminate()
        self.metadata.terminate()

    def select_coverage_files(self):
        """
        Prompt a file selection dialog, returning file selections.

        NOTE: This saves & reuses the last known directory for subsequent uses.
        """
        if not self._last_directory:
            self._last_directory = disassembler[self].get_database_directory()

        # create & configure a Qt File Dialog for immediate use
        file_dialog = QtWidgets.QFileDialog(
            None,
            'Open code coverage file',
            self._last_directory,
            'All Files (*.*)'
        )
        file_dialog.setFileMode(QtWidgets.QFileDialog.ExistingFiles)

        # prompt the user with the file dialog, and await filename(s)
        filenames, _ = file_dialog.getOpenFileNames()

        #
        # remember the last directory we were in (parsed from a selected file)
        # for the next time the user comes to load coverage files
        #

        if filenames:
            self._last_directory = os.path.dirname(filenames[0]) + os.sep

        # log the captured (selected) filenames from the dialog
        logger.debug("Captured filenames from file dialog:")
        for name in filenames:
            logger.debug(" - %s" % name)

        # return the captured filenames
        return filenames

