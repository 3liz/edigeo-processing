from typing import (
    Optional,
)

from qgis.core import QgsApplication
from qgis.gui import QgisInterface

from . import utils
from .provider import Provider


class Plugin:
    def __init__(self, iface: QgisInterface):
        self.provider: Optional[Provider] = None
        utils.log("Initializing EDIGEO processing plugin")

    def initGui(self):
        self.initProcessing()

    def initProcessing(self):
        # Create the provider(s)
        # NOTE: keep a reference to the provider
        utils.log("Registering EDIGEO processing provider")
        self.provider = Provider()
        # And register it
        QgsApplication.processingRegistry().addProvider(self.provider)

    def unload(self):
        if self.provider:
            QgsApplication.processingRegistry().removeProvider(self.provider)
