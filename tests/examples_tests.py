#!/usr/bin/env python3
# JUBE Benchmarking Environment
# Copyright (C) 2008-2022
# Forschungszentrum Juelich GmbH, Juelich Supercomputing Centre
# http://www.fz-juelich.de/jsc/jube
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""Test the examples"""

from __future__ import (print_function,
                        unicode_literals,
                        division)

import sys
import filecmp
import re
import glob
import unittest
import os
import shutil
import jube2.main

EXAMPLES_PREFIX = os.path.join(os.path.dirname(__file__), "../examples")


class TestExamples(unittest.TestCase):

    """Class for testing the included examples"""

    def test_examples(self):
        """Main function"""
        examples_tasks = []
        for i in [".xml", ".yaml"]:
            examples_tasks.append(ExampleChecker(
                "do_log", "do_log"+i))
            examples_tasks.append(ExampleChecker(
                "environment", "environment"+i))
            examples_tasks.append(ExampleChecker(
                "result_creation", "result_creation"+i))
            examples_tasks.append(ExampleChecker(
                "files_and_sub", "files_and_sub"+i))
            examples_tasks.append(ExampleChecker(
                "dependencies", "dependencies"+i))
            examples_tasks.append(ExampleChecker("tagging", "tagging"+i))
            examples_tasks.append(ExampleChecker(
                "parameterspace", "parameterspace"+i))
            examples_tasks.append(ExampleChecker(
                "parameter_dependencies", "parameter_dependencies"+i))
            examples_tasks.append(ExampleChecker(
                "scripting_parameter", "scripting_parameter"+i))
            examples_tasks.append(ExampleChecker(
                "scripting_pattern", "scripting_pattern"+i))
            examples_tasks.append(ExampleChecker("statistic", "statistic"+i))
            examples_tasks.append(ExampleChecker("include", "main"+i))
            examples_tasks.append(ExampleChecker("shared", "shared"+i))
            examples_tasks.append(ExampleChecker(
                "hello_world", "hello_world"+i))
            examples_tasks.append(ExampleChecker("iterations", "iterations"+i))
            examples_tasks.append(ExampleChecker("cycle", "cycle"+i))
            examples_tasks.append(ExampleChecker(
                "parameter_update", "parameter_update"+i))
            examples_tasks.append(ExampleChecker(
                "result_database", "result_database"+i))
            examples_tasks.append(ExampleChecker(
                "duplicate", "duplicate"+i, suffix="--tag few many"))

        for checker in examples_tasks:
            self.assertTrue(checker.run())


class ExampleChecker(object):

    """Class for checking examples"""

    def __init__(self, bench_path, xml_file, bench_run_path=None,
                 check_function=True, debug=False, suffix=""):
        """Init instance.

        The check_function should return a bool value to indicate the
        success of failure of the test.

        """
        self._bench_name = bench_path
        self._xml_file = os.path.join(EXAMPLES_PREFIX, bench_path, xml_file)

        self._bench_run_path = bench_run_path or os.path.join(
            EXAMPLES_PREFIX, bench_path, "bench_run")

        self._check_function = check_function
        self._debug = debug
        self._suffix = suffix

    def run(self):
        """Run example"""
        success = True
        debug = "--debug" if self._debug else ""
        jube2.main.main(
            "{0} run -e {1} -r {2}".format(debug, self._xml_file, self._suffix).split())

        if self._check_function:
            success = self._check()

        shutil.rmtree(os.path.join(EXAMPLES_PREFIX,
                      os.path.join(self._bench_name, "bench_run")))
        if self._bench_name == 'result_database':
            os.remove('result_database.dat')

        return success

    # compare the output line-wise with check file
    def _check(self):
        success = True
        if not self._debug:
            latest_file = max(glob.glob(os.path.join(os.path.join(EXAMPLES_PREFIX, os.path.join(
                self._bench_name, "bench_run")), '*/')), key=os.path.getmtime)

            # delete temporary files, if they are existing
            if os.path.exists(os.path.join(EXAMPLES_PREFIX, os.path.join(self._bench_name, "bench_run"), latest_file, "run.log.tmp")):
                os.remove(os.path.join(EXAMPLES_PREFIX, os.path.join(self._bench_name, "bench_run"), latest_file, "run.log.tmp"))
            if os.path.exists(os.path.join(os.path.dirname(__file__),"examples_output", self._bench_name, "run.log.tmp")):
                os.remove(os.path.join(os.path.dirname(__file__),"examples_output", self._bench_name, "run.log.tmp"))

            # preprocess test and check file to care for line breaks within tables
            ausgabe = open(os.path.join(EXAMPLES_PREFIX, os.path.join(
                self._bench_name, "bench_run"), latest_file, "run.log.tmp"), 'w')
            check = open(os.path.join(os.path.dirname(__file__),
                         "examples_output", self._bench_name, "run.log.tmp"), 'w')
            ausgabeOriginal = open(os.path.join(EXAMPLES_PREFIX, os.path.join(
                self._bench_name, "bench_run"), latest_file, "run.log"), 'r')
            checkOriginal = open(os.path.join(os.path.dirname(__file__),
                         "examples_output", self._bench_name, "run.log"), 'r')

            # leave out all jube printed tables rows, which have an emptry columns entry and therefore, are part of a line break
            for fileHandle in [[ausgabeOriginal,ausgabe],[checkOriginal,check]]:
                for line in fileHandle[0]:
                    if re.match('^(?:.+?:){4}(?:\s){10}(.*)(?:.*?\||\+)(.*)', line) and re.match('^.*\|\s*\|.*$', line):
                        pass
                    else:
                        fileHandle[1].write(line)
                
            # jump to start of the temporary output files
            ausgabe.close()
            check.close()
            ausgabe = open(os.path.join(EXAMPLES_PREFIX, os.path.join(
                self._bench_name, "bench_run"), latest_file, "run.log.tmp"), 'r')
            check = open(os.path.join(os.path.dirname(__file__),
                         "examples_output", self._bench_name, "run.log.tmp"), 'r')
            ausgabeOriginal.close()
            checkOriginal.close() 

            success = ExampleChecker._tabfinder(ausgabe, check) 
            for l1, l2 in zip(ausgabe, check):
                if not re.match('^(?:.+?:){4}(?:\s){10}(.*)(?:.*?\||\+)(.*)', l1) and "id" not in l1 and "dir" not in l1 and "handle" not in l1 and "copy" not in l1:
                    ausgabeMatcher = re.match(
                        '^(?:.+?:){4}(.*?)(?:stdout.*?)?(?:stderr.*?)?$', l1)
                    checkMatcher = re.match(
                        '^(?:.+?:){4}(.*?)(?:stdout.*?)?(?:stderr.*?)?$', l2)
                    if ausgabeMatcher.group(1) != checkMatcher.group(1):
                        check.close()
                        ausgabe.close()
                        # delete temporary files, if they are existing
                        if os.path.exists(os.path.join(EXAMPLES_PREFIX, os.path.join(self._bench_name, "bench_run"), latest_file, "run.log.tmp")):
                            os.remove(os.path.join(EXAMPLES_PREFIX, os.path.join(self._bench_name, "bench_run"), latest_file, "run.log.tmp"))
                        if os.path.exists(os.path.join(os.path.dirname(__file__),"examples_output", self._bench_name, "run.log.tmp")):
                            os.remove(os.path.join(os.path.dirname(__file__),"examples_output", self._bench_name, "run.log.tmp"))
                        return False
            check.close()
            ausgabe.close()

            # delete temporary files, if they are existing
            if os.path.exists(os.path.join(EXAMPLES_PREFIX, os.path.join(self._bench_name, "bench_run"), latest_file, "run.log.tmp")):
                os.remove(os.path.join(EXAMPLES_PREFIX, os.path.join(self._bench_name, "bench_run"), latest_file, "run.log.tmp"))
            if os.path.exists(os.path.join(os.path.dirname(__file__),"examples_output", self._bench_name, "run.log.tmp")):
                os.remove(os.path.join(os.path.dirname(__file__),"examples_output", self._bench_name, "run.log.tmp"))

        return success

    # extract and compare tables
    @staticmethod
    def _tabfinder(file1, file2):
        success = False
        ignore = ["_home", "_id", "_padid", "_rundir",
                  "_start", "_abspath", "_relpath"]
        vergleichbar = True
        ausgabe = ""
        ausgabeDic = {}
        check = ""
        checkDic = {}

        for l1, l2 in zip(file1, file2):
            if re.match('^(?:.+?:){4}(?:\s){10}(.*)(?:.*?\||\+)(.*)', l1):
                ausgabe += l1
            if re.match('^(?:.+?:){4}(?:\s){10}(.*)(?:.*?\||\+)(.*)', l2):
                check += l2

        for l1, l2 in zip(ausgabe.split("\n"), check.split("\n")):
            ausgabeTab = re.match(
                '^(?:.+?:){4}(?:\s){10}(.*)(?:.*?\||\+)(.*)', l1)
            checkTab = re.match(
                '^(?:.+?:){4}(?:\s){10}(.*)(?:.*?\||\+)(.*)', l2)
            if ausgabeTab:
                ausgabeDic[ausgabeTab.group(1).replace(
                    " ", "")] = ausgabeTab.group(2).replace(" ", "")
            if checkTab:
                checkDic[checkTab.group(1).replace(
                    " ", "")] = checkTab.group(2).replace(" ", "")
                
        for key in ausgabeDic:
            for elem in ignore:
                if elem in key:
                    vergleichbar = False
            if vergleichbar:
                if key in checkDic:
                    if ausgabeDic[key] == checkDic[key]:
                        success = True
                if success == False:
                    file1.seek(0)
                    file2.seek(0)

                    return False
 
        # remove to beginning of the files
        file1.seek(0)
        file2.seek(0)
        return success


if __name__ == "__main__":
    unittest.main()
