

from qgis.core import QgsProcessingProvider
from qgis.PyQt.QtGui import QIcon

from ..utils import resources_path


class Provider(QgsProcessingProvider):

    def id(self) -> str:
        return "edigeo_processing"

    def name(str) -> str:
        return "Edigeo processing"

    def loadAlgorithms(self):
        pass

    def icon(self) -> QIcon:
        return QIcon(str(resources_path("icons", "icon.png")))

