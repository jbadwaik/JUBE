.. # JUBE Benchmarking Environment
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

.. index:: release notes

Release notes
=============

Version 2.5.1
=============
Release: 2022-08-24

* The default behaviour of replacing two parameters with different options without throwing an error was restored.
* The testing suite was extended.
* The schema files were corrected such that they contain the duplicate option.

Version 2.5.0
=============
Release: 2022-08-22

* Several independent workpackages within a step can be executed by multiple processes in parallel by stating `procs=#number_of_parallel_processes#` within the `step` tag. An example and a documentation entry was added.
* A result database can be produced by use of the `database` tag. An example and a documentation entry was added.
* `python2`-support was removed.
* A couple of unittests were added which now include the testing of most of the examples.
* Sample `run.log` of most examples were added to `tests/examples_output`.
* Some yaml example scripts were corrected.
* The MANIFEST file was removed.
* A typo in the error message was fixed.
* Fix result command documentation.
* A wrong result entry in the glossary was fixed.
* A bug for the usage of a newline separator within yaml scripts is resolved.
* A feature to create a do_log file for every workpackage of a step is integrated. The do_log file contains the whole environment while execution, the execution shell, the change of current work directories, comments if a directive was executed in a shared fashion and the do directives of the steps.
* The execution cancels now, when a parameter is of type int or float and the parameter value has not the form of a int or float correspondingly.
* The FAQ documentation was extended with yaml examples.
* The option duplicate for parametersets and parameters was introduced.

Version 2.4.3
~~~~~~~~~~~~~
Release: 2022-07-20

* Fixes a bug related to `<include>` and `init-with` combinations.
* `JUBE_EXEC_SHELL` is now also taken into account during parameter evaluation.
* `jube status` now also returns `ERROR` state.
* Fixes a bug of using `$$` in shell commands.
* Updates *SLURM* `gres` default value in platform files.
* Fixes a bug of having a list of benchmarks in YAML format.

Version 2.4.2
~~~~~~~~~~~~~
Release: 2021-11-30

* JUBE will raise an error if an changed `work_dir` contains unknown variables.
* A bug was solved which enabled `dotall="true"` by default for all pattern, which can make those costly to evaluate.
* Fixes a bug in result data processing.
* Fixes a bug in YAML input format if `benchmark` key is not used.
* A empty value in YAML input format will now be treated liek an empty String not as a `None` value.
* Avoid crash due to overflow error for huge pattern values.
* Fixes a bug, which blocked `include` blocks to include other `include` blocks.
* `setup.py` now moves all additional non-code data to `.../share/jube`, which allows better utilization of `pip` based installation

Version 2.4.1
~~~~~~~~~~~~~
Release: 2021-02-09

* A bug was solved, if a benchmark used the older `,`-separated `tag=` format in contrast to the new layout introduced in *version 2.2.2*.
* A warning message in context of newer *YAML* versions was removed.
* A Python3 problem inside the *YAML* parser was solved.
* A bug was solved, which was raised if the benchmark was started on a different filesystem then the one which was configured within `outpath`.
* The `jube` base script within `bin` will now use `python3` by default. This is necessary as many newer systems does not have a "standard" `python`
  defined by default. In addition the additional script `jube-python2` is now available, which utilizes `python2`. 
  So far Python 2 is still fully supported but can be seen deprecated and future versions of *JUBE* might break 
  the Python 2 backwards compatibility.
* All `style=pretty` tables in *JUBE* will now use a markdown like format to allow easier integration within other tools.

Version 2.4.0
~~~~~~~~~~~~~
Release: 2020-07-03

* New *YAML* based *JUBE* input format. The existing *XML* format still stays available. Both
  formats cover the same amount of features. If you plan to use *YAML* based *JUBE* input files, you have to 
  add the `pyyaml-module <https://pyyaml.org>`_ to your *Python* module library. See also :ref:`input_format`
* New ``<do>`` attribute: ``error_file="..."``. In contrast to the existing ``done_file`` this file handle can be used to mark
  a broken asynchronous execution (the job templates in the ``platform`` folder were updated accordingly)
* The ``analyse`` step is now automatically called when a result is shown and if it was not executed before (instead of showing an error message).
* New option ``--workpackage`` for ``remove`` command line sub command. Allows to remove an individual 
  workpackage from a benchmark. See also: :ref:`restart_workpackage`
* New ``table`` output format: ``aligned``

Version 2.3.0
~~~~~~~~~~~~~
Release: 2019-11-07

* New command line option ``-s {pretty,csv}, --style {pretty,csv}`` for the ``result`` command
  allows to overwrite the selected table style
* New command line option ``-o OUTPATH, --outpath OUTPATH`` for the ``run`` command allows
  to overwrite the selected outpath for the benchmark run
* New parameter modes: ``env`` and ``tag``

  * ``mode="env``: include the content of an available environment variable
  * ``mode="tag``: include the tag name if the tag was set during execution, otherwise the content is empty

* New option ``dotall=true`` in ``<pattern>`` (default: ``false``) allows that ``.`` within a
  regular expression also matches newline characters. This can be very helpfull to extract a
  line only after a specific header was mentioned. See :ref:`extract_specifc_block`
* ``--tags`` used in combination with the ``--update`` option will now be added to the existing
  tags of the original run instead of overwriting the old tags. If no new tags need to be added within an update ``--tags`` can now be skipped.
* ``parse.log`` is now automatically moved into the specifc job run folder and is also available 
  within the ``jube log`` command


Version 2.2.2
~~~~~~~~~~~~~
Release: 2019-02-04

* New ``tag`` handling: Tags can now be mixed by using boolean operations (``+`` for and, ``|`` for or), brackets are allowed as well.
  Old ``,`` separated lists of tags are automatically converted. See :ref:`tagging`
* Extend parameter update documentation. See :ref:`parameter_update_mode`
* Platform files were renamed (system specific to queuing system specific)
* Fix ``$jube_wp_relpath`` and ``$jube_wp_abspath`` if *JUBE* is executed from a relative directory
* Fixed missing or wrong environment variable evaluation within *JUBE* parameters
* Fix for derived pattern handling if no match for regular pattern was found
* Fix default value handling for derived pattern
* Fix unicode decoding problems for environment variables

Version 2.2.1
~~~~~~~~~~~~~
Release: 2018-06-22

* Allow separator selection when using the ``jube info ... -c`` option
* Fix internal handling if a script parameter or a template is evaluated to an empty value
* Fix for different Python3 parsing conflicts

Version 2.2.0
~~~~~~~~~~~~~
Release: 2017-12-21

* New feature: step cycles. See :ref:`step_cycle`
* New parameter ``update_mode``. See :ref:`parameter_update_mode`
* Result creation by scanning multiple steps now automatically creates a combined output
* Speed up of the *JUBE* internal management if a large number of work packages is used
* *JUBE* 1 conversion tool is not available any more
* New general commandline option ``--strict`` stops *JUBE* if there is a version mismatch
* Broken analysis files will now be ignored
* Fix combination of ``active`` and ``shared``
* Fix sorting problem for multiple result columns
* Fix parameter problem, if the continue command is used and the parameter holds a value having multiple lines

Version 2.1.4
~~~~~~~~~~~~~
Release: 2016-12-20

* ``--id`` indices on the commandline can now be negative to count from the end of the available benchmarks
* *JUBE* now allows a basic auto completion mechanism if using *BASH*. To activate: ``eval "$(jube complete)"``
* Fix result sorting bug in Python3
* New ``jube_benchmark_rundir`` variable which holds the top level *JUBE* directory (the absolute ``outpath`` directory)
* Fix CSV output format, if parameter contain linebreaks.
* ``active`` attribute can now be used in ``<prepare>``, ``<copy>`` and ``<link>``
* New FAQ entry concerning multiple file analysis: :doc:`faq`
* ``<parameter>`` using ``mode="shell"`` or ``mode="perl"`` will now stop program execution if an error occurs
  (similar to ``mode="python"``)
* ``<do>`` specfic ``work_dir`` is now created automatically if needed
* ``directory`` attribute in ``<link>`` and ``<copy>`` was renamed to ``source_dir`` (old attribute name is still possible)

  * ``source_dir`` now allows parameter substitution

* New attribute ``target_dir`` in ``<link>`` and ``<copy>`` to specify the target directory path prefix


Version 2.1.3
~~~~~~~~~~~~~
Release: 2016-09-01

* Fix broken CSV table output style
* Fix ``jube_wp_...`` parameter handling bug, if these parameter are used inside another script parameter
* Added new optional argument ``suffix="..."`` to the ``<step>`` tag

  * Parameter are allowed inside this argument string.
  * The evaluated string will be attached to the default workpackage directory name to allow users to find specific directories in an easier way (e.g. ``000001_stepname_suffix`` ).

* The *XML* schema files can now be found inside the ``contrib`` folder
* Added new advanced error handling

  * JUBE will not stop any more if an error occurs inside a ``run`` or ``continue``. The error will be marked and the corresponding workpackage will not be touched anymore.
  * There is also a ``-e``/``--exit`` option to overwrite this behaviour to directly exit if there is an error.


Version 2.1.2
~~~~~~~~~~~~~
Release: 2016-07-29

* The internal parameter handling is much faster now, especially if a large number of parameter is used within the same step.
* Fix critical bug when storing environment variables. Environment variables wasn't read correctly inside a step if this step was only executed after
  a ``jube continue`` run.
* Fix bug inside a ``<sub>`` if it contains any linebreak
* Quotes are added automatically inside the ``$jube_wp_envstr`` variable to support spaces in the environment variable argument list
* Combining ``-u`` and ``tags`` in a ``jube result`` run will not filter the result branches anymore
* Allow lowercase ``false`` in bool expressions (e.g. the ``active`` option)
* Fix bug when using *JUBE* in a *Python3.x* environment
* The ``jube help`` output was restructed to display separate key columns instead of a keyword list
* ``<pattern>`` can now contain a ``default=...`` attribute which set their default value if the pattern can't be found or if it can't be evaluated
* ``null_value=...`` was removed from the ``<column>`` and ``<key>``-tag because the new default attribute matches its behaviour
* Added first *JUBE* FAQ entries to the documentation: :doc:`faq`
* New ``active``-attribute inside a ``<step>``-tag. The attribute enables or disables the corresponding step (and all following steps). It can contain any 
  bool expression and available parameter.
* Fix bug in ``<link>`` handling if an alternative link name is used which points to a sub directory
* Added new option ``-c / --csv-parametrization`` to ``jube info`` command to show a workpackage specfic parametrisation
  by using the CSV format (similar to the existing ``-p`` option)
* Allow Shell expansion in ``<link>`` tags. ``<link>`` now also support the ``*``
* Restructure internal ``<copy>`` and ``<link>`` handling
* All example platform files were updated an simplified


Version 2.1.1
~~~~~~~~~~~~~
Release: 2016-04-14

* *JUBE* will now show only the latest benchmark result by default, ``--id all`` must be used to see all results
* Bool expressions can now be used directly in the ``<do active="">`` attribute
* Added ``filter`` attribute in ``<table>`` and ``<syslog>`` to show only specifix result entries (based on a bool expression)
* New ``<parameter>`` and ``<pattern>`` mode: ``mode="shell"``
* Allow multiline output in result tables
* Fix wrong group handling if ``JUBE_GROUP_NAME`` is used
* Scripting parameter (e.g. ``mode="python"``) can now handle $ to allow access to environment variables
* Fix $$ bug ($$ were ignored when used within a parameter)
* Fix ``$jube_wp_parent_..._id`` bug if ``$jube_wp_parent_..._id`` is used within another parameter
* Fix bug in std calculation when creating statistical result values
* Fix bug if tags are used within ``<include>``


Version 2.1.0
~~~~~~~~~~~~~
Release: 2015-11-10

* Fix slow verbose mode
* Fix empty debug output file
* Fix broken command line ``--include-path`` option
* Allow recursive ``<include-path>`` and ``<selection>`` handling (additional include-paths
  can now be included by using the ``<include>`` tag)
* Allow multiple ``<selection>`` and ``<include-path>`` areas
* New ``transpose="true"`` attribute possible in ``<table>``
* Allow recursive parameter name creation in ``<do>`` or ``<sub>`` (e.g. ``${param${num}}``)
* Extend iteration feature

  * ``iteration=#number`` can be used in the ``<step>`` tag, the work package will be executed #number times
  * New ``reduce`` attribute in analyser, possible values: ``true`` or ``false`` (default: ``true``)

    * ``true``: use a single result line to combine all iterations
    * ``false``: each iteration will get its separate result line

* Fix pattern_cnt bug
* New pattern suffix: ``_std`` (standard deviation)
* ``reduce`` option in ``<pattern>`` not needed anymore (all possible reduce options are now calculated automatically)
* Fix jube-autorun and add progress check interval
* Added ``--force`` command line option to skip *JUBE* version check
* Added optional ``out_mode`` attribute in ``<iofile>``. It can be ``a`` or ``w`` to allow appending or overwriting
  an existing ``out``-file (default: ``w``).
* New version numbering model to divide between feature and bugfix releases

Version 2.0.7
~~~~~~~~~~~~~
Release: 2015-09-17

* *JUBE* will ignore folders in the benchmark directory which does not contain a ``configuration.xml``
* New pattern reduce example :ref:`statistic_values`
* New internal directory handling to allow more flexible feature addition
* New internal result structure
* Fix derived pattern bug when scanning multiple result files
* *JUBE* version number will now be stored inside the ``configuration.xml``
* *JUBE* version number will be checked when loading an existing benchmark run
* New *JUBE* variable: ``$jube_wp_relpath`` (contains relative workpackage path)
* Add Verbose-Mode ``-v`` / ``--verbose``

  * Enable verbose console output ``jube -v run ...``
  * Show stdout during execution: ``-vv``
  * Show log and stdout during execution: ``-vvv``

* Change version mode to ``-V`` / ``--version``
* ``jube_parse.log`` will now be created next to the ``<input_config>.xml`` file
* New syslog result type (thanks to Andy Georges for contribution), see :term:`syslog_tag`
* New environment variable ``JUBE_GROUP_NAME``: By setting and exporting ``JUBE_GROUP_NAME`` to an
  available UNIX group, *JUBE* will create benchmark directory structures which can be accessed
  by the given group.
* Benchmark results can now be created also by user without write-access to the benchmark directory
* Parametersets are now available within each dependent step. There is no need to reuse them anymore.

Version 2.0.6
~~~~~~~~~~~~~
Release: 2015-06-16

* users can now change the *JUBE* standard Shell (``/bin/sh``) by using the new environment variable ``JUBE_EXEC_SHELL``, see :ref:`configuration`
* fixes a bug if a Shell filename completion results to a single file name (inside the ``<copy>``-tag)
* fixes stderr reading bug if ``work_dir`` was changed in a specific ``<do>``
* changes include path order, new order: commandline (``--include-path ...``), config file (``<include-path>``), Shell var (``JUBE_INCLUDE_PATH``), ``.``
* fixes some unicode issues
* units in the result dataset will now be shown correctly if a file specific patternset is used

Version 2.0.5
~~~~~~~~~~~~~
Release: 2015-04-09

* ``argparse`` is now marked as a dependency in ``setup.py``. It will be automatically loaded when using *setuptools*.
* tags will now also be used when including external sets by using ``<use from="...">``
* change default platform output filenames: using *job.out* and *job.err* instead of *stdout* and *stderr* for default job output
* new internal workflow generation alogrithm
* parameter can now be used in step ``<use>``, e.g. ``<use>set_$number</use>``

  * external sets had to be given by name to allow later substitution: ``<use from="file:set1:set2">set$nr</use>``
  * also multiple files can be mixed: ``<use from="file:set1,file2:set2">set$nr</use>``
  * new example :ref:`parameter-dependencies`

* allow ``use``-attribute in file-tag to select file specific patternsets ``<file use="patternset">``
* Shell and parameter substitution now allowed in analyse files selection ``<file>*.log</file>``
* default ``stdout`` and ``stderr`` file will now stay in the default directory when changing the work_dir inside a ``<do>``
* start of public available *JUBE* configuration files repository: `<https://github.com/FZJ-JSC/jube-configs>`_

Version 2.0.4
~~~~~~~~~~~~~
Release: 2015-02-23

* fix bug when using *JUBE* in a *Python3.x* environment
* time information (start, last modified) will now be stored in a seperate file and are not extracted out of
  file and directory metadata
* ``jube run`` now allows the ``--id/-i`` command line option to set a specific benchmark id
* ``jube result`` now automatically combines multiple benchmark runs within the same benchmark directory. *JUBE* automatically
  add the benchmark id to the result output (except only a specific benchmark was requested)

  * new command line option: ``--num/-n`` allow to set a maximum number of visible benchmarks in result
  * new command line option: ``--revert/-r`` revert benchmark id order

* new attribute for ``<column>``: ``null_value="..."`` to set a NULL representation for the output table (default: ``""``)
* new command: ``jube update`` checks weather the newest *JUBE* version is installed
* new ``id`` options: ``--id last`` to get the last benchmark and ``--id all`` to get all benchmarks

Version 2.0.3
~~~~~~~~~~~~~
Release: 2015-01-29

* missing files given in a fileset will now raise an error message
* ``jube info <benchmark-dir> --id <id> --step <step_name>`` now also shows
  the current parametrization
* ``jube info <benchmark-dir> --id <id> --step <step_name> -p`` only shows the
  current parametrization using a csv table format
* add new (optional) attribute ``max_async="..."`` to ``<step>``: Maximum number of parallel workpackages
  of the correspondig step will run at the same time (default: 0, means no limitation)
* switch ``<analyzer>`` to ``<analyser>`` (also ``<analyzer>`` will be available) to avoid mixing of "s" and "z" versions
* fix bug when using ``,`` inside of a ``<pattern>``
* *JUBE* now return a none zero error code if it sends an error message
* update platform files to allow easier environment handling: ``<parameter ... export="true">`` will 
  be automatically used inside of the corresponding jobscript
* update platform jobscript templates to keep error code of running program
* fix bug when adding ``;`` at the end of a ``<do>``
* last five lines of stderr message will now be copied to user error message (if shell return code <> 0)
* fix *Python2.6* compatibility bug in converter module
* fix bug when using an evaluable parameter inside of another parameter

Version 2.0.2
~~~~~~~~~~~~~
Release: 2014-12-09

* fix a bug when using ``init-with`` to initialize a ``<copy>``-tag
* use ``cp -p`` behaviour to copy files
* fix error message when using an empty ``<do>``
* added error return code, if there was an error message

Version 2.0.1
~~~~~~~~~~~~~
Release: 2014-11-25

* ``--debug`` option should work now
* fixes problem when including an external ``<prepare>``
* update *Python 2.6* compatibility
* all ``<do>`` within a single ``<step>`` now shares the same environment (including all exported variables)
* a ``<step>`` can export its environment to a dependent ``<step>`` by using the new ``export="true"`` attribute (see new environment handling example)
* update analyse behaviour when scanning multiple files (new ``analyse`` run needed for existing benchmarks)
* in and out substitution files (given by ``<iofile>``) can now be the same
* ``<sub>`` now also supports multiline expressions inside the tag instead of the ``dest``-attribute: ``<sub source="..."></sub>``

Version 2.0.0
~~~~~~~~~~~~~
Release: 2014-11-14

* complete new **Python** kernel
* new input file format
* please see new documentation to get further information
