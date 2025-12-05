from io import BytesIO
from pathlib import Path
from textwrap import dedent
from typing import (
    Any,
    Optional,
)

import edigeo

from edigeo.extras import read_from_archive
from edigeo.report import ValidationError, create_report
from qgis.core import (
    QgsGeometry,
    QgsProcessingAlgorithm,
    QgsProcessingContext,
    QgsProcessingException,
    QgsProcessingFeedback,
    QgsProcessingOutputHtml,
    QgsProcessingParameterDefinition,
    QgsProcessingParameterFile,
    QgsProcessingParameterFolderDestination,
)

from .. import utils
from .json2html import json2html


class EdigeoInspect(QgsProcessingAlgorithm):
    INPUT_FILE = "file"
    OUTPUT_FOLDER = "folder"

    OUTPUT_HTML = "html"

    def initAlgorithm(self, config: Optional[dict] = None):
        # Input THF file
        self._add_parameter(
            QgsProcessingParameterFile(
                self.INPUT_FILE,
                "Edigeo archive or file",
                fileFilter="TAR archive (*.tar.bz2);;THF file (*.THF)",
            ),
            "Sélectionne un fichier .THF ou une archive TAR",
        )

        # Output folder
        self._add_parameter(
            QgsProcessingParameterFolderDestination(
                self.OUTPUT_FOLDER,
                "Dossier de destination",
            ),
            "Dossier d'export des fichier",
        )

        # Output HTML
        self.addOutput(
            QgsProcessingOutputHtml(
                self.OUTPUT_HTML,
                "Report EDIGEO Html",
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
            raise QgsProcessingException(f"Ficher invalide {file}")

        output_dir = Path(self.parameterAsString(parameters, self.OUTPUT_FOLDER, context))
        if not output_dir.is_dir():
            raise QgsProcessingAlgorithm(f"Repertoire invalide {output_dir}")

        parser = read_from_archive(file)

        writer = BytesIO()

        def inspect(
            feat: edigeo.Feature,
            mode: edigeo.ValidationMode,
            errors: list[ValidationError],
        ):
            writer.seek(0)
            writer.truncate(0)

            if feat.write_wkb_geom(
                writer,
                mode=mode,
                inspect=lambda fea, st, pfe: errors.append(
                    {
                        "rid": feat.id,
                        "face": pfe,
                        "status": st[0],
                        "arc": st[1],
                    }
                ),
            ):
                # Check geometry validity (i.e overlapping polygons)
                geom = QgsGeometry()
                geom.fromWkb(writer.getvalue())
                if not geom.isGeosValid():
                    errors.append(
                        {
                            "rid": feat.id,
                            "face": "",
                            "status": "Invalid",
                            "arc": "",
                        }
                    )

        report = create_report(parser, edigeo.ValidationMode.Trust, inspect)

        html_output = Path(output_dir).joinpath(f"{file.stem}-report.html")

        utils.log(f"Writing EDIGEO report to {html_output}")

        with html_output.open("w") as out:
            name = report["name"]
            extent = ", ".join(f"{x:.6f}" for x in report["extent"])
            out.write(
                dedent(f"""
                <h1>{name} EDIGEO Report</h1>
                <div id=edigeo_meta>
                    <span id="edigeo_name">Name: {name}</span><br/>
                    <span id="edigeo_author">Author: {report["author"]}</span><br/>
                    <span id="edigeo_version">Version: {report["edigeo_version"]}</span><br/>
                    <span id="edigeo_version_date">Version date: {report["edigeo_version_date"]}</span><br/>
                    <span id="edigeo_crs">Crs: {report["crs"]}</span><br/>
                    <span id="edigeo_extent">Extent: {extent}</span></br>
                </div>
                <h2>Layers</h2>
                <div id=edigeo_layers>
                    {json2html(report["layers"], clubbing=True)}
                </div>
                """)
            )

        return {
            self.OUTPUT_HTML: str(html_output),
        }

    def name(self) -> str:
        return "inspect"

    def displayName(self) -> str:
        return "inspect"

    def createInstance(self) -> "EdigeoInspect":
        return EdigeoInspect()

    def shortHelpString(self) -> str:
        parameters = "\n".join(f"{p.name()}: {p.help()}" for p in self.parameterDefinitions())
        returns = "\n".join(f"{o.name()}: {o.description()}" for o in self.outputDefinitions())
        return dedent(
            f"""Inspecte un fichier EDIGEO et retourne un rapport HTML.

                Inputs:
                    {parameters}

                Outputs:
                    {returns}
            """
        )

    def shortDescription(self) -> str:
        return "Inspect un fichier EDIGEO et retourne un rapport HTML"
