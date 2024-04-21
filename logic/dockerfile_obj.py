from __future__ import annotations

import logging
import os
import sys
from datetime import datetime
from typing import List, Dict
import json
import dockerfile as dockerfile_parser
import subprocess
from collections import defaultdict
from pykson import Pykson
from logic.smell import Smell
import ntpath


class InvalidDockerfileError(Exception):
    """Raised when the selected file is not a Dockerfile"""
    pass


class Dockerfile:
    def __init__(self, filepath: str, last_edit: datetime):
        self._filepath = filepath
        self._filename = self.__get_filename(filepath)
        self._last_edit = last_edit
        self._lines = self.__get_lines(filepath)
        self._parsed_lines = self.__get_parsed_lines(filepath)
        self._lines_changed = False
        self._smells_dict = self.__check_smells(filepath)

    @property
    def lines(self) -> List[str]:
        return self._lines

    @property
    def parsed_lines(self) -> Dict:
        return self._parsed_lines

    @property
    def lines_changed(self) -> bool:
        return self._lines_changed

    @lines_changed.setter
    def lines_changed(self, changed) -> None:
        self._lines_changed = changed

    @property
    def filepath(self) -> str:
        return self._filepath

    @property
    def last_edit(self) -> datetime:
        return self._last_edit

    @property
    def smells_dict(self) -> dict:
        return self._smells_dict

    def update_smells_dict(self, ignore: List = None) -> None:
        """
        Update the smells dictionary.
        Call it when the lines number of the Dockerfile change.
        """
        filepath = self.__produce_temp_dockerfile()
        # refresh parsed lines
        self._parsed_lines = self.__get_parsed_lines(filepath)
        self._smells_dict = self.__check_smells(filepath, ignore)
        os.remove(filepath)
        self._lines_changed = True

    def __produce_temp_dockerfile(self) -> str:
        filepath = sys.path[0] + f'/temp/{self._filename}'
        with open(filepath, 'w') as file:
            for line in self._lines:
                file.write(line)
        return filepath

    def __get_filename(self, filepath: str) -> str:
        head, tail = ntpath.split(filepath)
        return tail or ntpath.basename(head)

    def __get_lines(self, filepath: str) -> List[str]:
        with open(filepath, encoding="utf8") as f:
            return f.readlines()

    def __get_parsed_lines(self, filepath: str) -> Dict[str, dockerfile_parser.Command]:
        parsed_dict = dict()
        try:
            for cmd in dockerfile_parser.parse_file(filepath):
                parsed_dict[cmd.start_line] = cmd
            return parsed_dict
        except dockerfile_parser.GoParseError as res:
            raise InvalidDockerfileError(res)
        except dockerfile_parser.GoIOError as res:
            raise InvalidDockerfileError(res)

    def __check_smells(self, filepath: str, ignore: List = None) -> Dict:
        # Retrieve hadolint result
        output = subprocess.run(['hadolint', '-f', 'json', filepath], stdout=subprocess.PIPE)
        result = output.stdout.decode('utf-8')

        result_json = json.loads(result)

        # Set default value as an empty list
        smells_dict = defaultdict(list)

        # Put smells in a dictionary like line_position => [smells]
        for smell_json in result_json:
            if smell_json['code'] in ['DL1000', 'DL3061']:
                raise InvalidDockerfileError(result)

            if ignore and smell_json['code'] in ignore:
                #logging.info("Skipping", smell_json['code'])
                continue

            smell = Pykson().from_json(smell_json, Smell, accept_unknown=True)
            smells_dict[smell.line].append(smell)

        return smells_dict
