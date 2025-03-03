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
"""The Benchmark class manages the benchmark process"""

from __future__ import (print_function,
                        unicode_literals,
                        division)

import multiprocessing as mp
import xml.etree.ElementTree as ET
import xml.dom.minidom as DOM
import logging
import os
import re
import stat
import pprint
import shutil
import itertools
import jube2.parameter
import jube2.util.util
import jube2.util.output
import jube2.conf
import jube2.log

LOGGER = jube2.log.get_logger(__name__)


class Benchmark(object):

    """The Benchmark class contains all data to run a benchmark"""

    def __init__(self, name, outpath, parametersets, substitutesets,
                 filesets, patternsets, steps, analyser, results,
                 results_order, comment="", tags=None, file_path_ref="."):
        self._name = name
        self._outpath = outpath
        self._parametersets = parametersets
        self._substitutesets = substitutesets
        self._filesets = filesets
        self._patternsets = patternsets
        self._steps = steps
        self._analyser = analyser
        for analyser in self._analyser.values():
            analyser.benchmark = self
        self._results = results
        self._results_order = results_order
        for result in self._results.values():
            result.benchmark = self
        self._workpackages = dict()
        self._work_stat = jube2.util.util.WorkStat()
        self._comment = comment
        self._id = -1
        self._file_path_ref = file_path_ref
        if tags is None:
            self._tags = set()
        else:
            self._tags = tags

    @property
    def name(self):
        """Return benchmark name"""
        return self._name

    @property
    def comment(self):
        """Return comment string"""
        return self._comment

    @property
    def tags(self):
        """Return set of tags"""
        return self._tags

    @comment.setter
    def comment(self, new_comment):
        """Set new comment string"""
        self._comment = new_comment

    @property
    def parametersets(self):
        """Return parametersets"""
        return self._parametersets

    @property
    def patternsets(self):
        """Return patternsets"""
        return self._patternsets

    @property
    def analyser(self):
        """Return analyser"""
        return self._analyser

    @property
    def results(self):
        """Return results"""
        return self._results

    @property
    def results_order(self):
        """Return results_order"""
        return self._results_order

    @property
    def file_path_ref(self):
        """Get file path reference"""
        return self._file_path_ref

    @file_path_ref.setter
    def file_path_ref(self, file_path_ref):
        """Set file path reference"""
        self._file_path_ref = file_path_ref

    @property
    def outpath(self):
        """Return outpath"""
        return self._outpath

    @outpath.setter
    def outpath(self, new_outpath):
        """Overwrite outpath"""
        self._outpath = new_outpath

    @property
    def substitutesets(self):
        """Return substitutesets"""
        return self._substitutesets

    @property
    def workpackages(self):
        """Return workpackages"""
        return self._workpackages

    def add_tags(self, other_tags):
        if other_tags is not None:
            self._tags = self._tags.union(set(other_tags))

    def workpackage_by_id(self, wp_id):
        """Search and return a benchmark workpackage by its wp_id"""
        for stepname in self._workpackages:
            for workpackage in self._workpackages[stepname]:
                if workpackage.id == wp_id:
                    return workpackage
        return None

    def remove_workpackage(self, workpackage_to_delete):
        """Remove a specifc workpackage"""
        stepname = workpackage_to_delete.step.name
        if stepname in self._workpackages and \
                workpackage_to_delete in self._workpackages[stepname]:
            self._workpackages[stepname].remove(workpackage_to_delete)

    @property
    def work_stat(self):
        """Return work queue"""
        return self._work_stat

    @property
    def filesets(self):
        """Return filesets"""
        return self._filesets

    def delete_bench_dir(self):
        """Delete all data inside benchmark directory"""
        if os.path.exists(self.bench_dir):
            shutil.rmtree(self.bench_dir, ignore_errors=True)

    @property
    def steps(self):
        """Return steps"""
        return self._steps

    @property
    def workpackage_status(self):
        """Retun workpackage information dict"""
        result_dict = dict()
        for stepname in self._workpackages:
            result_dict[stepname] = {"all": 0,
                                     "open": 0,
                                     "wait": 0,
                                     "error": 0,
                                     "done": 0}
            for workpackage in self._workpackages[stepname]:
                result_dict[stepname]["all"] += 1
                if workpackage.done:
                    result_dict[stepname]["done"] += 1
                elif workpackage.error:
                    result_dict[stepname]["error"] += 1
                elif workpackage.started:
                    result_dict[stepname]["wait"] += 1
                else:
                    result_dict[stepname]["open"] += 1
        return result_dict

    @property
    def benchmark_status(self):
        """Retun global workpackage information dict"""
        result_dict = {"all": 0,
                       "open": 0,
                       "wait": 0,
                       "error": 0,
                       "done": 0}

        for status in self.workpackage_status.values():
            result_dict["all"] += status["all"]
            result_dict["open"] += status["open"]
            result_dict["wait"] += status["wait"]
            result_dict["error"] += status["error"]
            result_dict["done"] += status["done"]

        return result_dict

    @property
    def id(self):
        """Return benchmark id"""
        return self._id

    @id.setter
    def id(self, new_id):
        """Set new benchmark id"""
        self._id = new_id

    def get_jube_parameterset(self):
        """Return parameterset which contains benchmark related
        information"""
        parameterset = jube2.parameter.Parameterset()
        # benchmark id
        parameterset.add_parameter(
            jube2.parameter.Parameter.
            create_parameter(
                "jube_benchmark_id", str(self._id), parameter_type="int",
                update_mode=jube2.parameter.JUBE_MODE))

        # benchmark id with padding
        parameterset.add_parameter(
            jube2.parameter.Parameter.
            create_parameter("jube_benchmark_padid",
                             jube2.util.util.id_dir("", self._id),
                             parameter_type="string",
                             update_mode=jube2.parameter.JUBE_MODE))

        # benchmark name
        parameterset.add_parameter(
            jube2.parameter.Parameter.
            create_parameter("jube_benchmark_name", self._name,
                             update_mode=jube2.parameter.JUBE_MODE))

        # benchmark home
        parameterset.add_parameter(
            jube2.parameter.Parameter.
            create_parameter("jube_benchmark_home",
                             os.path.abspath(self._file_path_ref),
                             update_mode=jube2.parameter.JUBE_MODE))

        # benchmark rundir
        parameterset.add_parameter(
            jube2.parameter.Parameter.
            create_parameter("jube_benchmark_rundir",
                             os.path.abspath(self.bench_dir),
                             update_mode=jube2.parameter.JUBE_MODE))

        timestamps = jube2.util.util.read_timestamps(
            os.path.join(self.bench_dir, jube2.conf.TIMESTAMPS_INFO))

        # benchmark start
        parameterset.add_parameter(
            jube2.parameter.Parameter.create_parameter(
                "jube_benchmark_start",
                timestamps.get("start", "").replace(" ", "T"),
                update_mode=jube2.parameter.JUBE_MODE))

        return parameterset

    def etree_repr(self, new_cwd=None):
        """Return etree object representation"""
        benchmark_etree = ET.Element("benchmark")
        if len(self._comment) > 0:
            comment_element = ET.SubElement(benchmark_etree, "comment")
            comment_element.text = self._comment
        benchmark_etree.attrib["name"] = self._name
        # Modify file_path_ref and outpath to be relativly correct towards
        # new configuration file position
        if new_cwd is not None:
            benchmark_etree.attrib["file_path_ref"] = \
                os.path.relpath(self._file_path_ref, new_cwd)
            if not os.path.isabs(self._outpath):
                benchmark_etree.attrib["outpath"] = \
                    os.path.relpath(self._outpath, new_cwd)
            else:
                benchmark_etree.attrib["outpath"] = self._outpath

        for parameterset in self._parametersets.values():
            benchmark_etree.append(parameterset.etree_repr())
        for substituteset in self._substitutesets.values():
            benchmark_etree.append(substituteset.etree_repr())
        for fileset in self._filesets.values():
            benchmark_etree.append(fileset.etree_repr())
        for patternset in self._patternsets.values():
            benchmark_etree.append(patternset.etree_repr())
        for step in self._steps.values():
            benchmark_etree.append(step.etree_repr())
        for analyser in self._analyser.values():
            benchmark_etree.append(analyser.etree_repr())
        for result_name in self._results_order:
            result = self._results[result_name]
            benchmark_etree.append(result.etree_repr())
        return benchmark_etree

    def __repr__(self):
        return pprint.pformat(self.__dict__)

    def _create_initial_workpackages(self):
        """Create initial workpackages of current benchmark and create graph
        structure."""
        self._workpackages = dict()
        self._work_stat = jube2.util.util.WorkStat()

        # Create workpackage storage
        for step_name in self._steps:
            self._workpackages[step_name] = list()

        # Create initial workpackages
        for step in self._steps.values():
            if len(step.depend) == 0:
                new_workpackages = \
                    self._create_new_workpackages_with_parents(step)
                self._workpackages[step.name] += new_workpackages
                for workpackage in new_workpackages:
                    workpackage.queued = True
                    self._work_stat.put(workpackage)

    def analyse(self, show_info=True, specific_analyser_name=None):
        """Run analyser"""

        if show_info:
            LOGGER.info(">>> Start analyse")

        if specific_analyser_name is not None and \
                specific_analyser_name in self._analyser:
            self._analyser[specific_analyser_name].analyse()
        else:
            for analyser in self._analyser.values():
                analyser.analyse()
        if ((not jube2.conf.DEBUG_MODE) and
                (os.access(self.bench_dir, os.W_OK))):
            self.write_analyse_data(os.path.join(self.bench_dir,
                                                 jube2.conf.ANALYSE_FILENAME))
        if show_info:
            LOGGER.info(">>> Analyse finished")

    def create_result(self, only=None, show=False, data_list=None, style=None):
        """Show benchmark result"""
        if only is None:
            only = [result_name for result_name in self._results]
        if data_list is None:
            data_list = list()
        for result_name in self._results_order:
            result = self._results[result_name]
            if result.name in only:
                result_data = result.create_result_data(style)
                if result.result_dir is None:
                    result_dir = os.path.join(self.bench_dir,
                                              jube2.conf.RESULT_DIRNAME)
                else:
                    result_dir = result.result_dir
                    result_dir = os.path.expanduser(result_dir)
                    result_dir = os.path.expandvars(result_dir)
                    result_dir = jube2.util.util.id_dir(
                        os.path.join(self.file_path_ref, result_dir), self.id)
                if (not os.path.exists(result_dir)) and \
                   (not jube2.conf.DEBUG_MODE):
                    try:
                        os.makedirs(result_dir)
                    except OSError:
                        pass
                if ((not jube2.conf.DEBUG_MODE) and
                        (os.path.exists(result_dir)) and
                        (os.access(result_dir, os.W_OK))):
                    filename = os.path.join(result_dir,
                                            "{0}.dat".format(result.name))
                else:
                    filename = None
                result_data.create_result(show=show, filename=filename)

                if result_data in data_list:
                    data_list[data_list.index(result_data)].add_result_data(
                        result_data)
                else:
                    data_list.append(result_data)
        return data_list

    def update_analyse_and_result(self, new_patternsets, new_analyser,
                                  new_results, new_results_order, new_cwd):
        """Update analyser and result data"""
        if os.path.exists(self.bench_dir):
            LOGGER.debug("Update analyse and result data")
            self._patternsets = new_patternsets
            old_analyser = self._analyser
            self._analyser = new_analyser
            self._results = new_results
            self._results_order = new_results_order
            for analyser in self._analyser.values():
                if analyser.name in old_analyser:
                    analyser.analyse_result = \
                        old_analyser[analyser.name].analyse_result
                analyser.benchmark = self
            for result in self._results.values():
                result.benchmark = self
                # change result dir position relative to cwd
                if (result.result_dir is not None) and \
                   (new_cwd is not None) and \
                   (not os.path.isabs(result.result_dir)):
                    result.result_dir = \
                        os.path.join(new_cwd, result.result_dir)
            if ((not jube2.conf.DEBUG_MODE) and
                    (os.access(self.bench_dir, os.W_OK))):
                self.write_benchmark_configuration(
                    os.path.join(self.bench_dir,
                                 jube2.conf.CONFIGURATION_FILENAME),
                    outpath="..")

    def write_analyse_data(self, filename):
        """All analyse data will be written to given file
        using xml representation"""
        # Create root-tag and append analyser
        analyse_etree = ET.Element("analyse")
        for analyser_name in self._analyser:
            analyser_etree = ET.SubElement(analyse_etree, "analyser")
            analyser_etree.attrib["name"] = analyser_name
            for etree in self._analyser[analyser_name].analyse_etree_repr():
                analyser_etree.append(etree)
        xml = jube2.util.output.element_tree_tostring(
            analyse_etree, encoding="UTF-8")
        # Using dom for pretty-print
        dom = DOM.parseString(xml.encode("UTF-8"))
        fout = open(filename, "wb")
        fout.write(dom.toprettyxml(indent="  ", encoding="UTF-8"))
        fout.close()

    def _create_new_workpackages_for_workpackage(self, workpackage):
        """Create and return new workpackages if given workpackage
        was finished."""
        all_new_workpackages = list()
        if not workpackage.done or len(workpackage.children) > 0:
            return all_new_workpackages
        LOGGER.debug(("Create new workpackages for workpackage"
                      " {0}({1})").format(
            workpackage.step.name, workpackage.id))
        # Search for dependent steps
        dependent_steps = [step for step in self._steps.values() if
                           workpackage.step.name in step.depend]

        # Search for possible workpackage parents
        for dependent_step in dependent_steps:
            parent_workpackages = [[
                parent_workpackage for parent_workpackage in
                self._workpackages[step_name] if parent_workpackage.done]
                for step_name in dependent_step.depend
                if (step_name in self._workpackages) and
                   (step_name != workpackage.step.name)]
            parent_workpackages.append([workpackage])

            # Create all possible parent combinations
            workpackage_combinations = \
                [iterator for iterator in
                 itertools.product(*parent_workpackages)]
            possible_combination = len(workpackage_combinations)
            for workpackage_combination in workpackage_combinations:
                new_workpackages = self._create_new_workpackages_with_parents(
                    dependent_step, workpackage_combination)
                if len(new_workpackages) > 0:
                    possible_combination -= 1

                # Create links: parent workpackages -> new children
                for new_workpackage in new_workpackages:
                    for parent in workpackage_combination:
                        parent.add_children(new_workpackage)

                self._workpackages[dependent_step.name] += new_workpackages
                all_new_workpackages += new_workpackages
            if possible_combination > 0:
                LOGGER.debug(("  {0} workpackages combinations were skipped"
                              " while checking possible parent combinations"
                              " for step {1}").format(possible_combination,
                                                      dependent_step.name))

        LOGGER.debug("  {0} new workpackages created".format(
            len(all_new_workpackages)))
        return all_new_workpackages

    def _create_new_workpackages_with_parents(self, step,
                                              parent_workpackages=None):
        """Create workpackages with given parent combination"""
        if parent_workpackages is None:
            parent_workpackages = list()
        # Combine and check parent parametersets
        parameterset = jube2.parameter.Parameterset()
        incompatible_parameter_names = set()
        for parent_workpackage in parent_workpackages:
            # Check weather parameter combination is possible or not.
            # JUBE Parameter can be ignored
            incompatible_parameter_names = incompatible_parameter_names.union(
                parameterset.get_incompatible_parameter(
                    parent_workpackage.parameterset,
                    update_mode=jube2.parameter.JUBE_MODE))
            parameterset.add_parameterset(
                parent_workpackage.parameterset)

        # Sort parent workpackges after total iteration number and name
        sorted_parents = list(parent_workpackages)
        sorted_parents.sort(key=lambda x: x.step.name)
        sorted_parents.sort(key=lambda x: x.step.iterations)

        iteration_base = 0
        for i, parent in enumerate(sorted_parents):
            if i == 0:
                iteration_base = parent.iteration
            else:
                iteration_base = \
                    parent.step.iterations * iteration_base + parent.iteration

        parameterset.remove_jube_parameter()

        # Create new workpackages
        new_workpackages = step.create_workpackages(
            self, parameterset,
            iteration_base=iteration_base,
            parents=parent_workpackages,
            incompatible_parameters=incompatible_parameter_names)

        # Update iteration sibling connections
        if len(parent_workpackages) > 0 and len(new_workpackages) > 0:
            for sibling in parent_workpackages[0].iteration_siblings:
                if sibling != parent_workpackages[0]:
                    for child in sibling.children:
                        for workpackage in new_workpackages:
                            if workpackage.parameterset.is_compatible(
                                    child.parameterset,
                                    update_mode=jube2.parameter.JUBE_MODE):
                                workpackage.iteration_siblings.add(child)
                                child.iteration_siblings.add(workpackage)

        return new_workpackages

    def new_run(self):
        """Create workpackage structure and run benchmark"""
        # Check benchmark consistency
        LOGGER.debug("Start consistency check")
        jube2.util.util.consistency_check(self)

        # Create benchmark directory
        LOGGER.debug("Create benchmark directory")
        self._create_bench_dir()

        # Change logfile
        jube2.log.change_logfile_name(os.path.join(
            self.bench_dir, jube2.conf.LOGFILE_RUN_NAME))
        # Move parse logfile into benchmark folder
        if os.path.isfile(os.path.join(self._file_path_ref,
                                       jube2.conf.DEFAULT_LOGFILE_NAME)):
            shutil.move(os.path.join(self._file_path_ref,
                                     jube2.conf.DEFAULT_LOGFILE_NAME),
                        os.path.join(self.bench_dir,
                                     jube2.conf.LOGFILE_PARSE_NAME))

        # Reset Workpackage counter
        jube2.workpackage.Workpackage.id_counter = 0

        # Create initial workpackages
        LOGGER.debug("Create initial workpackages")
        self._create_initial_workpackages()

        # Store workpackage information
        LOGGER.debug("Store initial workpackage information")
        self.write_workpackage_information(
            os.path.join(self.bench_dir, jube2.conf.WORKPACKAGES_FILENAME))

        LOGGER.debug("Start benchmark run")

        self.run()

    def run(self):
        """Run benchmark"""
        title = "benchmark: {0}".format(self._name)
        title += "\nid: {0}".format(self._id)
        if jube2.conf.DEBUG_MODE:
            title += " ---DEBUG_MODE---"
        title += "\n\n{0}".format(self._comment)
        infostr = jube2.util.output.text_boxed(title)
        LOGGER.info(infostr)

        if not jube2.conf.HIDE_ANIMATIONS:
            print("\nRunning workpackages (#=done, 0=wait, E=error):")
            status = self.benchmark_status
            jube2.util.output.print_loading_bar(
                status["done"], status["all"], status["wait"], status["error"])

        # Handle all workpackages in given order
        while not self._work_stat.empty():
            workpackage = self._work_stat.get()

            run_parallel = False

            def collect_result(val):
                """used collect return values from pool.apply_async"""
                # run postprocessing of each wp
                for i, wp in enumerate(self._workpackages[val["step_name"]]):
                    if wp.id == val["id"]:
                        if(len(val) == 2):  # workpackage is done or its execution was erroneous
                            pass
                        else:
                            # update corresponding wp in self._workpackage with modified wp
                            wp.env = val["env"]
                            # restore the parameters containing a method of a class,
                            # which needed to be deleted within the multiprocess
                            # execution to avoid excessive memory usage
                            for p in wp._parameterset.all_parameters:
                                if(p.search_method(propertyString="eval_helper",
                                                   recursiveProperty="based_on")):
                                    val["parameterset"].add_parameter(p)
                            wp.parameterset = val["parameterset"]
                            wp.cycle = val["cycle"]
                        self.wp_post_run_config(wp)
                        break

            def log_e(e):
                """used to print error_callback from pool.apply_async"""
                print(e)
            # TODO
            # writeXML position(y) - replace by database
            # TODO END
            if not workpackage.done:
                # execute wps in parallel which have the same name
                if workpackage.step.procs > 1:
                    run_parallel = True
                    procs = workpackage.step.procs
                    name = workpackage.step.name
                    pool = mp.Pool(processes=procs)

                    # add wps to the parallel pool as long as they have the same name
                    while True:
                        pool.apply_async(workpackage.run, args=('p',),
                                         callback=collect_result, error_callback=log_e)

                        if not self._work_stat.empty():
                            workpackage = self._work_stat.get()
                            # push back as first element of _work_stat and
                            # terminate parallel loop
                            if workpackage.step.name != name:
                                self._work_stat.push_back(workpackage)
                                break
                        else:
                            break

                    pool.close()
                    pool.join()
                else:
                    workpackage.run()

            if run_parallel == True:
                # merge parallel run log files into the main run log file and
                # delete the parallel logs
                log_fname = jube2.log.LOGFILE_NAME.split('/')[-1]
                filenames = [file for file in os.listdir(self.bench_dir)
                             if file.startswith(log_fname.split('.')[0]) and
                             file != log_fname]
                filenames.sort(key=lambda o: int(re.split('_|\.', o)[1]))
                with open(os.path.join(self.bench_dir,
                                       jube2.conf.LOGFILE_RUN_NAME), 'a') as outfile:
                    for fname in filenames:
                        with open(os.path.join(self.bench_dir, fname), 'r') as infile:
                            contents = infile.read()
                            outfile.write(contents)
                        os.remove(os.path.join(self.bench_dir, fname))

                run_parallel = False
            else:
                self.wp_post_run_config(workpackage)

            # Store workpackage information
            self.write_workpackage_information(
                os.path.join(self.bench_dir, jube2.conf.WORKPACKAGES_FILENAME))

        print("\n")
        status_data = [("stepname", "all", "open", "wait", "error", "done")]
        status_data += [(stepname, str(_status["all"]), str(_status["open"]),
                         str(_status["wait"]), str(_status["error"]),
                         str(_status["done"]))
                        for stepname, _status in
                        self.workpackage_status.items()]
        LOGGER.info(jube2.util.output.text_table(
            status_data, use_header_line=True, indent=2))

        LOGGER.info("\n>>>> Benchmark information and " +
                    "further useful commands:")
        LOGGER.info(">>>>       id: {0}".format(self._id))
        LOGGER.info(">>>>   handle: {0}".format(self._outpath))
        LOGGER.info(">>>>      dir: {0}".format(self.bench_dir))

        status = self.benchmark_status
        if status["all"] != status["done"]:
            LOGGER.info((">>>> continue: jube continue {0} " +
                         "--id {1}").format(self._outpath, self._id))
        LOGGER.info((">>>>  analyse: jube analyse {0} " +
                     "--id {1}").format(self._outpath, self._id))
        LOGGER.info((">>>>   result: jube result {0} " +
                     "--id {1}").format(self._outpath, self._id))
        LOGGER.info((">>>>     info: jube info {0} " +
                     "--id {1}").format(self._outpath, self._id))
        LOGGER.info((">>>>      log: jube log {0} " +
                     "--id {1}").format(self._outpath, self._id))
        LOGGER.info(jube2.util.output.text_line() + "\n")

    def wp_post_run_config(self, workpackage):
        """additional processing of workpackage:
        - update status bar
        - build up queue after restart
        """
        self._create_new_workpackages_for_workpackage(workpackage)

        # Update queues (move waiting workpackages to work queue
        # if possible)
        self._work_stat.update_queues(workpackage)

        if not jube2.conf.HIDE_ANIMATIONS:
            status = self.benchmark_status
            jube2.util.output.print_loading_bar(
                status["done"], status["all"], status["wait"],
                status["error"])
        workpackage.queued = False

        for mode in ("only_started", "all"):
            for child in workpackage.children:
                all_done = True
                for parent in child.parents:
                    all_done = all_done and parent.done
                if all_done:
                    if (mode == "only_started" and child.started) or \
                            (mode == "all" and (not child.queued)):
                        child.queued = True
                        self._work_stat.put(child)

    def _create_bench_dir(self):
        """Create the directory for a benchmark."""
        # Get group_id if available (given by JUBE_GROUP_NAME)
        group_id = jube2.util.util.check_and_get_group_id()
        # Check if outpath exists
        if not (os.path.exists(self._outpath) and
                os.path.isdir(self._outpath)):
            os.makedirs(self._outpath)
            if group_id is not None:
                os.chown(self._outpath, os.getuid(), group_id)
        # Generate unique ID in outpath
        if self._id < 0:
            self._id = jube2.util.util.get_current_id(self._outpath) + 1
        if os.path.exists(self.bench_dir):
            raise RuntimeError("Benchmark directory \"{0}\" already exists"
                               .format(self.bench_dir))

        os.makedirs(self.bench_dir)
        # If JUBE_GROUP_NAME is given, set GID-Bit and change group
        if group_id is not None:
            os.chown(self.bench_dir, os.getuid(), group_id)
            os.chmod(self.bench_dir,
                     os.stat(self.bench_dir).st_mode | stat.S_ISGID)
        self.write_benchmark_configuration(
            os.path.join(self.bench_dir, jube2.conf.CONFIGURATION_FILENAME),
            outpath="..")
        jube2.util.util.update_timestamps(os.path.join(
            self.bench_dir, jube2.conf.TIMESTAMPS_INFO), "start", "change")

    def write_benchmark_configuration(self, filename, outpath=None):
        """The current benchmark configuration will be written to given file
        using xml representation"""
        # Create root-tag and append single benchmark
        benchmarks_etree = ET.Element("jube")
        benchmarks_etree.attrib["version"] = jube2.conf.JUBE_VERSION
        # Store tag information
        if len(self._tags) > 0:
            selection_etree = ET.SubElement(benchmarks_etree, "selection")
            for tag in self._tags:
                tag_etree = ET.SubElement(selection_etree, "tag")
                tag_etree.text = tag

        benchmark_etree = self.etree_repr(new_cwd=self.bench_dir)
        if outpath is not None:
            benchmark_etree.attrib["outpath"] = outpath

        benchmarks_etree.append(benchmark_etree)
        xml = jube2.util.output.element_tree_tostring(
            benchmarks_etree, encoding="UTF-8")
        # Using dom for pretty-print
        dom = DOM.parseString(xml.encode('UTF-8'))
        fout = open(filename, "wb")
        fout.write(dom.toprettyxml(indent="  ", encoding="UTF-8"))
        fout.close()

    def reset_all_workpackages(self):
        """Reset workpackage state"""
        for workpackages in self._workpackages.values():
            for workpackage in workpackages:
                workpackage.done = False

    def write_workpackage_information(self, filename):
        """All workpackage information will be written to given file
        using xml representation"""
        # Create root-tag and append workpackages
        workpackages_etree = ET.Element("workpackages")
        for workpackages in self._workpackages.values():
            for workpackage in workpackages:
                workpackages_etree.append(workpackage.etree_repr())
        xml = jube2.util.output.element_tree_tostring(
            workpackages_etree, encoding="UTF-8")
        # Using dom for pretty-print
        dom = DOM.parseString(xml.encode("UTF-8"))
        fout = open(filename, "wb")
        fout.write(dom.toprettyxml(indent="  ", encoding="UTF-8"))
        fout.close()

    def set_workpackage_information(self, workpackages, work_stat):
        """Set new workpackage information"""
        self._workpackages = workpackages
        self._work_stat = work_stat

    @property
    def bench_dir(self):
        """Return benchmark directory"""
        return jube2.util.util.id_dir(self._outpath, self._id)
