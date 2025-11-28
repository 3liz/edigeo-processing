from qgis.gui import QgisInterface

from .main import Plugin


def classFactory(iface: QgisInterface) -> Plugin:
    return Plugin(iface)
