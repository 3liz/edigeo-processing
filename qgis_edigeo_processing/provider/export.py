import traceback

from functools import cache
from pathlib import Path
from textwrap import dedent
from typing import (
    Any,
    Optional,
    Sequence,
)

from edigeo import Feature as EdigeoFeature
from edigeo import Layer as EdigeoLayer
from edigeo import ValidationMode, WriteOptions
from edigeo.extras import read_from_archive
from edigeo.types import Ring
from qgis.core import (
    Qgis,
    QgsGeometry,
    QgsPointXY,
    QgsProcessingAlgorithm,
    QgsProcessingContext,
    QgsProcessingException,
    QgsProcessingFeedback,
    QgsProcessingOutputMultipleLayers,
    QgsProcessingParameterBoolean,
    QgsProcessingParameterDefinition,
    QgsProcessingParameterFile,
    QgsProcessingParameterFolderDestination,
    QgsProcessingUtils,
)


class EdigeoExport(QgsProcessingAlgorithm):
    INPUT_FILE = "file"
    OUTPUT_FOLDER = "folder"
    ADD_TO_PROJECT = "add"

    OUTPUT_LAYERS = "layers"

    def initAlgorithm(self, config: Optional[dict] = None):
        # Input THF file
        self._add_parameter(
            QgsProcessingParameterFile(
                self.INPUT_FILE,
                "Edigeo archive or file",
                fileFilter="TAR archive (*.tar.bz2);;THF file (*.THF)",
            ),
            "Selectionne un fichier .THF ou une archive TAR",
        )

        # Output folder
        self._add_parameter(
            QgsProcessingParameterFolderDestination(
                self.OUTPUT_FOLDER,
                "Dossier de destination",
            ),
            "Dossier d'export des fichierl",
        )

        # Add to project ?
        self._add_parameter(
            QgsProcessingParameterBoolean(
                self.ADD_TO_PROJECT,
                "Add layers to project",
            ),
            "Add layers to current project",
        )

        # Output Layers
        self.addOutput(
            QgsProcessingOutputMultipleLayers(
                self.OUTPUT_LAYERS,
                "Edigeo layers",
            ),
        )

    def _add_parameter(
        self,
        parameter: QgsProcessingParameterDefinition,
        help_str: str,
    ):
        parameter.setHelp(dedent(help_str))
        self.addParameter(parameter)

    def processAlgorithm(
        self,
        parameters: dict[str, Any],
        context: QgsProcessingContext,
        feedback: QgsProcessingFeedback,
    ) -> dict[str, Any]:
        file = Path(self.parameterAsFile(parameters, self.INPUT_FILE, context))
        if not file.is_file():
            raise QgsProcessingException(f"Fichier invalide {file}")

        output_dir = Path(self.parameterAsString(parameters, self.OUTPUT_FOLDER, context))
        if not output_dir.is_dir():
            raise QgsProcessingAlgorithm(f"Repertoire invalide {output_dir}")

        add_to_project = self.parameterAsBool(parameters, self.ADD_TO_PROJECT, context)

        parser = read_from_archive(file)

        def validate(
            feat: EdigeoFeature,
            rings: Sequence[Ring],
            face: str,
        ) -> Sequence[Ring]:
            # Ideally, we should use the make_valid method from Geos/Shapely but:
            # 1. The 'structure' method is only available from Shapely 2.1
            # which is only available since Debian 'trixie'
            # 2. It is a pain to build an invalid polygon using QgsGeometry for
            # applying make_valid
            #
            # So let's cook a homemade recipy for validating rings
            try:
                # Convert each ring to QgsGeometry (Polygon)
                geoms: list[QgsGeometry] = []
                for ring, _ in rings:
                    geom = QgsGeometry()
                    result = geom.addPointsXYV2(
                        [QgsPointXY(x, y) for (x, y) in ring],
                        Qgis.WkbType.Polygon,
                    )
                    if result != Qgis.GeometryOperationResult.Success:
                        feedback.reportError(
                            f"{feat.id}/{face}: Geometry operation "
                            f"failed with error {result}"
                        )
                    else:
                        geom.convertToSingleType()
                        geoms.append(geom)

                @cache
                def area(g: QgsGeometry) -> float:
                    return g.area()

                # Order by area size in descending order (largest first)
                geoms.sort(key=lambda g: area(g), reverse=True)

                roots = [geoms[0]]
                # For eech ring check if it intersect a root
                # - if yes: add it as an inner ring of the root
                # - if no: add it as new root
                for g in geoms[1:]:
                    for root in roots:
                        if g.intersects(root):
                            result = root.addRing(g.asPolygon()[0])
                            if result != Qgis.GeometryOperationResult.Success:
                                # hum, it intersects a root but is not a child, drop it
                                feedback.reportError(f"Geometry operation failed with error {result}")
                            break
                    else:
                        # Add as a root
                        roots.append(g)

                rings = []
                for root in roots:
                    outer = True
                    for lines in root.asPolygon():
                        rings.append(([(x, y) for x, y in lines], outer))
                        outer = False

                return rings
            except Exception:
                traceback.print_exc()
                raise

        output_layers = []

        validation_mode = ValidationMode.Trust

        options = WriteOptions()
        options.mode = validation_mode

        def write_layer(layer: EdigeoLayer) -> str:
            out = output_dir.joinpath(layer.name).with_suffix(".fgb")
            with out.open("wb") as writer:
                layer.write_flatgeobuf(writer, options, validate=validate)

            if add_to_project:
                context.addLayerToLoadOnCompletion(
                    str(out),
                    context.LayerDetails(
                        layer.name,
                        context.project(),
                        "FOOBAR",
                        QgsProcessingUtils.LayerHint.Vector,
                    ),
                )
            return str(out)

        output_layers = [write_layer(layer) for layer in parser.layers() if len(layer) > 0]

        return {
            self.OUTPUT_LAYERS: output_layers,
        }

    def name(self) -> str:
        return "export"

    def displayName(self) -> str:
        return "export"

    def createInstance(self) -> "EdigeoExport":
        return EdigeoExport()

    def shortHelpString(self) -> str:
        parameters = "\n".join(f"{p.name()}: {p.help()}" for p in self.parameterDefinitions())
        returns = "\n".join(f"{o.name()}: {o.description()}" for o in self.outputDefinitions())
        return dedent(
            f"""Exporte les couches EDIGEO au format FlatGeoBuf .

                Inputs:
                    {parameters}

                Outputs:
                    {returns}
            """
        )

    def shortDescription(self) -> str:
        return "Exporte les fichiers EDIGEO au format FLatGeoBuf"
