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

Glossary
========

.. glossary::
   :sorted:

   remove
      The given benchmark will be removed.

      If no benchmark id is given, last benchmark found in directory will be removed.

      Only the *JUBE* internal directory structure will be deleted.
      External files and directories will stay unchanged.

      If no benchmark id is given, last benchmark found in directory will be used. If benchmark directory is missing, current
      directory will be used.

   comment
      Add or manipulate the comment string.

      If no benchmark id is given, last benchmark found in directory will be used. If benchmark directory is missing, current
      directory will be used.

   info
      Show info for the given benchmark directory, a given benchmark or a specific
      step.

      If benchmark directory is missing, current directory will be used.

   log
      Show logs for the given benchmark directory or a given benchmark.

      If no benchmark id is given, last benchmark found in directory will be used. If benchmark directory is missing, current
      directory will be used.

   status
      Show status string (RUNNING or FINISHED) for the given benchmark.

      If no benchmark id is given, last benchmark found in directory will be used. If benchmark directory is missing, current
      directory will be used.

   continue
      Continue an existing benchmark. Not finished steps will be continued,
      if they are leaving pending mode.

      If no benchmark id is given, last benchmark found in directory will be used. If benchmark directory is missing, current
      directory will be used.

   analyse
      Analyse an existing benchmark. The analyser will scan through all files given
      inside the configuration by using the given patternsets.

      If no benchmark id is given, last benchmark found in directory will be used. If benchmark directory is missing, current
      directory will be used.

   run
      Start a new benchmark run by parsing the given *JUBE* input file.
 
   update
      Check if a newer JUBE version is available.

   result
      Create a result table.

      If no benchmark id is given, last benchmark found in directory will be used. If multiple benchmarks are selected (e.g. by using ``--id all``), a combined result 
      view of all available benchmarks in the given directory will be created. If benchmark directory is missing, current directory will be used.

   benchmark_tag
      The main benchmark definition

      .. code-block:: xml

         <benchmark name="..." outpath="...">
         ...
         </benchmark>

      * container for all benchmark information
      * benchmark-name must be unique inside input file
      * ``outpath`` contains the path to the root folder for benchmark runs

        * multiple benchmarks can use the same folder
        * every benchmark and every (new) run will create a new folder (named by an unique benchmark id) inside this given ``outpath``
        * the path will be relative to input file location

   include-path_tag
      Add some include paths where to search for include files.

      .. code-block:: xml

         <include-path>
           <path>...</path>
           ...
         </include-path>

      * the additional path will be scanned for include files

   comment_tag
      Add a benchmark specific comment. These comment will be stored inside the benchmark directory.

      .. code-block:: xml

         <comment>...</comment>

   selection_tag
      Select benchmarks by name.

      .. code-block:: xml

         <selection>
           <only>...</only>
           <not>...</not>
           ...
         </selection>

      * select or unselect a benchmark by name
      * only selected benchmarks will run (when using the ``run`` command)
      * multiple ``<only>`` and ``<not>`` are allowed
      * ``<only>`` and ``<not>`` can contain a name list divided by ``,``

   patternset_tag
      A patternset is a container to store a bundle of patterns.

      .. code-block:: xml

         <patternset name="..." init_with="...">
            <pattern>...</pattern>
            ...
         </patternset>

      * patternset-name must be unique
      * ``init_with`` is optional

        * if the given filepath can be found inside of the ``JUBE_INCLUDE_PATH`` and if it contains a patternset
          using the given name, all pattern will be copied to the local set
        * local pattern will overwrite imported pattern
        * the name of the external set can differ to the local one by using ``init-with="filename.xml:external_name"``

      * patternsets can be used inside the analyser tag
      * different sets, which are used inside the same analyser, must be compatible

   pattern_tag
      A pattern is used to parse your output files and create your result data.

      .. code-block:: xml

         <pattern name="..." default="..." unit="..." mode="..." type="..." dotall="...">...</pattern>

      * ``unit`` is optional, will be used in the result table
      * ``mode`` is optional, allowed modes:

        * ``pattern``: a regular expression (default)
        * ``text``: simple text and variable concatenation
        * ``perl``: snippet evaluation (using *Perl*)
        * ``python``: snippet evaluation (using *Python*)
        * ``shell``: snippet evaluation (using *Shell*)

      * ``type`` is optional, specify datatype (for sort operation)

        * default: ``string``
        * allowed: ``int``, ``float`` or ``string``

      * ``default`` is optional: Specify default value if pattern cannot be found or if it cannot be evaluated
      * ``dotall`` is optional (default: ``false``): Can be set to ``true`` or ``false`` to specify if a ``.`` within the regular expression
        should also match newline characters, which can be very helpfull to extract a line only after a specific header was mentioned.

   statistical_values
      If there are multiple pattern matches within one file, multiple files or
      when using multiple iterations. *JUBE* will create some statistical values
      automatically:

      * ``first``: first match (default)
      * ``last``: last match
      * ``min``: min value
      * ``max``: max value
      * ``avg``: average value
      * ``std``: standard deviation
      * ``sum``: sum 
      * ``cnt``: counter

      These variabels can be accessed within the the result creation or to create derived pattern
      by ``variable_name_<statistic_option>`` e.g. ``${nodes_min}``

      The variable name itself always matches the first match.

   parameterset_tag
      A parameterset is a container to store a bundle of :term:`parameters <parameter_tag>`.

      .. code-block:: xml

         <parameterset name="..." init_with="..." duplicate="...">
            <parameter>...</parameter>
            ...
         </parameterset>

      * parameterset-name must be unique (cannot be reused inside substitutionsets or filesets)
      * ``init_with`` is optional

        * if the given filepath can be found inside of the ``JUBE_INCLUDE_PATH`` and if it contains a parameterset
          using the given name, all parameters will be copied to the local set
        * local parameters will overwrite imported parameters
        * the name of the external set can differ to the local one by using ``init-with="filename.xml:external_name"``

      * parametersets can be used inside the step-command
      * parametersets can be combined inside the step-tag, but they must be compatible:

        * Two parametersets are compatible if the parameter intersection (given by the parameter-name), only contains
          parameter based on the same definition
        * These two sets are compatible:

          .. code-block:: xml

             <parameterset name="set1">
               <parameter name="test">1,2,4</parameter>
               <parameter name="test2">foo</parameter>
             </parameterset>
             <parameterset name="set2">
               <parameter name="test">1,2,4</parameter>
               <parameter name="test3">bar</parameter>
             </parameterset>

        * These two sets are not compatible:

          .. code-block:: xml

             <parameterset name="set1">
               <parameter name="test">1,2,4</parameter>
               <parameter name="test2">foo</parameter>
             </parameterset>
             <parameterset name="set2">
               <parameter name="test">2</parameter> <!-- Template in set1 -->
               <parameter name="test2">bar</parameter> <!-- Other content in set2 -->
             </parameterset>

      * ``duplicate`` is optional and of relevance, if there are more than one parameter definitions with the same name within one parameterset. This ``duplicate`` option has lower priority than the ``duplicte`` option of the parameters. ``duplicate`` must contain one of the following three options:

        * ``replace`` (default): Parameters with the same name are overwritten
        * ``concat``: Parameters with the same name are concatenated
        * ``error``: Throws an error, if parameters with the same name are defined

   parameter_tag
      A parameter can be used to store benchmark configuration data. A set of different parameters will create
      a specific parameter environment (also called :term:`parameter space <parameter_space>`) for the different steps of the benchmark.

      .. code-block:: xml

         <parameter name="..." mode="..." type="..." separator="..." export="..." update_mode="..." duplicate="...">...</parameter>

      * a parameter can be seen as variable: Name is the name to use the variable, and the text between the tags
        will be the real content
      * name must be unique inside the given parameterset
      * ``type`` is optional (only used for sorting, default: ``string``)
      * ``mode`` is optional (used for script-types, default: ``text``)
      * ``separator`` is optional, default: ``,``
      * ``export`` is optional, if set to ``true`` the parameter will be exported to the shell environment when using ``<do>``
      * if the text contains the given (or the implicit) separator, a template will be created
      * use of another parameter:

        * inside the parameter definition, a parameter can be reused: ``... $nameofparameter ...``
        * the parameter will be replaced multiple times (to handle complex parameter structures; max: 5 times)
        * the substitution will be run before the execution step starts with the current :term:`parameter space <parameter_space>`. Only parameters reachable
          in this step will be usable for substitution!

      * Scripting modes allowed:

        * ``mode="python"``: allow *Python* snippets (using ``eval <cmd>``)
        * ``mode="perl"``: allow *Perl* snippets (using ``perl -e "print <cmd>"``)
        * ``mode="shell"``: allow *Shell* snippets
        * ``mode="env"``: include the content of an available environment variable
        * ``mode="tag"``: include the tag name if the tag was set during execution, otherwise the content is empty

      * Templates can be created, using scripting e.g.: ``",".join([str(2**i) for i in range(3)])``
      * ``update_mode`` is optional (default: ``never``)

        * can be set to ``never``, ``use``, ``step``, ``cycle`` and ``always``
        * depending on the setting the parameter will be reevaluated:

          * ``never``: no reevaluation, even if the parameterset is used multiple times
          * ``use``: reevaluation if the parameterset is explicitly used
          * ``step``: reevaluation in each new step
          * ``cycle``: reevaluation in each cycle (number of workpackages will stay unchanged)
          * ``always``: reevaluation in each step and cycle

      * ``duplicate`` is optional and of relevance, if there are more than one parameter definitions with the same name within one parameterset. This ``duplicate`` option has higher priority than the ``duplicte`` option of the parameterset. ``duplicate`` must contain one of the following four options:

        * ``none`` (default): The ``duplicate`` option of the parameterset is prioritized
        * ``replace``: Parameters with the same name are overwritten
        * ``concat``: Parameters with the same name are concatenated
        * ``error``: Throws an error, if parameters with the same name are defined


   update_mode
      The update mode is parameter attribute which can be used to control the reevaluation of the parameter content.

      These update modes are available:

      * ``never``: no reevaluation, even if the parameterset is used multiple times
      * ``use``: reevaluation if the parameterset is explicitly used
      * ``step``: reevaluation in each new step
      * ``cycle``: reevaluation in each cycle (number of workpackages will stay unchanged)
      * ``always``: reevaluation in each step and cycle

   fileset_tag
      A fileset is a container to store a bundle of links and copy commands.

      .. code-block:: xml

         <fileset name="..." init_with="...">
           <link>...</link>
           <copy>...</copy>
           <prepare>...</prepare>
           ...
         </fileset>

      * init_with is optional

        * if the given filepath can be found inside of the ``JUBE_INCLUDE_PATH`` and if it contains a fileset using the
          given name, all link and copy will be copied to the local set
        * the name of the external set can differ to the local one by using ``init-with="filename.xml:external_name"``

      * link and copy can be mixed within one fileset (or left)
      * filesets can be used inside the step-command

   link_tag
     A link can be used to create a symbolic link from your sandbox work directory to a file or directory inside your normal filesystem.

     .. code-block:: xml

        <link source_dir="..." target_dir="..." name="..." rel_path_ref="..." separator="..." active="...">...</link>

     * ``source_dir`` is optional, will be used as a prefix for the source filenames
     * ``target_dir`` is optional, will be used as a prefix for the target filenames
     * ``name`` is optional, it can be used to rename the file inside your work directory (will be ignored if you use shell extensions in your pathname)
     * ``rel_path_ref`` is optional

       * ``external`` or ``internal`` can be chosen, default: external
       * ``external``: rel.-paths based on position of xml-file
       * ``internal``: rel.-paths based on current work directory (e.g. to link files of another step)

     * ``active`` is optional

       * can be set to ``true`` or ``false`` or any *Python* parsable bool expression to enable or disable the single command
       * :term:`parameter <parameter_tag>` are allowed inside this attribute

     * each link-tag can contain a list of filenames (or directories), separated by ``,``, the default separator can be changed
       by using the ``separator`` attribute

       * if ``name`` is present, the lists must have the same length

     * in the execution step the given files or directories will be linked

   copy_tag
     A copy can be used to copy a file or directory from your normal filesytem to your sandbox work directory.

     .. code-block:: xml

        <copy source_dir="..." target_dir="..." name="..." rel_path_ref="..." separator="..." active="...">...</copy>

     * ``source_dir`` is optional, will be used as a prefix for the source filenames
     * ``target_dir`` is optional, will be used as a prefix for the target filenames
     * ``name`` is optional, it can be used to rename the file inside your work directory (will be ignored if you use shell extensions in your pathname)
     * ``rel_path_ref`` is optional

       * ``external`` or ``internal`` can be chosen, default: external
       * ``external``: rel.-paths based on position of xml-file
       * ``internal``: rel.-paths based on current work directory (e.g. to link files of another step)

     * ``active`` is optional

       * can be set to ``true`` or ``false`` or any *Python* parsable bool expression to enable or disable the single command
       * :term:`parameter <parameter_tag>` are allowed inside this attribute

     * each copy-tag can contain a list of filenames (or directories), separated by ``,``, the default separator can be changed
       by using the ``separator`` attribute

       * if ``name`` is present, the lists must have the same length

     * you can copy all files inside a directory by using ``directory/*``

       * this cannot be mixed using ``name``

     * in the execution step the given files or directories will be copied

   prepare_tag
     The prepare can contain any *Shell* command you want. It will be executed like a normal :term:`<do> <do_tag>` inside the
     step where the corresponding fileset is used. The only difference towards the normal do is, that it will be executed
     **before** the substitution will be executed.

     .. code-block:: xml

        <prepare stdout="..." stderr="..." work_dir="..." active="...">...</prepare>

     * ``stdout``- and ``stderr``-filename are optional (default: ``stdout`` and ``stderr``)
     * ``work_dir`` is optional, it can be used to change the work directory of this single command (relativly seen towards
       the original work directory)
     * ``active`` is optional

       * can be set to ``true`` or ``false`` or any *Python* parsable bool expression to enable or disable the single command
       * :term:`parameter <parameter_tag>` are allowed inside this attribute

   substituteset_tag
     A substituteset is a container to store a bundle of :term:`sub <sub_tag>` commands.

     .. code-block:: xml

        <substituteset name="..." init_with="...">
          <iofile/>
          ...
          <sub/>
          ...
        </substituteset>

     * init_with is optional

       * if the given filepath can be found inside of the ``JUBE_INCLUDE_PATH`` and if it contains a substituteset using the given name, all iofile and sub will be copied to the local set
       * local ``iofile`` will overwrite imported ones based on ``out``, local ``sub`` will overwrite imported ones based on ``source``
       * the name of the external set can differ to the local one by using ``init-with="filename.xml:external_name"``

     * substitutesets can be used inside the step-command

   iofile_tag
     A iofile declare the name (and path) of a file used for substitution.

     .. code-block:: xml

        <iofile in="..." out="..." out_mode="..." />

     * ``in`` and ``out`` filepath are relative to the current work directory for every single step (not relative to the path of the inputfile)
     * ``in`` and ``out`` can be the same
     * ``out_mode`` is optional, can be ``w`` or ``a`` (default: ``w``)

       * ``w`` : ``out``-file will be overridden
       * ``a`` : ``out``-file will be appended

   sub_tag
     A substition expression.

     .. code-block:: xml

        <sub source="..." dest="..." />

     * ``source``-string will be replaced by ``dest``-string
     * both can contain parameter: ``... $nameofparameter ...``

   step_tag
     A step give a list of *Shell* operations and a corresponding parameter environment.

     .. code-block:: xml

        <step name="..." depend="..." work_dir="..." suffix="..." shared="..." active="..." 
              export="..." max_async="..." iterations="..." cycles="..." procs="..." do_log_file="...">
          <use from="">...</use>
          ...
          <do></do>
          ...
        </step>

     * parametersets, filesets and substitutionsets are usable
     * using sets ``<use>set1,set2</use>`` is the same as ``<use>set1</use><use>set2</use>``
     * parameter can be used inside the ``<use>``-tag
     * the ``from`` attribute is optional and can be used to specify an external set source
     * any name must be unique, it is **not allowed to reuse** a set
     * ``depend`` is optional and can contain a list of other step names which must be executed before the current step
     * ``max_async`` is optional and can contain a number (or a parameter) which describe how many :term:`workpackages <workpackage>` can be executed asynchronously (default: 0 means no limitation).
       This option is only important if a :term:`do <do_tag>` inside the step contains a ``done_file`` attribute and should be executed in the background (or managed by a jobsystem).
       In this case *JUBE* will manage that there will not be to many instances at the same time. To update the benchmark and start further instances, if the first ones were finished,
       the :term:`continue` command must be used.
     * ``work_dir`` is optional and can be used to switch to an alternative work directory

       * the user had to handle **uniqueness of this directory** by his own
       * no automatic parent/children link creation

     * ``suffix`` is optional and can contain a string (parameters are allowed) which will be attached to the default workpackage directory name
     * ``active`` is optional

       * can be set to ``true`` or ``false`` or any *Python* parsable bool expression to enable or disable the single command
       * :term:`parameter <parameter_tag>` are allowed inside this attribute

     * ``shared`` is optional and can be used to create a shared folder which can be accessed by all workpackages based on this step

       * a link, named by the attribute content, is used to access the shared folder
       * the shared folder link will not be automatically created in an alternative working directory!

     * ``export="true"``

       * the environment of the current step will be exported to an dependent step

     * ``iterations`` is optional. All workpackages within this step will be executed multiple times if the iterations value is used.
     * ``cycles`` is optional. All ``<do>`` commands within the step will be executed ``cycles``-times
     * ``procs`` is optional. Amount of processes used to execute the parameter expansions of the corresponding step in parallel.
     * ``do_log_file`` is optional. Name or path of a do log file trying to mimick the do steps and the environment of a workpacakge of a step to produce an executable script.

   do_tag
     A do contain a executable *Shell* operation.

     .. code-block:: xml

        <do stdout="..." stderr="..." active="...">...</do>
        <do done_file="..." error_file="...">...</do>
        <do break_file="...">...</do>
        <do shared="true">...</do>
        <do work_dir="...">...</do>


     * ``do`` can contain any *Shell*-syntax-snippet (:term:`parameter <parameter_tag>` will be replaced ``... $nameofparameter ...``)
     * ``stdout``- and ``stderr``-filename are optional (default: ``stdout`` and ``stderr``)
     * ``work_dir`` is optional, it can be used to change the work directory of this single command (relativly seen towards
       the original work directory)
     * ``active`` is optional

       * can be set to ``true`` or ``false`` or any *Python* parsable bool expression to enable or disable the single command
       * :term:`parameter <parameter_tag>` are allowed inside this attribute

     * ``done_file``-filename and ``error_file`` are optional

       * by using ``done_file`` the user can mark async-steps. The operation will stop until the script will create the named file inside the work directory.
       * by using ``error_file`` the operation will produce a error if the named file can be found inside the work directory. This feature can be used together with the
         ``done_file`` to signalise broken async-steps.

     * ``break_file``-filename is optional

       * by using ``break_file`` the user can stop further cycle runs. the current step will be directly marked with finalized and further ``<do>`` will be ignored.

     * ``shared="true"``

       * can be used inside a step using a shared folder
       * cmd will be **executed inside the shared folder**
       * cmd will run once (synchronize all workpackages)
       * ``$jube_wp_...`` - parameter cannot be used inside the shared command

   analyser_tag
     The analyser describe the steps and files which should be scanned using a set of pattern.

     .. code-block:: xml

        <analyser name="..." reduce="...">
          <use from="">...</use>
          ...
          <analyse step="...">
            <file use="">...</file>
          </analyse>
          ...
        </analyser>

     * you can use different patternsets to analyse a set of files
     * only patternsets are usable
     * using patternsets ``<use>set1,set2</use>`` is the same as ``<use>set1</use><use>set2</use>``
     * the from-attribute is optional and can be used to specify an external set source
     * any name must be unique, it is not allowed to reuse a set
     * the step-attribute contains an existing stepname
     * each file using each workpackage will be scanned seperatly
     * the ``use`` argument inside the ``<file>`` tag is optional and can be used to specify a file specific patternset;

       * the global ``<use>`` and this local use will be combined and evaluated at the same time
       * a ``from```subargument is not possible in this local ``use``

     * ``reduce`` is optional (default: ``true`` )

       * ``true`` : Combine result lines if iteration-option is used
       * ``false`` : Create single line for each iteration

   database_tag
     Create sqlite3 database

     .. code-block:: xml

        <database name="..." primekeys="..." file="..." filter="...">
          <key>...</key>
          ...
        </database>

     * "name": name of the table in the database

     * "<key>" must contain an single parameter or pattern name

     * "primekeys" is optional: can contain a list of parameter or
       pattern names (separated by ,). Given parameters or patterns
       will be used as primary keys of the database table. All
       primekeys have to be listed as a "<key>" as well. Modification
       of primary keys of an existing table is not supported.
       If no primekeys are set then each `jube result` will add new rows
       to the database. Otherwise rows with matching primekeys will be updated.

     * "file" is optional. The given value should hold the full path
       to the database file. If the file including the path does not
       exists it will be created. Absolute and relative paths are supported.

     * "filter" is optional. It can contain a bool expression to show only specific result entries.

   result_tag
     The result tag is used to handle different visualisation types of your analysed data.

     .. code-block:: xml

        <result result_dir="...">
          <use>...</use>
          ...
          <table>...</table>
          <syslog>...</syslog>
          ...
        </result>

     * ``result_dir`` is optional. Here you can specify an different output directory. Inside of this directory a subfolder
       named by the current benchmark id will be created. Default: benchmark_dir/result
     * only analyser are usable
     * using analyser ``<use>set1,set2</use>`` is the same as ``<use>set1</use><use>set2</use>``

   types
     :term:`Parameter <parameter_tag>` and :term:`Pattern <pattern_tag>` allow a type specification. This type is either used for
     sorting within the result table and is also used to validate the parameter content. The types are not used to convert parameter values,
     e.g. a floating value will stay unchanged when used in any other context even if the type int was specified.

     allowed types are:

     * ``string`` (this is also the default type)
     * ``int``
     * ``float``

   table_tag
     A simple ASCII based table ouput.

     .. code-block:: xml

        <table name="..." style="..." sort="..." separator="..." transpose="..." filter="...">
          <column>...</column>
          ...
        </table>

     * ``style`` is optional; allowed styles: ``csv``, ``pretty``, ``aligned``; default: ``csv``
     * ``separator`` is optional; only used in csv-style, default: ``,``
     * ``sort`` is optional: can contain a list of parameter- or patternnames (separated by ,).
       Given patterntype or parametertype will be used for sorting
     * ``<column>`` must contain an single parameter- or patternname
     * ``transpose`` is optional (default: ``false``)
     * ``filter`` is optional, it can contain a bool expression to show only specific result entries

   column_tag
     A line within a ASCII result table. The <column>-tag can contain the name of a pattern or
     the name of a parameter.

     .. code-block:: xml

        <column colw="..." format="..." title="...">...</column>

     * ``colw`` is optional: column width
     * ``title`` is optional: column title
     * ``format`` can contain a C like format string: e.g. ``format=".2f"``

   syslog_tag
     A syslog result type

     .. code-block:: xml

        <syslog name="..." address="..." host="..." port="..." sort="..." format="..." filter="...">
          <key>...</key>
          ...
        </syslog>

     * Syslog deamon can be given by a ``host`` and ``port`` combination (default ``port``: 541) or
       by a socket ``address`` e.g.: ``/dev/log`` (mixing of host and address is not allowed)
     * ``format`` is optional: can contain a log format written in a pythonic way (default: ``jube[%(process)s]: %(message)s``)
     * ``sort`` is optional: can contain a list of parameter- or patternnames (separated by ,).
       Given patterntype or parametertype will be used for sorting
     * ``<key>`` must contain an single parameter- or patternname
     * ``filter`` is optional, it can contain a bool expression to show only specific result entries

   key_tag
     A syslog result key. ``<key>`` must contain an single parameter- or patternname.

     .. code-block:: xml

        <key format="..." title="...">...</key>

     * ``title`` is optional: alternative key title
     * ``format`` can contain a C like format string: e.g. ``format=".2f"``

   parameter_space
     The parameter space for a specific benchmark run is the bundle of all possible parameter combinations.
     E.g. there are to different parameter: a = 1,2 and b= "p","q" then you will get four different parameter
     combinations: ``a=1``, ``b="p"``; ``a=1``, ``b="q"``; ``a=2``, ``b="p"``; ``a=2``, ``b="q"``.

     The parameter space of a specific step will be one of these parameter combinations. To fulfill all combinations
     the step will be executed multible times (each time using a new combination). The specific combination of a step and
     an expanded parameter space is named :term:`workpackage`.

   include_tag
     Include *XML*-data from an external file.

     .. code-block:: xml

        <include from="..." path="..." />

     * ``<include>`` can be used to include an external *XML*-structure into the current file
     * can be used at every position (inside the ``<jube>``-tag)
     * path is optional and can be used to give an alternative xml-path inside the include-file (default: root-node)

   workpackage
      A workpackage is the combination of a :term:`step <step_tag>` (which contains all operations) and one parameter setting out of the expanded :term:`parameter space <parameter_space>`.

      Every workpackage will run inside its own sandbox directory!

   tagging
      Tagging is a simple way to mark parts of your input file to be includable or excludable.

      * Every available ``<tag>`` (not the root ``<jube>``-tag) can contain a tag-attribute
      * The tag-attribute can contain a list of names: ``tag="a,b,c"`` or "not" names: ``tag="a,!b,c"``
      * When running *JUBE*, multiple tags can be send to the input-file parser::

          jube run <filename> --tag a b

        * ``<tags>`` which does not contain one of these names will be hidden inside the include file
        * <tags> which does not contain any tag-attribute will stay inside the include file

      * "not" tags are more important than normal tags: ``tag="a,!b,c"`` and running with ``a b`` will hide the ``<tag>`` because
        the ``!b`` is more important than the ``a``

   directory_structure
      * every (new) benchmark run will create its own directory structure
      * every single workpackage will create its own directory structure
      * user can add files (or links) to the workpackage dir, but the real position in filesystem will be seen as a blackbox
      * general directory structure:

        .. code-block:: none

           benchmark_runs (given by "outpath" in xml-file)
           |
           +- 000000 (determined through benchmark-id)
              |
              +- 000000_compile (step: just an example, can be arbitrary chosen)
                 |
                 +- work (user environment)
                 +- done (workpackage finished information file)
                 +- ...  (more jube internal information files)
              +- 000001_execute
                 |
                 +- work
                    |
                    +- compile -> ../../000000_compile/work (automatic generated link for depending step)
                 +- wp_done_00 (single "do" finished, but not the whole workpackage)
                 +- ...
              +- 000002_execute
              +- result (result data)
              +- configuration.xml (benchmark configuration information file)
              +- workpackages.xml (workpackage graph information file)
              +- analyse.xml (analyse data)
           +- 000001 (determined through benchmark-id)
              |
              +- 000000_compile (step: just an example, can be arbitrary chosen)
              +- 000001_execute
              +- 000002_postprocessing

   general_structure_xml

      .. code-block:: xml

         <?xml version="1.0" encoding="UTF-8"?>
         <!-- Basic top level JUBE structure -->
         <jube>
           <!-- optional additional include paths -->
           <include-path>
             <path>...</path>
             ...
           </include-path>
           <!-- optional benchmark selection -->
           <selection>
             <only>...</only>
             <not>...</not>
             ...
           </selection>
           <!-- global sets -->
           <parameterset name="">...</parameterset>
           <substitutionset name="">...</substitutionset>
           <fileset name="">...</fileset>
           <patternset name="">...</patternset>
           ...
           <benchmark name="" outpath="">
             <!-- optional benchmark comment -->
             <comment>...</comment>
             <!-- local benchmark parametersets -->
             <parameterset name="">...</parameterset>
             ...
             <!-- files, which should be used -->
             <fileset name="">...</fileset>
             ...
             <!-- substitution rules -->
             <substituteset name="">...</substituteset>
             ...
             <!-- pattern -->
             <patternset name="">...</patternset>
             ...
             <!-- commands -->
             <step name="">...</step>
             ...
             <!-- analyse -->
             <analyser name="">...</analyser>
             ...
             <!-- result -->
             <result>...</result>
             ...
           </benchmark>
           ...
         </jube>

   general_structure_yaml

      .. code-block:: yaml

         # optional additional include paths
         include-path:
           ...

         # optional benchmark selection 
         selection:
           only: ...
           not: ...

         # global sets
         parameterset: 
           ...
         substitutionset:
           ...
         fileset:
           ...
         patternset:
           ... 

         benchmark: # can be skipped if only a single benchmark is handled
           - name: ...
             outpath: ...
             # optional benchmark comment
             comment: ...

             # local sets
             parameterset:
               ...
             substitutionset:
               ...
             fileset:
               ...
             patternset:
               ...

             # commands
             step:
               ...

             analyser:
               ...
             result:
               ...

   jube_pattern
      List of available jube pattern:

      * ``$jube_pat_int``: integer number
      * ``$jube_pat_nint``: integer number, skip
      * ``$jube_pat_fp``: floating point number
      * ``$jube_pat_nfp``: floating point number, skip
      * ``$jube_pat_wrd``: word
      * ``$jube_pat_nwrd``: word, skip
      * ``$jube_pat_bl``: blank space (variable length), skip

   jube_variables
      List of available jube variables:

      * Benchmark:

        * ``$jube_benchmark_name``: current benchmark name
        * ``$jube_benchmark_id``: current benchmark id
        * ``$jube_benchmark_padid``: current benchmark id with preceding zeros
        * ``$jube_benchmark_home``: original input file location
        * ``$jube_benchmark_rundir``: main benchmark specific execution directory
        * ``$jube_benchmark_start``: benchmark starting time

      * Step:

        * ``$jube_step_name``: current step name
        * ``$jube_step_iterations``: number of step iterations (default: 1)
        * ``$jube_step_cycles``: number of step cycles (default: 1)

      * Workpackage:

        * ``$jube_wp_id``: current workpackage id
        * ``$jube_wp_padid``: current workpackage id with preceding zeros
        * ``$jube_wp_iteration``: current iteration number (default: 0)
        * ``$jube_wp_parent_<parent_name>_id``: workpackage id of selected parent step
        * ``$jube_wp_relpath``: relative path to workpackage work directory (relative towards configuration file)
        * ``$jube_wp_abspath``: absolute path to workpackage work directory
        * ``$jube_wp_envstr``: a string containing all exported parameter in shell syntax::

            export par=$par
            export par2=$par2

        * ``$jube_wp_envlist``: list of all exported parameter names
        * ``$jube_wp_cycle``: id of current step cycle (starts at 0)
