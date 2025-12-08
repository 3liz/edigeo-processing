from pathlib import Path
from typing import Any

from qgis.core import (
    QgsApplication,
    QgsProcessingContext,
    QgsProcessingFeedback,
)


def test_resources():
    from qgis_edigeo_processing.utils import resources_path

    icon_path = resources_path("icon.png")
    print("\n::test_resources::icon", icon_path)
    assert icon_path.exists()


def test_provider(qgis_app: QgsApplication, plugin: Any):
    reg = qgis_app.processingRegistry()

    provider = reg.providerById("edigeo")
    assert provider is not None


def test_html_report(plugin: Any, data: Path, output_dir: Path):
    # Test HTML reporting
    from qgis import processing

    context = QgsProcessingContext()
    context.setTemporaryFolder(str(output_dir))

    result = processing.run(
        "edigeo:inspect",
        {
            "file": str(data.joinpath("75103000AO01", "E000AO01.THF")),
            "folder": str(output_dir),
        },
        context=context,
    )

    html_output = Path(result.get("html"))
    assert html_output.exists()

    with html_output.open() as f:
        print("\n::test_inspect::", f.read())


def test_export(plugin: Any, data: Path, output_dir: Path):
    # Test HTML reporting
    from qgis import processing

    class Feedback(QgsProcessingFeedback):
        def reportError(self, msg: str, fatalError: bool = False):
            print("\n::test_export::error", msg)

    context = QgsProcessingContext()
    context.setTemporaryFolder(str(output_dir))

    result = processing.run(
        "edigeo:export",
        {
            "file": str(data.joinpath("75103000AO01", "E000AO01.THF")),
            "folder": str(output_dir),
            "add": False,
        },
        context=context,
        feedback=Feedback(),
    )

    outputs = result.get("layers")
    print("\n::test_export::", outputs)
    for layer in outputs:
        path = Path(layer)
        assert path.exists()
        assert path.is_relative_to(output_dir)
