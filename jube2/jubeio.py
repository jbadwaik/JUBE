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
"""Basic I/O module"""

from __future__ import (print_function,
                        unicode_literals,
                        division)

import xml.etree.ElementTree as ET
import os
from jube2.util.util import Queue
import jube2.benchmark
import jube2.substitute
import jube2.parameter
import jube2.fileset
import jube2.pattern
import jube2.workpackage
import jube2.analyser
import jube2.step
import jube2.util.util
import jube2.util.output
import jube2.conf
import jube2.result_types.syslog
import jube2.result_types.table
import jube2.result_types.database
import jube2.util.yaml_converter
import sys
import re
import copy
import hashlib
import jube2.log
from distutils.version import StrictVersion

LOGGER = jube2.log.get_logger(__name__)


class Parser(object):

    """JUBE XML input file parser"""

    def __init__(self, filename, tags=None, include_path=None, force=False,
                 strict=False):
        self._filename = filename
        if include_path is None:
            include_path = list()
        self._include_path = include_path
        if tags is None:
            tags = set()
        self._tags = tags
        self._force = force
        self._strict = strict
        self._file_handle = None

    def __del__(self):
        if self._file_handle is not None:
            self._file_handle.close()

    @property
    def file_path_ref(self):
        """Return file path given by config file"""
        file_path_ref = os.path.dirname(self._filename)
        if len(file_path_ref) > 0:
            return file_path_ref
        else:
            return "."

    def benchmarks_from_xml(self):
        """Return a dict of benchmarks

        Here parametersets are global and accessible to all benchmarks defined
        in the corresponding XML file.
        """
        benchmarks = dict()
        LOGGER.debug("Parsing {0}".format(self._filename))

        if not os.path.isfile(self._filename):
            raise IOError("Benchmark configuration file not found: \"{0}\""
                          .format(self._filename))

        tree = self._tree_from_file(self._filename)

        # Check compatible terminal encoding: In some cases, the terminal env.
        # only allow ascii based encoding, print and filesystem operation will
        # be broken if there is a special char inside the input file.
        # In such cases the encode will stop, using an UnicodeEncodeError
        try:
            xml = jube2.util.output.element_tree_tostring(tree.getroot(),
                                                          encoding="UTF-8")
            xml.encode(sys.getfilesystemencoding())
        except UnicodeEncodeError as uee:
            raise ValueError("Your terminal only allows '{0}' encoding. {1}"
                             .format(sys.getfilesystemencoding(), str(uee)))

        # Check input file version
        version = tree.getroot().get("version")
        if (version is not None) and (not self._force):
            version = version.strip()
            if StrictVersion(version) > StrictVersion(jube2.conf.JUBE_VERSION):
                if self._strict:
                    error_str = ("Benchmark file \"{0}\" was created using " +
                                 "a newer version of JUBE ({1}).\nCurrent " +
                                 "JUBE version ({2}) might not be compatible" +
                                 ". Due to strict mode, further execution " +
                                 "was stopped.").format(
                                     self._filename, version,
                                     jube2.conf.JUBE_VERSION)
                    raise ValueError(error_str)
                else:
                    info_str = ("Benchmark file \"{0}\" was created using a " +
                                "newer version of JUBE ({1}).\nCurrent JUBE " +
                                "version ({2}) might not be compatible." +
                                "\nContinue? (y/n):").format(
                                    self._filename, version,
                                    jube2.conf.JUBE_VERSION)
                    try:
                        inp = raw_input(info_str)
                    except NameError:
                        inp = input(info_str)
                    if not inp.startswith("y"):
                        return None, list(), list()

        valid_tags = ["selection", "include-path", "parameterset", "benchmark",
                      "substituteset", "fileset", "include", "patternset"]

        # Save init include path (from command line)
        init_include_path = list(self._include_path)

        # Preprocess xml-tree, this must be done multiple times because of
        # recursive include structures
        changed = True
        counter = 0
        while changed and counter < jube2.conf.PREPROCESS_MAX_ITERATION:
            # Reset variables
            only_bench = set()
            not_bench = set()
            local_tree = copy.deepcopy(tree)
            self._include_path = list(init_include_path)
            counter += 1
            LOGGER.debug("  --> Preprocess run {0} <--".format(counter))

            LOGGER.debug("  Remove invalid tags")
            LOGGER.debug("    Available tags: {0}"
                         .format(jube2.conf.DEFAULT_SEPARATOR.join(
                             self._tags)))
            Parser._remove_invalid_tags(local_tree.getroot(), self._tags)

            # Read selection area
            for selection_tree in local_tree.findall("selection"):
                new_only_bench, new_not_bench, new_tags = \
                    Parser._extract_selection(selection_tree)
                self._tags.update(new_tags)
                only_bench.update(new_only_bench)
                not_bench.update(new_not_bench)

            LOGGER.debug("  Remove invalid tags")
            LOGGER.debug("    Available tags: {0}"
                         .format(jube2.conf.DEFAULT_SEPARATOR.join(
                             self._tags)))
            # Reset tree, because selection might add additional tags
            local_tree = copy.deepcopy(tree)
            Parser._remove_invalid_tags(local_tree.getroot(), self._tags)

            # Read include-path
            for include_path_tree in local_tree.findall("include-path"):
                self._extract_include_path(include_path_tree)

            # Add env var based include path
            self._include_path += Parser._read_envvar_include_path()

            # Add local dir to include path
            self._include_path += [self.file_path_ref]

            # Preprocess xml-tree
            LOGGER.debug("  Preprocess xml tree")
            for path in self._include_path:
                LOGGER.debug("    path: {0}".format(path))

            changed = self._preprocessor(tree.getroot())
            if changed:
                LOGGER.debug("  New tags might be included, start " +
                             "additional include-preprocess run.")
            else:
                LOGGER.debug("  No preprocessing changes were detected, stop" +
                             " additional include-preprocess runs.")

        # Rerun removing invalid tags
        LOGGER.debug("  Remove invalid tags")
        LOGGER.debug("    Available tags: {0}"
                     .format(jube2.conf.DEFAULT_SEPARATOR.join(self._tags)))
        Parser._remove_invalid_tags(tree.getroot(), self._tags)

        # Check tags
        for element in tree.getroot():
            Parser._check_tag(element, valid_tags)

        # Check for remaing <include> tags
        node = jube2.util.util.get_tree_element(tree.getroot(),
                                                tag_path="include")
        if node is not None:
            raise ValueError(("Remaining include element found, which " +
                              "was not replaced (e.g. due to a missing " +
                              "include-path):\n" +
                              "<include from=\"{0}\" ... />")
                             .format(node.attrib["from"]))

        LOGGER.debug("  Preprocess done")

        # Read all global parametersets
        global_parametersets = self._extract_parametersets(tree)
        # Read all global substitutesets
        global_substitutesets = self._extract_substitutesets(tree)
        # Read all global filesets
        global_filesets = self._extract_filesets(tree)
        # Read all global patternsets
        global_patternsets = self._extract_patternsets(tree)

        # At this stage we iterate over benchmarks
        benchmark_list = tree.findall("benchmark")
        for benchmark_tree in benchmark_list:
            self._benchmark_preprocessor(benchmark_tree)
            benchmark = self._create_benchmark(benchmark_tree,
                                               global_parametersets,
                                               global_substitutesets,
                                               global_filesets,
                                               global_patternsets)
            benchmarks[benchmark.name] = benchmark
        return benchmarks, list(only_bench), list(not_bench)

    @staticmethod
    def _convert_old_tag_format(input_string):
        """Converts the old ,-based tag format into the new tag format"""

        tags = set(map(lambda x: x.strip(), input_string.split(",")))
        not_tags = set([tag for tag in tags if tag[0] == "!"])
        tags = tags.difference(not_tags)

        output_string = "+".join(not_tags)
        if len(output_string) > 0 and len(tags) > 0:
            output_string += "+"
        if len(tags) > 0:
            output_string += "(" + "|".join(tags) + ")"
        return output_string

    @staticmethod
    def _check_valid_tags(element, tags):
        """Check if element contains only valid tags"""
        return jube2.util.util.valid_tags(element.get("tag"), tags)

    @staticmethod
    def _remove_invalid_tags(etree, tags):
        """Remove tags which contain an invalid tags-attribute"""
        children = list(etree)
        for child in children:
            if not Parser._check_valid_tags(child, tags):
                etree.remove(child)
                continue
            Parser._remove_invalid_tags(child, tags)

    def _preprocessor(self, etree):
        """Preprocess the xml-file by replacing include-tags"""
        children = list(etree)
        new_children = list()
        include_index = 0
        changed = False
        for child in children:
            # Replace include tags
            if ((child.tag == "include") and
                    Parser._check_valid_tags(child, self._tags)):
                filename = Parser._attribute_from_element(child, "from")
                path = child.get("path", ".")
                if path == "":
                    path = "."
                try:
                    file_path = self._find_include_file(filename)
                    include_tree = ET.parse(file_path)
                    # Find external nodes
                    includes = include_tree.findall(path)
                except ValueError:
                    includes = list()
                except ET.ParseError:
                    LOGGER.error("Error while parsing {0}:".format(file_path))
                    raise
                if len(includes) > 0:
                    # Remove include-node
                    etree.remove(child)
                    # Insert external nodes
                    for include in includes:
                        etree.insert(include_index, include)
                        include_index += 1
                        new_children.append(include)
                    include_index -= 1
                    changed = True
            else:
                new_children.append(child)
            include_index += 1
        for child in new_children:
            changed = self._preprocessor(child) or changed
        return changed

    def _benchmark_preprocessor(self, benchmark_etree):
        """Preprocess the xml-tree of given benchmark."""
        LOGGER.debug("  Preprocess benchmark xml tree")

        # Search for <use from=""></use> and load external set
        uses = jube2.util.util.get_tree_elements(benchmark_etree, "use")
        files = dict()
        for use in uses:
            from_str = use.get("from", "").strip()
            if (use.text is not None) and (use.text.strip() != "") and \
               (from_str != ""):
                hash_val = hashlib.md5(from_str.encode()).hexdigest()
                if hash_val not in files:
                    files[hash_val] = set()

                set_names = [element.strip() for element
                             in use.text.split(jube2.conf.DEFAULT_SEPARATOR)]

                for file_str in from_str.split(jube2.conf.DEFAULT_SEPARATOR):
                    parts = file_str.strip().split(":")
                    filename = parts[0].strip()
                    if filename == "":
                        filename = self._filename
                    alt_set_names = set([element.strip()
                                         for element in parts[1:]])
                    if len(alt_set_names) == 0:
                        alt_set_names = set(set_names)
                    for name in alt_set_names:
                        files[hash_val].add((filename, name))

                # Replace set-name with an internal one
                new_use_str = ""
                for name in set_names:
                    if len(new_use_str) > 0:
                        new_use_str += jube2.conf.DEFAULT_SEPARATOR
                    new_use_str += "jube_{0}_{1}".format(hash_val, name)
                use.text = new_use_str

        # Create new xml elements
        for fileid in files:
            for filename, name in files[fileid]:
                set_type = self._find_set_type(filename, name)
                set_etree = ET.SubElement(benchmark_etree, set_type)
                set_etree.attrib["name"] = "jube_{0}_{1}".format(fileid, name)
                set_etree.attrib["init_with"] = "{0}:{1}".format(
                    filename, name)
                LOGGER.debug("    Created new <{0}>: jube_{1}_{2}".format(
                    set_type, fileid, name))

    def _find_include_file(self, filename):
        """Search for filename in include-pathes and return resulting path"""
        for path in self._include_path:
            file_path = os.path.join(path, filename)
            if os.path.exists(file_path):
                break
        else:
            raise ValueError(("\"{0}\" not found in possible " +
                              "include pathes").format(filename))
        return file_path

    def _find_set_type(self, filename, name):
        """Search for the set-type inside given file"""
        LOGGER.debug(
            "    Searching for type of \"{0}\" in {1}".format(name, filename))
        file_path = self._find_include_file(filename)
        etree = self._tree_from_file(file_path).getroot()
        Parser._remove_invalid_tags(etree, self._tags)
        found_set = jube2.util.util.get_tree_elements(
            etree, attribute_dict={"name": name})

        found_set = [set_etree for set_etree in found_set
                     if set_etree.tag in ("parameterset", "substituteset",
                                          "fileset", "patternset")]

        if len(found_set) > 1:
            raise ValueError(("name=\"{0}\" can be found multiple times " +
                              "inside \"{1}\"").format(name, file_path))
        elif len(found_set) == 0:
            raise ValueError(("name=\"{0}\" not found inside " +
                              "\"{1}\"").format(name, file_path))
        else:
            return found_set[0].tag

    def benchmark_info_from_xml(self):
        """Return name, comment and available tags of first benchmark
        found in file"""
        tree = ET.parse(self._filename).getroot()
        tags = set()
        for tag_etree in jube2.util.util.get_tree_elements(tree,
                                                           "selection/tag"):
            if tag_etree.text is not None:
                tags.update(set([tag.strip() for tag in
                                 tag_etree.text.split(
                                     jube2.conf.DEFAULT_SEPARATOR)]))
        benchmark_etree = jube2.util.util.get_tree_element(tree, "benchmark")
        if benchmark_etree is None:
            raise ValueError("benchmark-tag not found in \"{0}\"".format(
                self._filename))
        name = Parser._attribute_from_element(benchmark_etree,
                                              "name").strip()
        comment_element = benchmark_etree.find("comment")
        if comment_element is not None:
            comment = comment_element.text
            if comment is None:
                comment = ""
        else:
            comment = ""
        comment = re.sub(r"\s+", " ", comment).strip()
        return name, comment, tags

    def analyse_result_from_xml(self):
        """Read existing analyse out of xml-file"""
        LOGGER.debug("Parsing {0}".format(self._filename))
        try:
            tree = ET.parse(self._filename).getroot()
        except ET.ParseError as pe:
            LOGGER.error(
                "Parsing error while reading existing analysis: " +
                "{0}".format(pe))
            return None
        analyse_result = dict()
        analyser = jube2.util.util.get_tree_elements(tree, "analyzer")
        analyser += jube2.util.util.get_tree_elements(tree, "analyser")
        for analyser_etree in analyser:
            analyser_name = Parser._attribute_from_element(
                analyser_etree, "name")
            analyse_result[analyser_name] = dict()
            for step_etree in analyser_etree:
                Parser._check_tag(step_etree, ["step"])
                step_name = Parser._attribute_from_element(
                    step_etree, "name")
                analyse_result[analyser_name][step_name] = dict()
                for workpackage_etree in step_etree:
                    Parser._check_tag(workpackage_etree, ["workpackage"])
                    wp_id = int(Parser._attribute_from_element(
                        workpackage_etree, "id"))
                    analyse_result[analyser_name][step_name][wp_id] = dict()
                    for pattern_etree in workpackage_etree:
                        Parser._check_tag(pattern_etree, ["pattern"])
                        pattern_name = \
                            Parser._attribute_from_element(
                                pattern_etree, "name")
                        pattern_type = \
                            Parser._attribute_from_element(
                                pattern_etree, "type")
                        value = pattern_etree.text
                        if value is not None:
                            value = value.strip()
                        else:
                            value = ""
                        value = jube2.util.util.convert_type(pattern_type,
                                                             value)
                        analyse_result[analyser_name][step_name][
                            wp_id][pattern_name] = value
        return analyse_result

    def workpackages_from_xml(self, benchmark):
        """Read existing workpackage data out of a xml-file"""
        workpackages = dict()
        # tmp: Dict workpackage_id => workpackage
        tmp = dict()
        # parents_tmp: Dict workpackage_id => list of parent_workpackage_ids
        parents_tmp = dict()
        iteration_siblings_tmp = dict()
        work_list = Queue()
        LOGGER.debug("Parsing {0}".format(self._filename))
        if not os.path.isfile(self._filename):
            raise IOError("Workpackage configuration file not found: \"{0}\""
                          .format(self._filename))
        tree = ET.parse(self._filename)
        max_id = -1
        for element in tree.getroot():
            Parser._check_tag(element, ["workpackage"])
            # Read XML-data
            (workpackage_id, step_name, parameterset, parents,
             iteration_siblings, iteration, cycle, set_env, unset_env) = \
                Parser._extract_workpackage_data(element)
            # Search for step
            step = benchmark.steps[step_name]
            parameter_names = [parameter.name for parameter in parameterset]
            tmp[workpackage_id] = \
                jube2.workpackage.Workpackage(benchmark, step, parameter_names,
                                              parameterset, workpackage_id,
                                              iteration, cycle)
            max_id = max(max_id, workpackage_id)
            parents_tmp[workpackage_id] = parents
            iteration_siblings_tmp[workpackage_id] = iteration_siblings
            tmp[workpackage_id].env.update(set_env)
            for env_name in unset_env:
                if env_name in tmp[workpackage_id].env:
                    del tmp[workpackage_id].env[env_name]
            if len(parents) == 0:
                work_list.put(tmp[workpackage_id])

        # Set workpackage counter to current id number
        jube2.workpackage.Workpackage.id_counter = max_id + 1

        # Rebuild graph structure
        for workpackage_id in parents_tmp:
            for parent_id in parents_tmp[workpackage_id]:
                tmp[workpackage_id].add_parent(tmp[parent_id])
                tmp[parent_id].add_children(tmp[workpackage_id])

        # Rebuild sibling structure
        for workpackage_id in iteration_siblings_tmp:
            for sibling_id in iteration_siblings_tmp[workpackage_id]:
                tmp[workpackage_id].iteration_siblings.add(tmp[sibling_id])

        # Rebuild history
        done_list = list()
        while not work_list.empty():
            workpackage = work_list.get_nowait()
            history = jube2.parameter.Parameterset()
            if workpackage.id in parents_tmp:
                for parent_id in parents_tmp[workpackage.id]:
                    history.add_parameterset(tmp[parent_id].parameterset)
            done_list.append(workpackage)
            for child in workpackage.children:
                all_done = True
                for parent in child.parents:
                    all_done = all_done and (parent in done_list)
                if all_done and (child not in done_list):
                    work_list.put(child)
            history.add_parameterset(workpackage.parameterset)
            workpackage.parameterset.add_parameterset(history)

        # Add JUBE parameter
        for workpackage in tmp.values():
            # JUBE benchmark parameter
            workpackage.parameterset.add_parameterset(
                benchmark.get_jube_parameterset())
            # JUBE step parameter
            workpackage.parameterset.add_parameterset(
                workpackage.step.get_jube_parameterset())
            # JUBE workpackage parameter
            workpackage.parameterset.add_parameterset(
                workpackage.get_jube_parameterset())
            # Enable work_dir caching
            workpackage.allow_workpackage_dir_caching()
            jube_parameter = workpackage.parameterset.get_updatable_parameter(
                jube2.parameter.JUBE_MODE)
            jube_parameter.parameter_substitution(
                additional_parametersets=[workpackage.parameterset],
                final_sub=True)
            workpackage.parameterset.update_parameterset(jube_parameter)

        # Store workpackage data
        work_stat = jube2.util.util.WorkStat()
        for step_name in benchmark.steps:
            workpackages[step_name] = list()
        # First put started wps inside the queue
        for mode in ("only_started", "all"):
            for workpackage in tmp.values():
                if len(workpackage.parents) == 0:
                    if (mode == "only_started" and workpackage.started) or \
                       (mode == "all" and (not workpackage.queued)):
                        workpackage.queued = True
                        work_stat.put(workpackage)
                if mode == "all":
                    workpackages[workpackage.step.name].append(workpackage)

        return workpackages, work_stat

    @staticmethod
    def _extract_workpackage_data(workpackage_etree):
        """Extract workpackage information from etree

        Return workpackage id, name of step, local parameterset and list of
        parent ids
        """
        valid_tags = ["step", "parameterset", "parents", "iteration_siblings",
                      "environment"]
        for element in workpackage_etree:
            Parser._check_tag(element, valid_tags)
        workpackage_id = int(Parser._attribute_from_element(
            workpackage_etree, "id"))
        step_etree = workpackage_etree.find("step")
        iteration = int(step_etree.get("iteration", "0").strip())
        cycle = int(step_etree.get("cycle", "0").strip())
        step_name = step_etree.text.strip()
        parameterset_etree = workpackage_etree.find("parameterset")
        if parameterset_etree is not None:
            parameters = Parser._extract_parameters(parameterset_etree)
        else:
            parameters = list()
        parameterset = jube2.parameter.Parameterset()
        for parameter in parameters:
            parameterset.add_parameter(parameter)
        parents_etree = workpackage_etree.find("parents")
        if parents_etree is not None:
            parents = [int(parent) for parent in
                       parents_etree.text.split(",")]
        else:
            parents = list()
        siblings_etree = workpackage_etree.find("iteration_siblings")
        if siblings_etree is not None:
            iteration_siblings = set([int(sibling) for sibling in
                                      siblings_etree.text.split(",")])
        else:
            iteration_siblings = set([workpackage_id])
        environment_etree = workpackage_etree.find("environment")
        set_env = dict()
        unset_env = list()
        if environment_etree is not None:
            for env_etree in environment_etree:
                env_name = Parser._attribute_from_element(env_etree,
                                                          "name")
                if env_etree.tag == "env":
                    if env_etree.text is not None:
                        set_env[env_name] = env_etree.text.strip()
                        # string repr must be evaluated
                        if (set_env[env_name][0] == "'") or \
                            ((set_env[env_name][0] == "u") and
                             (set_env[env_name][1] == "'")) and \
                           (set_env[env_name][-1] == "'"):
                            set_env[env_name] = eval(set_env[env_name])
                elif env_etree.tag == "nonenv":
                    unset_env.append(env_name)
        return (workpackage_id, step_name, parameterset, parents,
                iteration_siblings, iteration, cycle, set_env, unset_env)

    @staticmethod
    def _extract_selection(selection_etree):
        """Extract selction information from etree

        Return names of benchmarks and tags (set([only,...]),set([not,...]),
        set([tag, ...]))
        """
        LOGGER.debug("  Parsing <selection>")
        valid_tags = ["only", "not", "tag"]
        only_bench = list()
        not_bench = list()
        tags = set()
        for element in selection_etree:
            Parser._check_tag(element, valid_tags)
            separator = jube2.conf.DEFAULT_SEPARATOR
            if element.text is not None:
                if element.tag == "only":
                    only_bench += element.text.split(separator)
                elif element.tag == "not":
                    not_bench += element.text.split(separator)
                elif element.tag == "tag":
                    tags.update(set([tag.strip() for tag in
                                     element.text.split(separator)]))
        only_bench = set([bench.strip() for bench in only_bench])
        not_bench = set([bench.strip() for bench in not_bench])
        return only_bench, not_bench, tags

    def _extract_include_path(self, include_path_etree):
        """Extract include-path pathes from etree"""
        LOGGER.debug("  Parsing <include-path>")
        valid_tags = ["path"]
        pathes = []
        if len(include_path_etree.text.strip()) > 0:
            pathes.append(include_path_etree.text.strip())
        for element in include_path_etree:
            Parser._check_tag(element, valid_tags)
            path = element.text
            if path is None:
                raise ValueError("Empty \"<path>\" found")
            path = path.strip()
            if len(path) == 0:
                raise ValueError("Empty \"<path>\" found")
            pathes.append(path)
        for path in pathes:
            path = os.path.expandvars(os.path.expanduser(path))
            path = os.path.join(self.file_path_ref, path)
            self._include_path += [path]
            LOGGER.debug("    New path: {0}".format(path))

    @staticmethod
    def _read_envvar_include_path():
        """Add environment var include-path"""
        LOGGER.debug("  Read $JUBE_INCLUDE_PATH")
        if "JUBE_INCLUDE_PATH" in os.environ:
            return [include_path for include_path in
                    os.environ["JUBE_INCLUDE_PATH"].split(":")
                    if include_path != ""]
        else:
            return []

    def _create_benchmark(self, benchmark_etree, global_parametersets,
                          global_substitutesets, global_filesets,
                          global_patternsets):
        """Create benchmark from etree

        Return a benchmark
        """
        name = \
            Parser._attribute_from_element(benchmark_etree, "name").strip()

        valid_tags = ["parameterset", "substituteset", "fileset", "step",
                      "comment", "patternset", "analyzer", "analyser",
                      "result"]
        for element in benchmark_etree:
            Parser._check_tag(element, valid_tags)

        comment_element = benchmark_etree.find("comment")
        if comment_element is not None:
            comment = comment_element.text
            if comment is None:
                comment = ""
        else:
            comment = ""
        comment = re.sub(r"\s+", " ", comment).strip()
        outpath = Parser._attribute_from_element(benchmark_etree,
                                                 "outpath").strip()
        outpath = os.path.expandvars(os.path.expanduser(outpath))
        # Add position of user to outpath
        outpath = os.path.normpath(os.path.join(self.file_path_ref, outpath))
        file_path_ref = benchmark_etree.get("file_path_ref")

        # Combine global and local sets
        parametersets = \
            Parser._combine_global_and_local_sets(
                global_parametersets,
                self._extract_parametersets(benchmark_etree))

        substitutesets = \
            Parser._combine_global_and_local_sets(
                global_substitutesets,
                self._extract_substitutesets(benchmark_etree))

        filesets = \
            Parser._combine_global_and_local_sets(
                global_filesets, self._extract_filesets(benchmark_etree))

        patternsets = \
            Parser._combine_global_and_local_sets(
                global_patternsets, self._extract_patternsets(benchmark_etree))

        # dict of local steps
        steps = self._extract_steps(benchmark_etree)

        # dict of local analysers
        analyser = self._extract_analysers(benchmark_etree)

        # dict of local results
        results, results_order = self._extract_results(benchmark_etree)

        # File path reference for relative file location
        if file_path_ref is not None:
            file_path_ref = file_path_ref.strip()
            file_path_ref = \
                os.path.expandvars(os.path.expanduser(file_path_ref))
        else:
            file_path_ref = "."

        # Add position of user to file_path_ref
        file_path_ref = \
            os.path.normpath(os.path.join(self.file_path_ref, file_path_ref))

        benchmark = jube2.benchmark.Benchmark(name, outpath,
                                              parametersets, substitutesets,
                                              filesets, patternsets, steps,
                                              analyser, results, results_order,
                                              comment, self._tags,
                                              file_path_ref)

        return benchmark

    @staticmethod
    def _combine_global_and_local_sets(global_sets, local_sets):
        """Combine global and local sets """
        result_sets = dict(global_sets)
        if set(result_sets) & set(local_sets):
            raise ValueError("\"{0}\" not unique"
                             .format(",".join([name for name in
                                               (set(result_sets) &
                                                set(local_sets))])))
        result_sets.update(local_sets)
        return result_sets

    @staticmethod
    def _extract_steps(etree):
        """Extract all steps from benchmark

        Return a dict of steps, e.g. {"compile": Step(...), ...}
        """
        steps = dict()
        for element in etree.findall("step"):
            step = Parser._extract_step(element)
            if step.name in steps:
                raise ValueError("\"{0}\" not unique".format(step.name))
            steps[step.name] = step
        return steps

    @staticmethod
    def _extract_step(etree_step):
        """Extract a step from etree

        Return name, list of contents (dicts), depend (list of strings).
        """
        valid_tags = ["use", "do"]

        name = Parser._attribute_from_element(etree_step, "name").strip()
        LOGGER.debug("  Parsing <step name=\"{0}\">".format(name))
        tmp = etree_step.get("depend", "").strip()
        iterations = int(etree_step.get("iterations", "1").strip())
        alt_work_dir = etree_step.get("work_dir")
        if alt_work_dir is not None:
            alt_work_dir = alt_work_dir.strip()
        export = etree_step.get("export", "false").strip().lower() == "true"
        max_wps = etree_step.get("max_async", "0").strip()
        active = etree_step.get("active", "true").strip()
        suffix = etree_step.get("suffix", "").strip()
        cycles = int(etree_step.get("cycles", "1").strip())
        procs = int(etree_step.get("procs", "1").strip())
        do_log_file = etree_step.get("do_log_file", "None").strip()
        do_log_file = None if do_log_file == "None" else do_log_file
        do_log_file = None if do_log_file == "False" else do_log_file
        do_log_file = None if do_log_file == "false" else do_log_file
        do_log_file = jube2.conf.DO_LOG_FILENAME if do_log_file == "True" else do_log_file
        do_log_file = jube2.conf.DO_LOG_FILENAME if do_log_file == "true" else do_log_file
        shared_name = etree_step.get("shared")
        if shared_name is not None:
            shared_name = shared_name.strip()
            if shared_name == "":
                raise ValueError("Empty \"shared\" attribute in " +
                                 "<step> found.")
        depend = set(val.strip() for val in
                     tmp.split(jube2.conf.DEFAULT_SEPARATOR) if val.strip())

        step = jube2.step.Step(name, depend, iterations, alt_work_dir,
                               shared_name, export, max_wps, active, suffix,
                               cycles, procs, do_log_file)
        for element in etree_step:
            Parser._check_tag(element, valid_tags)
            if element.tag == "do":
                async_filename = element.get("done_file")
                if async_filename is not None:
                    async_filename = async_filename.strip()
                error_filename = element.get("error_file")
                if error_filename is not None:
                    error_filename = error_filename.strip()
                break_filename = element.get("break_file")
                if break_filename is not None:
                    break_filename = break_filename.strip()
                stdout_filename = element.get("stdout")
                if stdout_filename is not None:
                    stdout_filename = stdout_filename.strip()
                stderr_filename = element.get("stderr")
                if stderr_filename is not None:
                    stderr_filename = stderr_filename.strip()
                active = element.get("active", "true").strip()
                shared_str = element.get("shared", "false").strip()
                alt_work_dir = element.get("work_dir")
                if alt_work_dir is not None:
                    alt_work_dir = alt_work_dir.strip()
                if shared_str.lower() == "true":
                    if shared_name is None:
                        raise ValueError("<do shared=\"true\"> only allowed "
                                         "inside a <step> which has a shared "
                                         "region")
                    if procs != 1:
                        raise ValueError("<do shared=\"true\"> not allowed " +
                                         "inside a parallel <step>")
                    shared = True
                elif shared_str == "false":
                    shared = False
                else:
                    raise ValueError("shared=\"{0}\" not allowed. Must be " +
                                     "\"true\" or \"false\"".format(
                                         shared_str))
                cmd = element.text
                if cmd is None:
                    cmd = ""
                operation = jube2.step.Operation(cmd.strip(),
                                                 async_filename,
                                                 stdout_filename,
                                                 stderr_filename,
                                                 active,
                                                 shared,
                                                 alt_work_dir,
                                                 break_filename,
                                                 error_filename)
                step.add_operation(operation)
            elif element.tag == "use":
                step.add_uses(Parser._extract_use(element))
        return step

    @staticmethod
    def _extract_analysers(etree):
        """Extract all analyser from etree"""
        analysers = dict()
        analyser_tags = etree.findall("analyzer")
        analyser_tags += etree.findall("analyser")
        for element in analyser_tags:
            analyser = Parser._extract_analyser(element)
            if analyser.name in analysers:
                raise ValueError("\"{0}\" not unique".format(analyser.name))
            analysers[analyser.name] = analyser
        return analysers

    @staticmethod
    def _extract_analyser(etree_analyser):
        """Extract an analyser from etree"""
        valid_tags = ["use", "analyse"]
        name = Parser._attribute_from_element(etree_analyser,
                                              "name").strip()
        reduce_iteration = \
            etree_analyser.get("reduce", "true").strip().lower() == "true"
        analyser = jube2.analyser.Analyser(name, reduce_iteration)
        LOGGER.debug("  Parsing <analyser name=\"{0}\">".format(name))
        for element in etree_analyser:
            Parser._check_tag(element, valid_tags)
            if element.tag == "analyse":
                step_name = Parser._attribute_from_element(element,
                                                           "step").strip()
                # If there are no files, just add a dummy element to the list
                if len(element) == 0:
                    analyser.add_analyse(step_name, None)
                for file_etree in element:
                    if (file_etree.text is None) or \
                            (file_etree.text.strip() == ""):
                        raise ValueError("Empty <file> found")
                    else:
                        use_text = file_etree.get("use")
                        if use_text is not None:
                            use_names = \
                                [use_name.strip() for use_name in
                                 use_text.split(jube2.conf.DEFAULT_SEPARATOR)]
                        else:
                            use_names = list()
                        for filename in file_etree.text.split(
                                jube2.conf.DEFAULT_SEPARATOR):
                            file_obj = jube2.analyser.Analyser.AnalyseFile(
                                filename.strip())
                            file_obj.add_uses(use_names)
                            analyser.add_analyse(step_name, file_obj)
            elif element.tag == "use":
                analyser.add_uses(Parser._extract_use(element))
        return analyser

    @staticmethod
    def _extract_results(etree):
        """Extract all results from etree"""
        results = dict()
        results_order = list()
        valid_tags = ["use", "table", "syslog", "database"]
        for result_etree in etree.findall("result"):
            result_dir = result_etree.get("result_dir")
            if result_dir is not None:
                result_dir = \
                    os.path.expandvars(os.path.expanduser(result_dir.strip()))
            sub_results = dict()
            uses = list()
            for element in result_etree:
                Parser._check_tag(element, valid_tags)
                if element.tag == "use":
                    uses.append(Parser._extract_use(element))
                elif element.tag == "table":
                    result = Parser._extract_table(element)
                    result.result_dir = result_dir
                elif element.tag == "syslog":
                    result = Parser._extract_syslog(element)
                elif element.tag == "database":
                    result = Parser._extract_database(element)
                    result.result_dir = result_dir
                if element.tag in ["table", "syslog", "database"]:
                    if result.name in sub_results:
                        raise ValueError(
                            ("Result name \"{0}\" is used " +
                             "multiple times").format(result.name))
                    sub_results[result.name] = result
                    if result.name not in results_order:
                        results_order.append(result.name)
            for result in sub_results.values():
                for use in uses:
                    result.add_uses(use)
            if len(set(results.keys()).intersection(
                    set(sub_results.keys()))) > 0:
                raise ValueError(
                    ("Result name(s) \"{0}\" is/are used " +
                     "multiple times").format(
                        ",".join(set(results.keys()).intersection(
                            set(sub_results.keys())))))

            results.update(sub_results)
        return results, results_order

    @staticmethod
    def _extract_table(etree_table):
        """Extract a table from etree"""
        name = Parser._attribute_from_element(etree_table, "name").strip()
        separator = \
            etree_table.get("separator", jube2.conf.DEFAULT_SEPARATOR)
        style = etree_table.get("style", "csv").strip()
        if style not in ["csv", "pretty", "aligned"]:
            raise ValueError("Not allowed style-type \"{0}\" "
                             "in <table name=\"{1}\">".format(style, name))
        sort_names = etree_table.get("sort", "").split(
            jube2.conf.DEFAULT_SEPARATOR)
        sort_names = [sort_name.strip() for sort_name in sort_names]
        sort_names = [
            sort_name for sort_name in sort_names if len(sort_name) > 0]
        transpose = etree_table.get("transpose")
        if transpose is not None:
            transpose = transpose.strip().lower() == "true"
        else:
            transpose = False
        res_filter = etree_table.get("filter")
        if res_filter is not None:
            res_filter = res_filter.strip()
        table = jube2.result_types.table.Table(name, style, separator,
                                               sort_names, transpose,
                                               res_filter)
        for element in etree_table:
            Parser._check_tag(element, ["column"])
            column_name = element.text
            if column_name is None:
                column_name = ""
            column_name = column_name.strip()
            if column_name == "":
                raise ValueError("Empty <column> not allowed")
            colw = element.get("colw")
            if colw is not None:
                colw = int(colw)
            title = element.get("title")
            format_string = element.get("format")
            if format_string is not None:
                format_string = format_string.strip()
            table.add_column(column_name, colw, format_string, title)
        return table

    @staticmethod
    def _extract_database(etree_database):
        """Extract a database result infos from etree"""
        name = Parser._attribute_from_element(etree_database, "name").strip()
        res_filter = etree_database.get("filter")
        if res_filter is not None:
            res_filter = res_filter.strip()
        primekeys = etree_database.get("primekeys", "")
        primekeys = primekeys.replace('[', '').replace(']', '').replace(
            "'", '').split(jube2.conf.DEFAULT_SEPARATOR)
        primekeys = [primekey.strip() for primekey in primekeys]
        primekeys = [primekey for primekey in primekeys if len(primekey) > 0]
        db_file = etree_database.get("file")
        database = jube2.result_types.database.Database(
            name, res_filter, primekeys, db_file)
        for element in etree_database:
            Parser._check_tag(element, ["key"])
            key_name = element.text
            if key_name is None:
                key_name = ""
            key_name = key_name.strip()
            if key_name == "":
                raise ValueError("Empty <key> not allowed")
            title = element.get("title")
            format_string = element.get("format")
            if format_string is not None:
                format_string = format_string.strip()
            database.add_key(key_name, format_string, title)
        return database

    @staticmethod
    def _extract_syslog(etree_syslog):
        """Extract requires syslog information from etree."""
        name = Parser._attribute_from_element(etree_syslog, "name").strip()
        # see if the host, port combination or address is given
        syslog_address = etree_syslog.get("address")
        if syslog_address is not None:
            syslog_address = \
                os.path.expandvars(os.path.expanduser(syslog_address.strip()))
        syslog_host = etree_syslog.get("host")
        if syslog_host is not None:
            syslog_host = syslog_host.strip()
        syslog_port = etree_syslog.get("port")
        if syslog_port is not None:
            syslog_port = int(syslog_port.strip())
        syslog_fmt_string = etree_syslog.get("format")
        if syslog_fmt_string is not None:
            syslog_fmt_string = syslog_fmt_string.strip()
        sort_names = etree_syslog.get("sort", "").split(
            jube2.conf.DEFAULT_SEPARATOR)
        sort_names = [sort_name.strip() for sort_name in sort_names]
        sort_names = [
            sort_name for sort_name in sort_names if len(sort_name) > 0]
        res_filter = etree_syslog.get("filter")
        if res_filter is not None:
            res_filter = res_filter.strip()
        syslog_result = jube2.result_types.syslog.SysloggedResult(
            name, syslog_address, syslog_host, syslog_port, syslog_fmt_string,
            sort_names, res_filter)

        for element in etree_syslog:
            Parser._check_tag(element, ["key"])
            key_name = element.text
            if key_name is None:
                key_name = ""
            key_name = key_name.strip()
            if key_name == "":
                raise ValueError("Empty <key> not allowed")
            title = element.get("title")
            format_string = element.get("format")
            if format_string is not None:
                format_string = format_string.strip()
            syslog_result.add_key(key_name, format_string, title)
        return syslog_result

    @staticmethod
    def _extract_use(etree_use):
        """Extract a use from etree"""
        if etree_use.text is not None:
            use_names = [use_name.strip() for use_name in
                         etree_use.text.split(jube2.conf.DEFAULT_SEPARATOR)]
            return use_names
        else:
            raise ValueError("Empty <use> found")

    def _tree_from_file(self, file_path):
        """Extract a XML tree from a file (doing implicit YAML conversion)"""
        try:
            if file_path.endswith(".xml"):
                return ET.parse(file_path)
            elif file_path.endswith(".yml") or file_path.endswith(".yaml") or \
                jube2.util.yaml_converter.\
                    YAML_Converter.is_parseable_yaml_file(file_path):
                include_path = list(self._include_path)
                include_path += Parser._read_envvar_include_path()
                file_handle = jube2.util.yaml_converter.YAML_Converter(
                    file_path, include_path, self._tags)
                data = file_handle.read()
                tree = ET.ElementTree(ET.fromstring(data))
                file_handle.close()
                return tree
            else:
                return ET.parse(file_path)
        except Exception:
            LOGGER.error("Error while parsing {0}:".format(file_path))
            raise

    def _extract_extern_set(self, filename, set_type, name, search_name=None, duplicate=None):
        """Load a parameter-/file-/substitutionset from a given file"""
        if search_name is None:
            search_name = name
        LOGGER.debug("    Searching for <{0} name=\"{1}\"> in {2}"
                     .format(set_type, search_name, filename))
        file_path = self._find_include_file(filename)
        etree = self._tree_from_file(file_path).getroot()
        Parser._remove_invalid_tags(etree, self._tags)
        self._preprocessor(etree)
        result_set = None

        # Find element in XML-tree
        elements = jube2.util.util.get_tree_elements(etree, set_type,
                                                     {"name": search_name})
        # Element can also be the root element itself
        if etree.tag == set_type:
            element = jube2.util.util.get_tree_element(
                etree, attribute_dict={"name": search_name})
            if element is not None:
                elements.append(element)

        test_duplicate=None
        if duplicate == "###initiated_with_without_duplicate_mentioning###":
            if elements[0].get("duplicate") != None:
                duplicate = elements[0].get("duplicate")
            else:
                duplicate = "replace"
        if duplicate != "###initiated_with_without_duplicate_mentioning###" and duplicate != None:
            if set_type == "parameterset":
                if elements[0].get("duplicate") == None:
                    test_duplicate = duplicate
                else:
                    test_duplicate = elements[0].get("duplicate")
            if duplicate != None:
                if test_duplicate != duplicate:
                    raise ValueError("The {0} {1} is mentioned at least twice with different duplicate options.".format(set_type, name))
        if duplicate == "###initiated_with_without_duplicate_mentioning###":
            raise Exception("Unknown error in extracting an extern set." +
                            "This should not happen. Please contact the JUBE developers.")

        if elements is not None:
            if len(elements) > 1:
                raise ValueError("\"{0}\" found multiple times in \"{1}\""
                                 .format(search_name, file_path))
            elif len(elements) == 0:
                raise ValueError("\"{0}\" not found in \"{1}\""
                                 .format(search_name, file_path))
            init_with = elements[0].get("init_with")

            # recursive external file open
            if init_with is not None:
                parts = init_with.strip().split(":")
                new_filename = parts[0]
                if len(parts) > 1:
                    new_search_name = parts[1]
                else:
                    new_search_name = search_name
                if (new_filename == filename) and \
                        (new_search_name == search_name):
                    raise ValueError(("Cannot init <{0} name=\"{1}\"> by "
                                      "itself inside \"{2}\"").format(
                                          set_type, search_name, file_path))
                result_set = self._extract_extern_set(new_filename,
                                                      set_type, name,
                                                      new_search_name, duplicate)

            if set_type == "parameterset":
                if result_set is None:
                    result_set = jube2.parameter.Parameterset(name, duplicate)
                for parameter in self._extract_parameters(elements[0]):
                    result_set.add_parameter(parameter)
            elif set_type == "substituteset":
                files, subs = self._extract_subs(elements[0])
                if result_set is None:
                    result_set = \
                        jube2.substitute.Substituteset(name, files, subs)
                else:
                    result_set.update_files(files)
                    result_set.update_substitute(subs)
            elif set_type == "fileset":
                if result_set is None:
                    result_set = jube2.fileset.Fileset(name)
                    files = self._extract_files(elements[0])
                    for file_obj in files:
                        if type(file_obj) is not jube2.fileset.Prepare:
                            file_obj.file_path_ref = \
                                os.path.join(os.path.dirname(file_path),
                                             file_obj.file_path_ref)
                            if not os.path.isabs(file_obj.file_path_ref):
                                file_obj.file_path_ref = \
                                    os.path.relpath(file_obj.file_path_ref,
                                                    self.file_path_ref)
                    result_set += files
            elif set_type == "patternset":
                if result_set is None:
                    result_set = jube2.pattern.Patternset(name)
                for pattern in self._extract_pattern(elements[0]):
                    result_set.add_pattern(pattern)
            return result_set
        else:
            raise ValueError("\"{0}\" not found in \"{1}\""
                             .format(name, file_path))

    def _extract_parametersets(self, etree):
        """Return parametersets from etree"""

        parametersets = dict()
        for element in etree.findall("parameterset"):
            name = Parser._attribute_from_element(element, "name").strip()
            if name == "":
                raise ValueError("Empty \"name\" attribute in " +
                                 "<parameterset> found.")
            LOGGER.debug("  Parsing <parameterset name=\"{0}\">".format(name))
            duplicate = element.get("duplicate", "replace").strip()
            if duplicate is None:
                duplicate="replace"
            if duplicate != "replace" and duplicate != "concat" and duplicate != "error":
                raise ValueError("Invalid \"duplicate\" attribute in " +
                                 "parameterset {0} found. Use \"replace\" (default)" +
                                 ", \"concat\" or \"error\".".format(name))
            init_with = element.get("init_with")
            if init_with is not None:
                parts = init_with.strip().split(":")
                if len(parts) > 1:
                    search_name = parts[1]
                else:
                    search_name = None
                if element.get("duplicate") == None:
                    duplicate = "###initiated_with_without_duplicate_mentioning###"
                parameterset = self._extract_extern_set(parts[0],
                                                        "parameterset", name,
                                                        search_name, duplicate)
            else:
                parameterset = jube2.parameter.Parameterset(name, duplicate)
            for parameter in self._extract_parameters(element):
                parameterset.add_parameter(parameter)
            if parameterset.name in parametersets:
                raise ValueError(
                    "\"{0}\" not unique".format(parameterset.name))
            parametersets[parameterset.name] = parameterset
        return parametersets

    @staticmethod
    def _extract_parameters(etree_parameterset):
        """Extract parameters from parameterset

        Return a list of parameters. Parameters might also include lists"""
        parameters = list()
        for param in etree_parameterset:
            Parser._check_tag(param, ["parameter"])
            name = Parser._attribute_from_element(param, "name").strip()
            if name == "":
                raise ValueError(
                    "Empty \"name\" attribute in <parameter> found.")
            if not re.match(r"^[^\d\W]\w*$", name, re.UNICODE):
                raise ValueError(("name=\"{0}\" in <parameter> " +
                                  "contains a disallowed " +
                                  "character").format(name))
            separator = param.get("separator",
                                  default=jube2.conf.DEFAULT_SEPARATOR)
            parameter_type = param.get("type", default="string").strip()
            parameter_mode = param.get("mode", default="text").strip()
            parameter_update_mode = param.get("update_mode",
                                              default="never").strip()
            if parameter_update_mode not in jube2.parameter.UPDATE_MODES:
                raise ValueError(
                    ("update_mode=\"{0}\" in " +
                     "<parameter name=\"{1}\"> does not exist")
                    .format(parameter_update_mode, name))
            export_str = param.get("export", default="false").strip()
            export = export_str.lower() == "true"

            duplicate = param.get("duplicate", "none").strip()
            if duplicate is None:
                duplicate="none"
            if duplicate != "replace" and duplicate != "concat" and duplicate != "error" and duplicate != "none":
                raise ValueError("Invalid \"duplicate\" attribute in " +
                                 "parameter {0} found. Use \"replace\"" +
                                 ", \"concat\", \"error\" or \"none\" (default).".format(name))
            if parameter_mode not in jube2.conf.ALLOWED_MODETYPES:
                raise ValueError(
                    ("parameter-mode \"{0}\" not allowed in " +
                     "<parameter name=\"{1}\">").format(parameter_mode,
                                                        name))
            value_etree = param.find("value")
            if value_etree is not None:
                if value_etree.text is None:
                    value = ""
                else:
                    value = value_etree.text.strip()
            else:
                if param.text is None:
                    value = ""
                else:
                    value = param.text.strip()
            selection_etree = param.find("selection")
            if selection_etree is not None:
                selected_value = selection_etree.text
                if selected_value is None:
                    selected_value = ""
                idx = int(selection_etree.get("idx", "-1"))
            else:
                selected_value = param.get("selection")
                idx = -1
            if selected_value is not None:
                selected_value = selected_value.strip()
            parameter = \
                jube2.parameter.Parameter.create_parameter(
                    name, value, separator, parameter_type, selected_value,
                    parameter_mode, export, update_mode=parameter_update_mode,
                    idx=idx, eval_helper=None, fixed=False, duplicate=duplicate)
            parameters.append(parameter)
        return parameters

    def _extract_patternsets(self, etree):
        """Return patternset from etree"""
        patternsets = dict()
        for element in etree.findall("patternset"):
            name = Parser._attribute_from_element(element, "name").strip()
            if name == "":
                raise ValueError("Empty \"name\" attribute in " +
                                 "<patternset> found.")
            LOGGER.debug("  Parsing <patternset name=\"{0}\">".format(name))
            init_with = element.get("init_with")
            if init_with is not None:
                parts = init_with.strip().split(":")
                if len(parts) > 1:
                    search_name = parts[1]
                else:
                    search_name = None
                patternset = self._extract_extern_set(parts[0],
                                                      "patternset", name,
                                                      search_name)
            else:
                patternset = jube2.pattern.Patternset(name)
            for pattern in Parser._extract_pattern(element):
                patternset.add_pattern(pattern)
            if patternset.name in patternsets:
                raise ValueError("\"{0}\" not unique".format(patternset.name))
            patternsets[patternset.name] = patternset
        return patternsets

    @staticmethod
    def _extract_pattern(etree_patternset):
        """Extract pattern from patternset

        Return a list of pattern"""
        patternlist = list()
        for pattern in etree_patternset:
            Parser._check_tag(pattern, ["pattern"])
            name = Parser._attribute_from_element(pattern, "name").strip()
            if name == "":
                raise ValueError(
                    "Empty \"name\" attribute in <pattern> found.")
            if not re.match(r"^[^\d\W]\w*$", name, re.UNICODE):
                raise ValueError(("name=\"{0}\" in <pattern> " +
                                  "contains a disallowed " +
                                  "character").format(name))
            pattern_mode = pattern.get("mode", default="pattern").strip()
            if pattern_mode not in \
                    set(["pattern", "text"]).union(
                        jube2.conf.ALLOWED_SCRIPTTYPES):
                raise ValueError(("pattern-mdoe \"{0}\" not allowed in " +
                                  "<pattern name=\"{1}\">").format(
                    pattern_mode, name))
            content_type = pattern.get("type", default="string").strip()
            unit = pattern.get("unit", "").strip()
            dotall = \
                pattern.get("dotall", "false").strip().lower() == "true"
            default = pattern.get("default")
            if default is not None:
                default = default.strip()
            if pattern.text is None:
                value = ""
            else:
                value = pattern.text.strip()
            patternlist.append(jube2.pattern.Pattern(name, value, pattern_mode,
                                                     content_type, unit,
                                                     default, dotall))
        return patternlist

    def _extract_filesets(self, etree):
        """Return filesets from etree"""
        filesets = dict()
        for element in etree.findall("fileset"):
            name = Parser._attribute_from_element(element, "name").strip()
            if name == "":
                raise ValueError(
                    "Empty \"name\" attribute in <fileset> found.")
            LOGGER.debug("  Parsing <fileset name=\"{0}\">".format(name))
            init_with = element.get("init_with")
            filelist = Parser._extract_files(element)
            if name in filesets:
                raise ValueError("\"{0}\" not unique".format(name))
            if init_with is not None:
                parts = init_with.strip().split(":")
                if len(parts) > 1:
                    search_name = parts[1]
                else:
                    search_name = None
                filesets[name] = self._extract_extern_set(parts[0],
                                                          "fileset", name,
                                                          search_name)
            else:
                filesets[name] = jube2.fileset.Fileset(name)
            filesets[name] += filelist
        return filesets

    @staticmethod
    def _extract_files(etree_fileset):
        """Return filelist from fileset-etree"""
        filelist = list()
        valid_tags = ["copy", "link", "prepare"]
        for etree_file in etree_fileset:
            Parser._check_tag(etree_file, valid_tags)
            if etree_file.tag in ["copy", "link"]:
                separator = etree_file.get(
                    "separator", jube2.conf.DEFAULT_SEPARATOR)
                source_dir = etree_file.get("directory", default="").strip()
                # New source_dir attribute overwrites deprecated directory
                # attribute
                source_dir_new = etree_file.get("source_dir")
                target_dir = etree_file.get("target_dir", default="").strip()
                if source_dir_new is not None:
                    source_dir = source_dir_new.strip()
                active = etree_file.get("active", "true").strip()
                file_path_ref = etree_file.get("file_path_ref")
                alt_name = etree_file.get("name")
                # Check if the filepath is relativly seen to working dir or the
                # position of the xml-input-file
                is_internal_ref = \
                    etree_file.get("rel_path_ref",
                                   default="external").strip() == "internal"
                if etree_file.text is None:
                    raise ValueError("Empty filelist in <{0}> found."
                                     .format(etree_file.tag))
                files = jube2.util.util.safe_split(etree_file.text.strip(),
                                                   separator)
                if alt_name is not None:
                    # Use the new alternativ filenames
                    names = [name.strip() for name in
                             alt_name.split(jube2.conf.DEFAULT_SEPARATOR)]
                    if len(names) != len(files):
                        raise ValueError("Namelist and filelist must have " +
                                         "same length in <{0}>".
                                         format(etree_file.tag))
                else:
                    names = None
                for i, file_path in enumerate(files):
                    path = file_path.strip()
                    if names is not None:
                        name = names[i]
                    else:
                        name = None
                    if etree_file.tag == "copy":
                        file_obj = jube2.fileset.Copy(
                            path, name, is_internal_ref, active, source_dir,
                            target_dir)
                    elif etree_file.tag == "link":
                        file_obj = jube2.fileset.Link(
                            path, name, is_internal_ref, active, source_dir,
                            target_dir)
                    if file_path_ref is not None:
                        file_obj.file_path_ref = \
                            os.path.expandvars(os.path.expanduser(
                                file_path_ref.strip()))
                    filelist.append(file_obj)
            elif etree_file.tag == "prepare":
                cmd = etree_file.text
                if cmd is None:
                    cmd = ""
                cmd = cmd.strip()
                stdout_filename = etree_file.get("stdout")
                if stdout_filename is not None:
                    stdout_filename = stdout_filename.strip()
                stderr_filename = etree_file.get("stderr")
                if stderr_filename is not None:
                    stderr_filename = stderr_filename.strip()
                alt_work_dir = etree_file.get("work_dir")
                if alt_work_dir is not None:
                    alt_work_dir = alt_work_dir.strip()
                active = etree_file.get("active", "true").strip()

                prepare_obj = jube2.fileset.Prepare(cmd, stdout_filename,
                                                    stderr_filename,
                                                    alt_work_dir, active)
                filelist.append(prepare_obj)
        return filelist

    def _extract_substitutesets(self, etree):
        """Extract substitutesets from benchmark

        Return a dict of substitute sets, e.g.
        {"compilesub": ([iofile0,...], [sub0,...])}"""
        substitutesets = dict()
        for element in etree.findall("substituteset"):
            name = Parser._attribute_from_element(element, "name").strip()
            if name == "":
                raise ValueError("Empty \"name\" attribute in " +
                                 "<substituteset> found.")
            LOGGER.debug("  Parsing <substituteset name=\"{0}\">".format(name))
            init_with = element.get("init_with")
            files, subs = Parser._extract_subs(element)
            if name in substitutesets:
                raise ValueError("\"{0}\" not unique".format(name))
            if init_with is not None:
                parts = init_with.strip().split(":")
                if len(parts) > 1:
                    search_name = parts[1]
                else:
                    search_name = None
                substitutesets[name] = \
                    self._extract_extern_set(parts[0], "substituteset", name,
                                             search_name)
                substitutesets[name].update_files(files)
                substitutesets[name].update_substitute(subs)
            else:
                substitutesets[name] = \
                    jube2.substitute.Substituteset(name, files, subs)
        return substitutesets

    @staticmethod
    def _extract_subs(etree_substituteset):
        """Extract files for substitution and subs from substituteset

        Return a files dict for substitute and a dict of subs
        """
        valid_tags = ["iofile", "sub"]
        files = list()
        subs = dict()
        for sub in etree_substituteset:
            Parser._check_tag(sub, valid_tags)
            if sub.tag == "iofile":
                in_file = Parser._attribute_from_element(sub, "in").strip()
                out_file = Parser._attribute_from_element(
                    sub, "out").strip()
                out_mode = sub.get("out_mode", "w").strip()
                if out_mode not in ["w", "a"]:
                    raise ValueError(
                        "out_mode in <iofile> must be \"w\" or \"a\"")
                in_file = os.path.expandvars(os.path.expanduser(in_file))
                out_file = os.path.expandvars(os.path.expanduser(out_file))
                files.append((out_file, in_file, out_mode))
            elif sub.tag == "sub":
                source = "" + \
                    Parser._attribute_from_element(sub, "source").strip()
                if source == "":
                    raise ValueError(
                        "Empty \"source\" attribute in <sub> found.")
                dest = sub.get("dest")
                if dest is None:
                    dest = sub.text
                    if dest is None:
                        dest = ""
                dest = dest.strip() + ""
                subs[source] = dest
        return (files, subs)

    @staticmethod
    def _attribute_from_element(element, attribute):
        """Return attribute from element
        element -- etree.Element
        attribute -- string
        Raise a useful exception if value not found """
        value = element.get(attribute)
        if value is None:
            raise ValueError("Missing attribute '{0}' in <{1}>"
                             .format(attribute, element.tag))
        return value

    @staticmethod
    def _check_tag(element, valid_tags):
        """Check tag and raise a useful exception if needed
        element -- etree.Element
        valid_tags -- list of valid strings
        """
        if element.tag not in valid_tags:
            raise ValueError(("Unknown tag or tag used in wrong " +
                              "position:\n{0}").format(
                jube2.util.output.element_tree_tostring(
                    element, encoding="UTF-8")))
