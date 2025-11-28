from qgis.core import QgsProcessingProvider
from qgis.PyQt.QtGui import QIcon

from ..utils import resources_path
from .export import EdigeoExport
from .inspect import EdigeoInspect


class Provider(QgsProcessingProvider):
    def id(self) -> str:
        return "edigeo"

    def name(str) -> str:
        return "Edigeo processing"

    def loadAlgorithms(self):
        self.addAlgorithm(EdigeoInspect())
        self.addAlgorithm(EdigeoExport())

    def icon(self) -> QIcon:
        return QIcon(str(resources_path("icon.png")))
