# -*- coding: utf-8 -*-

"""
JSON 2 HTML Converter
=====================

(c) Varun Malhotra 2013-2024
Source Code: https://github.com/softvar/json2html


Contributors:
-------------
1. Michel Müller (@muellermichel), https://github.com/softvar/json2html/pull/2
2. Daniel Lekic (@lekic), https://github.com/softvar/json2html/pull/17

LICENSE: MIT
--------
"""

from html import escape as html_escape
from typing import (
    Any,
    Collection,
    Optional,
    Sequence,
)


class Json2Html:
    def __init__(
        self,
        table_attributes: str = 'border="1"',
        clubbing: bool = True,
        escape: bool = True,
    ):
        # table attributes such as class, id, data-attr-*, etc.
        # eg: table_attributes = 'class = "table table-bordered sortable"'
        self.table_init_markup = "<table %s>" % table_attributes
        self.clubbing = clubbing
        self.escape = escape

    def column_headers_from_list_of_dicts(
        self,
        json_input: Sequence[dict[str, Any]],
    ) -> Optional[Collection[str]]:
        """
        This method is required to implement clubbing.
        It tries to come up with column headers for your input
        """
        if not json_input:
            return ()

        column_headers = json_input[0].keys()
        for entry in json_input:
            if len(entry.keys()) != len(column_headers):
                return None
            if not all(header in entry for header in column_headers):
                return None
        return column_headers

    def convert_json_node(self, json_input: dict | list | str) -> str:
        """Dispatch JSON input according to the outermost type and process it
        to generate the super awesome HTML format.
        """
        match json_input:
            case str():
                if self.escape:
                    return html_escape(json_input)
                else:
                    return json_input
            case dict():
                return self.convert_object(json_input)
            case list() | tuple():
                return self.convert_list(json_input)
        return str(json_input)

    def convert_list(self, list_input: Sequence) -> str:
        """Iterate over the JSON list and process it
        to generate either an HTML table or a HTML list, depending on what's inside.
        If suppose some key has array of objects and all the keys are same,
        instead of creating a new row for each such entry,
        club such values, thus it makes more sense and more readable table.

        @example:
            jsonObject = {
                "sampleData": [
                    {"a":1, "b":2, "c":3},
                    {"a":5, "b":6, "c":7}
                ]
            }
            OUTPUT:
            _____________________________
            |               |   |   |   |
            |               | a | c | b |
            |   sampleData  |---|---|---|
            |               | 1 | 3 | 2 |
            |               | 5 | 7 | 6 |
            -----------------------------

        @contributed by: @muellermichel
        """
        if not list_input:
            return ""
        converted_output = ""
        column_headers = None
        if self.clubbing:
            column_headers = self.column_headers_from_list_of_dicts(list_input)
        if column_headers is not None:
            converted_output += self.table_init_markup
            converted_output += "<thead>"
            converted_output += "<tr><th>" + "</th><th>".join(column_headers) + "</th></tr>"
            converted_output += "</thead>"
            converted_output += "<tbody>"
            for list_entry in list_input:
                converted_output += "<tr><td>"
                converted_output += "</td><td>".join(
                    self.convert_json_node(list_entry[column_header]) for column_header in column_headers
                )
                converted_output += "</td></tr>"
            converted_output += "</tbody>"
            converted_output += "</table>"
            return converted_output

        # so you don't want or need clubbing eh? This makes @muellermichel very sad... ;(
        # alright, let's fall back to a basic list here...
        converted_output = "<ul><li>"
        converted_output += "</li><li>".join([self.convert_json_node(child) for child in list_input])
        converted_output += "</li></ul>"
        return converted_output

    def convert_object(self, json_input: dict) -> str:
        """
        Iterate over the JSON object and process it
        to generate the super awesome HTML Table format
        """
        if not json_input:
            return ""  # avoid empty tables
        converted_output = self.table_init_markup + "<tr>"
        converted_output += "</tr><tr>".join(
            [
                "<th>%s</th><td>%s</td>" % (self.convert_json_node(k), self.convert_json_node(v))
                for k, v in json_input.items()
            ]
        )
        converted_output += "</tr></table>"
        return converted_output


def json2html(
    json_input: dict | list | str,
    *,
    table_attributes: str = 'border="1"',
    clubbing: bool = True,
    escape: bool = True,
) -> str:
    """Convert JSON dict to HTML Table format"""
    convert = Json2Html(table_attributes, clubbing, escape)
    return convert.convert_json_node(json_input)
