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
"""Step contains the commands for steps"""

from __future__ import (print_function,
                        unicode_literals,
                        division)

import subprocess
import os
import re
import time
import xml.etree.ElementTree as ET
import jube2.util.util
import jube2.conf
import jube2.log
import jube2.parameter

LOGGER = jube2.log.get_logger(__name__)


class Step(object):

    """A Step represent one execution step. It contains a list of
    Do-operations and multiple parametersets, substitutionsets and filesets.
    A Step is a template for Workpackages.
    """

    def __init__(self, name, depend, iterations=1, alt_work_dir=None,
                 shared_name=None, export=False, max_wps="0",
                 active="true", suffix="", cycles=1, procs=1, do_log_file=None):
        self._name = name
        self._use = list()
        self._operations = list()
        self._iterations = iterations
        self._depend = depend
        self._alt_work_dir = alt_work_dir
        self._shared_name = shared_name
        self._export = export
        self._max_wps = max_wps
        self._active = active
        self._suffix = suffix
        self._cycles = cycles
        self._procs = procs
        self._do_log_file = do_log_file

    def etree_repr(self):
        """Return etree object representation"""
        step_etree = ET.Element("step")
        step_etree.attrib["name"] = self._name
        if len(self._depend) > 0:
            step_etree.attrib["depend"] = \
                jube2.conf.DEFAULT_SEPARATOR.join(self._depend)
        if self._alt_work_dir is not None:
            step_etree.attrib["work_dir"] = self._alt_work_dir
        if self._shared_name is not None:
            step_etree.attrib["shared"] = self._shared_name
        if self._active != "true":
            step_etree.attrib["active"] = self._active
        if self._suffix != "":
            step_etree.attrib["suffix"] = self._suffix
        if self._export:
            step_etree.attrib["export"] = "true"
        if self._max_wps != "0":
            step_etree.attrib["max_async"] = self._max_wps
        if self._iterations > 1:
            step_etree.attrib["iterations"] = str(self._iterations)
        if self._cycles > 1:
            step_etree.attrib["cycles"] = str(self._cycles)
        if self._procs != 1:
            step_etree.attrib["procs"] = str(self._procs)
        if self._do_log_file != None:
            step_etree.attrib["do_log_file"] = str(self._do_log_file)
        for use in self._use:
            use_etree = ET.SubElement(step_etree, "use")
            use_etree.text = jube2.conf.DEFAULT_SEPARATOR.join(use)
        for operation in self._operations:
            step_etree.append(operation.etree_repr())
        return step_etree

    def __repr__(self):
        return "{0}".format(vars(self))

    def add_operation(self, operation):
        """Add operation"""
        self._operations.append(operation)

    def add_uses(self, use_names):
        """Add use"""
        for use_name in use_names:
            if any([use_name in use_list for use_list in self._use]):
                raise ValueError(("Element \"{0}\" can only be used once")
                                 .format(use_name))
        self._use.append(use_names)

    @property
    def name(self):
        """Return step name"""
        return self._name

    @property
    def active(self):
        """Return active state"""
        return self._active

    @property
    def export(self):
        """Return export behaviour"""
        return self._export

    @property
    def iterations(self):
        """Return iterations"""
        return self._iterations

    @property
    def cycles(self):
        """Return number of cycles"""
        return self._cycles

    @property
    def procs(self):
        """Return number of procs"""
        return self._procs

    @property
    def shared_link_name(self):
        """Return shared link name"""
        return self._shared_name

    @property
    def max_wps(self):
        """Return maximum number of simultaneous workpackages"""
        return self._max_wps

    @property
    def do_log_file(self):
        """Return do log file name"""
        return self._do_log_file

    def get_used_sets(self, available_sets, parameter_dict=None):
        """Get list of all used sets, which can be found in available_sets"""
        set_names = list()
        if parameter_dict is None:
            parameter_dict = dict()
        for use in self._use:
            for name in use:
                name = jube2.util.util.substitution(name, parameter_dict)
                if (name in available_sets) and (name not in set_names):
                    set_names.append(name)
        return set_names

    def shared_folder_path(self, benchdir, parameter_dict=None):
        """Return shared folder name"""
        if self._shared_name is not None:
            if parameter_dict is not None:
                shared_name = jube2.util.util.substitution(self._shared_name,
                                                           parameter_dict)
            else:
                shared_name = self._shared_name
            return os.path.join(benchdir,
                                "{0}_{1}".format(self._name, shared_name))
        else:
            return ""

    def get_jube_parameterset(self):
        """Return parameterset which contains step related
        information"""
        parameterset = jube2.parameter.Parameterset()

        # step name
        parameterset.add_parameter(
            jube2.parameter.Parameter.
            create_parameter("jube_step_name", self._name,
                             update_mode=jube2.parameter.JUBE_MODE))

        # iterations
        parameterset.add_parameter(
            jube2.parameter.Parameter.
            create_parameter("jube_step_iterations", str(self._iterations),
                             parameter_type="int",
                             update_mode=jube2.parameter.JUBE_MODE))

        # cycles
        parameterset.add_parameter(
            jube2.parameter.Parameter.
            create_parameter("jube_step_cycles", str(self._cycles),
                             parameter_type="int",
                             update_mode=jube2.parameter.JUBE_MODE))

        # default worpackage cycle, will be overwritten by specific worpackage
        # cycle
        parameterset.add_parameter(
            jube2.parameter.Parameter.
            create_parameter("jube_wp_cycle", "0", parameter_type="int",
                             update_mode=jube2.parameter.JUBE_MODE))

        return parameterset

    def create_workpackages(self, benchmark, global_parameterset,
                            local_parameterset=None, used_sets=None,
                            iteration_base=0, parents=None,
                            incompatible_parameters=None):
        """Create workpackages for current step using given
        benchmark context"""
        if used_sets is None:
            used_sets = set()

        update_parameters = jube2.parameter.Parameterset()
        if local_parameterset is None:
            local_parameterset = jube2.parameter.Parameterset()
            global_parameterset.add_parameterset(
                benchmark.get_jube_parameterset())
            global_parameterset.add_parameterset(self.get_jube_parameterset())
            update_parameters.add_parameterset(
                global_parameterset.get_updatable_parameter(
                    jube2.parameter.STEP_MODE))
            for parameter in update_parameters:
                incompatible_parameters.discard(parameter.name)

        if parents is None:
            parents = list()

        new_workpackages = list()

        # Create parameter dictionary for substitution
        parameter_dict = \
            dict([[par.name, par.value] for par in
                  global_parameterset.constant_parameter_dict.values()])

        # Filter for parametersets in uses
        parameterset_names = \
            set(self.get_used_sets(benchmark.parametersets, parameter_dict))
        new_sets_found = len(parameterset_names.difference(used_sets)) > 0

        if new_sets_found:
            parameterset_names = parameterset_names.difference(used_sets)
            used_sets = used_sets.union(parameterset_names)

            for parameterset_name in parameterset_names:
                # The parametersets in a single step must be compatible
                if not local_parameterset.is_compatible(
                        benchmark.parametersets[parameterset_name]):
                    incompatible_names = \
                        local_parameterset.get_incompatible_parameter(
                            benchmark.parametersets[parameterset_name])
                    raise ValueError(("Cannot use parameterset '{0}' in " +
                                      "step '{1}'.\nParameter '{2}' is/are " +
                                      "already defined by a different " +
                                      "parameterset.")
                                     .format(parameterset_name, self.name,
                                             ",".join(incompatible_names)))
                local_parameterset.add_parameterset(
                    benchmark.parametersets[parameterset_name])

            # Combine local and history parameterset
            if local_parameterset.is_compatible(
                    global_parameterset, update_mode=jube2.parameter.USE_MODE):
                update_parameters.add_parameterset(
                    local_parameterset.get_updatable_parameter(
                        jube2.parameter.USE_MODE))
                for parameter in update_parameters:
                    incompatible_parameters.discard(parameter.name)
                global_parameterset = \
                    local_parameterset.copy().add_parameterset(
                        global_parameterset)
            else:
                incompatible_names = \
                    local_parameterset.get_incompatible_parameter(
                        global_parameterset,
                        update_mode=jube2.parameter.USE_MODE)
                LOGGER.debug("Incompatible parameterset combination found " +
                             "between current and parent steps. \nParameter " +
                             "'{0}' is/are already defined different.".format(
                                 ",".join(incompatible_names)))
                return new_workpackages

        # update parameters
        global_parameterset.update_parameterset(update_parameters)

        # Set tag-mode evaluation helper function to allow access to tag list
        # during paramter evaluation
        for parameter in global_parameterset.all_parameters:
            if parameter.mode == "tag":
                parameter.eval_helper = \
                    lambda tag: tag if tag in benchmark.tags else ""

        # Expand templates
        parametersets = [global_parameterset]
        change = True
        while change:
            change = False
            new_parametersets = list()
            for parameterset in parametersets:
                parameterset.parameter_substitution()
                # Maybe new templates were created
                if parameterset.has_templates:
                    LOGGER.debug("Expand parameter templates:\n{0}".format(
                        "\n".join("    \"{0}\": {1}".format(i, j.value)
                                  for i, j in parameterset.
                                  template_parameter_dict.items())))
                    new_parametersets += \
                        [new_parameterset for new_parameterset in
                         parameterset.expand_templates()]
                    change = True
                else:
                    new_parametersets += [parameterset]
            parametersets = new_parametersets

        # Create workpackages
        for parameterset in parametersets:
            workpackage_parameterset = local_parameterset.copy()
            workpackage_parameterset.update_parameterset(parameterset)
            if new_sets_found:
                new_workpackages += \
                    self.create_workpackages(benchmark, parameterset,
                                             workpackage_parameterset,
                                             used_sets, iteration_base,
                                             parents,
                                             incompatible_parameters.copy())
            else:
                # Check if all incompatible_parameters were updated
                if len(incompatible_parameters) > 0:
                    return new_workpackages
                # Create new workpackage
                created_workpackages = list()
                for iteration in range(self.iterations):
                    workpackage = jube2.workpackage.Workpackage(
                        benchmark=benchmark,
                        step=self,
                        parameterset=parameterset.copy(),
                        local_parameter_names=[
                            par.name for par in workpackage_parameterset],
                        iteration=iteration_base * self.iterations + iteration,
                        cycle=0)

                    # --- Link parent workpackages ---
                    for parent in parents:
                        workpackage.add_parent(parent)

                    # --- Add workpackage JUBE parameterset ---
                    workpackage.parameterset.add_parameterset(
                        workpackage.get_jube_parameterset())

                    # --- Final parameter substitution ---
                    workpackage.parameterset.parameter_substitution(
                        final_sub=True)

                    # --- Check parameter type ---
                    for parameter in workpackage.parameterset:
                        if not parameter.is_template:
                            jube2.util.util.convert_type(
                                parameter.parameter_type, parameter.value)

                    # --- Enable workpackage dir cache ---
                    workpackage.allow_workpackage_dir_caching()

                    if workpackage.active:
                        created_workpackages.append(workpackage)
                    else:
                        jube2.workpackage.Workpackage.\
                            reduce_workpackage_id_counter()

                for workpackage in created_workpackages:
                    workpackage.iteration_siblings.update(
                        set(created_workpackages))

                new_workpackages += created_workpackages

        return new_workpackages

    @property
    def alt_work_dir(self):
        """Return alternativ work directory"""
        return self._alt_work_dir

    @property
    def use(self):
        """Return parameters and substitutions"""
        return self._use

    @property
    def suffix(self):
        """Return directory suffix"""
        return self._suffix

    @property
    def operations(self):
        """Return operations"""
        return self._operations

    @property
    def depend(self):
        """Return dependencies"""
        return self._depend

    def get_depend_history(self, benchmark):
        """Creates a set of all dependent steps in history for given
        benchmark"""
        depend_history = set()
        for step_name in self._depend:
            if step_name not in depend_history:
                depend_history.add(step_name)
                depend_history.update(
                    benchmark.steps[step_name].get_depend_history(benchmark))
        return depend_history


class Operation(object):

    """The Operation-class represents a single instruction, which will be
    executed in a shell environment.
    """

    def __init__(self, do, async_filename=None, stdout_filename=None,
                 stderr_filename=None, active="true", shared=False,
                 work_dir=None, break_filename=None, error_filename=None):
        self._do = do
        self._error_filename = error_filename
        self._async_filename = async_filename
        self._break_filename = break_filename
        self._stdout_filename = stdout_filename
        self._stderr_filename = stderr_filename
        self._active = active
        self._shared = shared
        self._work_dir = work_dir

    @property
    def stdout_filename(self):
        """Get stdout filename"""
        return self._stdout_filename

    @property
    def stderr_filename(self):
        """Get stderr filename"""
        return self._stderr_filename

    @property
    def error_filename(self):
        """Get error filename"""
        return self._error_filename

    @property
    def async_filename(self):
        """Get async filename"""
        return self._async_filename

    @property
    def shared(self):
        """Shared operation?"""
        return self._shared

    def active(self, parameter_dict):
        """Return active status of the current operation depending on the
        given parameter_dict"""
        active_str = jube2.util.util.substitution(self._active, parameter_dict)
        return jube2.util.util.eval_bool(active_str)

    def execute(self, parameter_dict, work_dir, only_check_pending=False,
                environment=None, pid=None, dolog=None):
        """Execute the operation. work_dir must be set to the given context
        path. The parameter_dict used for inline substitution.
        If only_check_pending is set to True, the operation will not be
        executed, only the async_file will be checked.
        Return operation status:
        True => operation finished
        False => operation pending
        """
        if not self.active(parameter_dict):
            return True

        if environment is not None:
            env = environment
        else:
            env = os.environ

        if not only_check_pending:
            # Inline substitution
            do = jube2.util.util.substitution(self._do, parameter_dict)

            # Remove leading and trailing ; because otherwise ;; will cause
            # trouble when adding ; env
            do = do.strip(";")

            if (not jube2.conf.DEBUG_MODE) and (do.strip() != ""):
                # Change stdout
                if self._stdout_filename is not None:
                    stdout_filename = jube2.util.util.substitution(
                        self._stdout_filename, parameter_dict)
                    stdout_filename = \
                        os.path.expandvars(os.path.expanduser(stdout_filename))
                else:
                    stdout_filename = "stdout"
                stdout_path = os.path.join(work_dir, stdout_filename)
                stdout = open(stdout_path, "a")

                # Change stderr
                if self._stderr_filename is not None:
                    stderr_filename = jube2.util.util.substitution(
                        self._stderr_filename, parameter_dict)
                    stderr_filename = \
                        os.path.expandvars(os.path.expanduser(stderr_filename))
                else:
                    stderr_filename = "stderr"
                stderr_path = os.path.join(work_dir, stderr_filename)
                stderr = open(stderr_path, "a")

        # Use operation specific work directory
        if self._work_dir is not None and len(self._work_dir) > 0:
            new_work_dir = jube2.util.util.substitution(
                self._work_dir, parameter_dict)
            new_work_dir = os.path.expandvars(os.path.expanduser(new_work_dir))
            work_dir = os.path.join(work_dir, new_work_dir)
            if re.search(jube2.parameter.Parameter.parameter_regex, work_dir):
                raise IOError(("Given work directory {0} contains a unknown " +
                               "JUBE or environment variable.").format(
                    work_dir))

            # Create directory if it does not exist
            if not jube2.conf.DEBUG_MODE and not os.path.exists(work_dir):
                try:
                    os.makedirs(work_dir)
                except FileExistsError:
                    pass

        if not only_check_pending:

            if pid is not None:
                env_file_name = jube2.conf.ENVIRONMENT_INFO.replace(
                    '.', '_{}.'.format(pid))
            else:
                env_file_name = jube2.conf.ENVIRONMENT_INFO
            abs_info_file_path = \
                os.path.abspath(os.path.join(work_dir, env_file_name))

            # Select unix shell
            shell = jube2.conf.STANDARD_SHELL
            if "JUBE_EXEC_SHELL" in os.environ:
                alt_shell = os.environ["JUBE_EXEC_SHELL"].strip()
                if len(alt_shell) > 0:
                    shell = alt_shell

            # Execute "do"
            LOGGER.debug(">>> {0}".format(do))
            if (not jube2.conf.DEBUG_MODE) and (do != ""):
                LOGGER.debug("    stdout: {0}".format(
                    os.path.abspath(stdout_path)))
                LOGGER.debug("    stderr: {0}".format(
                    os.path.abspath(stderr_path)))
                try:
                    if jube2.conf.VERBOSE_LEVEL > 1:
                        stdout_handle = subprocess.PIPE
                    else:
                        stdout_handle = stdout

                    if dolog != None:
                        dolog.store_do(do=do, shell=shell, work_dir=os.path.abspath(
                            work_dir), parameter_dict=parameter_dict, shared=self.shared)

                    sub = subprocess.Popen(
                        [shell, "-c",
                         "{0} && env > \"{1}\"".format(do,
                                                       abs_info_file_path)],
                        cwd=work_dir, stdout=stdout_handle,
                        stderr=stderr, shell=False,
                        env=env)
                except OSError:
                    stdout.close()
                    stderr.close()
                    raise RuntimeError(("Error (returncode <> 0) while " +
                                        "running \"{0}\" in " +
                                        "directory \"{1}\"")
                                       .format(do, os.path.abspath(work_dir)))

                # stdout verbose output
                if jube2.conf.VERBOSE_LEVEL > 1:
                    while True:
                        read_out = sub.stdout.read(
                            jube2.conf.VERBOSE_STDOUT_READ_CHUNK_SIZE)
                        if (not read_out):
                            break
                        else:
                            try:
                                print(read_out.decode(errors="ignore"), end="")
                            except TypeError:
                                print(read_out.decode("utf-8", "ignore"),
                                      end="")
                            try:
                                stdout.write(read_out)
                            except TypeError:
                                try:
                                    stdout.write(read_out.decode(
                                        errors="ignore"))
                                except TypeError:
                                    stdout.write(read_out.decode("utf-8",
                                                                 "ignore"))
                            time.sleep(jube2.conf.VERBOSE_STDOUT_POLL_SLEEP)
                    sub.communicate()

                returncode = sub.wait()

                # Close filehandles
                stdout.close()
                stderr.close()

                env = Operation.read_process_environment(work_dir, pid=pid)

                # Read and store new environment
                if (environment is not None) and (returncode == 0):
                    environment.clear()
                    environment.update(env)

                if returncode != 0:
                    if os.path.isfile(stderr_path):
                        stderr = open(stderr_path, "r")
                        stderr_msg = stderr.readlines()
                        stderr.close()
                    else:
                        stderr_msg = ""
                    try:
                        raise RuntimeError(
                            ("Error (returncode <> 0) while running \"{0}\" " +
                             "in directory \"{1}\"\nMessage in \"{2}\":" +
                             "{3}\n{4}").format(
                                do,
                                os.path.abspath(work_dir),
                                os.path.abspath(stderr_path),
                                "\n..." if len(stderr_msg) >
                                jube2.conf.ERROR_MSG_LINES else "",
                                "\n".join(stderr_msg[
                                    -jube2.conf.ERROR_MSG_LINES:])))
                    except UnicodeDecodeError:
                        raise RuntimeError(
                            ("Error (returncode <> 0) while running \"{0}\" " +
                             "in directory \"{1}\"").format(
                                do,
                                os.path.abspath(work_dir)))

        continue_op = True
        continue_cycle = True

        # Check if further execution was skipped
        if self._break_filename is not None:
            break_filename = jube2.util.util.substitution(
                self._break_filename, parameter_dict)
            break_filename = \
                os.path.expandvars(os.path.expanduser(break_filename))
            if os.path.exists(os.path.join(work_dir, break_filename)):
                LOGGER.debug(("\"{0}\" was found, workpackage execution and "
                              " further loop continuation was stopped.")
                             .format(break_filename))
                continue_cycle = False

        # Waiting to continue
        if self._async_filename is not None:
            async_filename = jube2.util.util.substitution(
                self._async_filename, parameter_dict)
            async_filename = \
                os.path.expandvars(os.path.expanduser(async_filename))
            if not os.path.exists(os.path.join(work_dir, async_filename)):
                LOGGER.debug("Waiting for file \"{0}\" ..."
                             .format(async_filename))
                if jube2.conf.DEBUG_MODE:
                    LOGGER.debug("  skip waiting")
                else:
                    continue_op = False

        # Search for error file
        if self._error_filename is not None:
            error_filename = jube2.util.util.substitution(
                self._error_filename, parameter_dict)
            error_filename = \
                os.path.expandvars(os.path.expanduser(error_filename))
            if os.path.exists(os.path.join(work_dir, error_filename)):
                LOGGER.debug("Checking for error file \"{0}\" ..."
                             .format(error_filename))
                if jube2.conf.DEBUG_MODE:
                    LOGGER.debug("  skip error")
                else:
                    do = jube2.util.util.substitution(self._do, parameter_dict)
                    raise(RuntimeError(("Error file \"{0}\" found after " +
                                        "running the command \"{1}\".").format(
                                            error_filename, do)))

        return continue_op, continue_cycle

    def etree_repr(self):
        """Return etree object representation"""
        do_etree = ET.Element("do")
        do_etree.text = self._do
        if self._async_filename is not None:
            do_etree.attrib["done_file"] = self._async_filename
        if self._error_filename is not None:
            do_etree.attrib["error_file"] = self._error_filename
        if self._break_filename is not None:
            do_etree.attrib["break_file"] = self._break_filename
        if self._stdout_filename is not None:
            do_etree.attrib["stdout"] = self._stdout_filename
        if self._stderr_filename is not None:
            do_etree.attrib["stderr"] = self._stderr_filename
        if self._active != "true":
            do_etree.attrib["active"] = self._active
        if self._shared:
            do_etree.attrib["shared"] = "true"
        if self._work_dir is not None:
            do_etree.attrib["work_dir"] = self._work_dir
        return do_etree

    def __repr__(self):
        return self._do

    @staticmethod
    def read_process_environment(work_dir, remove_after_read=True, pid=None):
        """Read standard environment info file in given directory."""
        env = dict()
        last = None
        if pid is not None:
            env_file_name = jube2.conf.ENVIRONMENT_INFO.replace(
                '.', '_{}.'.format(pid))
        else:
            env_file_name = jube2.conf.ENVIRONMENT_INFO
        env_file_path = os.path.join(work_dir, env_file_name)
        if os.path.isfile(env_file_path):
            env_file = open(env_file_path, "r")
            for line in env_file:
                line = line.rstrip()
                matcher = re.match(r"^(\S.*?)=(.*?)$", line)
                if matcher:
                    env[matcher.group(1)] = matcher.group(2)
                    last = matcher.group(1)
                elif last is not None:
                    env[last] += "\n" + line
            env_file.close()
            if remove_after_read:
                os.remove(env_file_path)
        return env


class DoLog(object):

    """A DoLog class containing the operations and information for setting up the do log."""

    def __init__(self, log_dir, log_file, initial_env, cycle=0):
        self._log_dir = log_dir
        if log_file != None:
            if log_file[-1] == '/':
                raise ValueError(
                    "The path of do_log_file is ending with / which is a invalid file path.")
        self._log_file = log_file
        self._initial_env = initial_env
        self._work_dir = None
        self._cycle = cycle
        self._log_path = None

    @property
    def log_path(self):
        """Get log directory"""
        return self._log_path

    @property
    def log_file(self):
        """Get log file"""
        return self._log_file

    @property
    def log_path(self):
        """Get log path"""
        return self._log_path

    @property
    def work_dir(self):
        """Get last work directory"""
        return self._work_dir

    @property
    def initial_env(self):
        """Get initial env"""
        return self._initial_env

    def initialiseFile(self, shell):
        """Initialise file if not yet existent."""
        fdologout = open(self.log_path, 'a')
        fdologout.write('#!'+shell+'\n\n')
        for envVarName, envVarValue in self.initial_env.items():
            fdologout.write('set '+envVarName+"='" +
                            envVarValue.replace('\n', '\\n')+"'\n")
        fdologout.write('\n')
        fdologout.close()

    def store_do(self, do, shell, work_dir, parameter_dict=None, shared=False):
        """Store the current execution directive to the do log and set up the environment if file does not yet exist."""
        if self._log_file == None:
            return

        if self._log_path == None:
            if parameter_dict:
                new_log_file = jube2.util.util.substitution(
                    self._log_file, parameter_dict)
                new_log_file = os.path.expandvars(
                    os.path.expanduser(new_log_file))
                self._log_file = new_log_file
                if re.search(jube2.parameter.Parameter.parameter_regex, self._log_file):
                    raise IOError(("Given do_log_file path {0} contains a unknown " +
                                   "JUBE or environment variable.").format(
                        self._log_file))

            if self._log_file[0] == '/':
                self._log_path = self._log_file
            elif '/' not in self._log_file:
                self._log_path = os.path.join(self._log_dir, self._log_file)
            else:
                self._log_path = os.path.join(os.getcwd(), self._log_file)

        # create directory if not yet existent
        if not os.path.exists(os.path.dirname(self.log_path)):
            os.makedirs(os.path.dirname(self.log_path))

        if not os.path.exists(self.log_path):
            self.initialiseFile(shell)

        fdologout = open(self.log_path, 'a')
        if work_dir != self.work_dir:
            fdologout.write('cd '+work_dir+'\n')
            self._work_dir = work_dir
        fdologout.write(do)
        if shared:
            fdologout.write(' # shared execution')
        fdologout.write('\n')
        fdologout.close()
