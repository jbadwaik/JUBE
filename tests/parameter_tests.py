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
"""Parameter related tests"""

from __future__ import (print_function,
                        unicode_literals,
                        division)

import unittest
import jube2.parameter


class TestParameter(unittest.TestCase):

    """Parameter test class"""

    def setUp(self):
        self.para_cons = \
            jube2.parameter.Parameter.create_parameter("test", "3")
        self.temp_values = ["2", "3", "4"]
        self.para_temp = \
            jube2.parameter.Parameter.create_parameter(
                "test", ",".join(self.temp_values))
        self.para_select = \
            jube2.parameter.Parameter.create_parameter("test", "2,3,4",
                                                       selected_value="3")
        self.para_export = \
            jube2.parameter.Parameter.create_parameter("test2", "4",
                                                       export=True)
        self.para_no_template = \
            jube2.parameter.Parameter.create_parameter("no_templates", "2,3,4",
                                                       no_templates=True)
        self.para_eval = \
            jube2.parameter.Parameter.create_parameter("eval", "2+2",
                                                       parameter_mode="python")
        self.para_error = \
            jube2.parameter.Parameter.create_parameter("error", "2+'test'",
                                                       parameter_mode="python")
        self.para_search_method_3 = \
            jube2.parameter.Parameter.create_parameter("dummy_name", "dummy_value",
                                                       parameter_mode="python")
        self.para_search_method_2 = \
            jube2.parameter.Parameter.create_parameter("dummy_name", "dummy_value",
                                                       parameter_mode="python")
        self.para_search_method_1 = \
            jube2.parameter.Parameter.create_parameter("dummy_name", "dummy_value",
                                                       parameter_mode="python")
        self.para_search_method_3.eval_helper = self.para_search_method_1.search_method
        self.para_search_method_3.based_on = None
        self.para_search_method_2.eval_helper = "not a method"
        self.para_search_method_2.based_on = self.para_search_method_3
        self.para_search_method_1.eval_helper = "not a method"
        self.para_search_method_1.based_on = self.para_search_method_2

    def test_constant(self):
        """Test Constants"""
        self.assertEqual(self.para_cons.value, "3")
        self.assertFalse(self.para_cons.is_template)
        self.assertEqual(self.para_cons.parameter_type, "string")
        self.assertTrue(repr(self.para_cons).startswith("Parameter({"))
        self.assertTrue(repr(self.para_cons).endswith("})"))

    def test_template(self):
        """Test Template"""
        self.assertTrue(self.para_temp.is_template)
        self.assertEqual(self.para_temp.value, "2,3,4")

        # Template become constant check
        for idx, static_par in enumerate(self.para_temp.expand()):
            self.assertEqual(static_par.value, self.temp_values[idx])
            self.assertFalse(static_par.is_template)
            self.assertTrue(static_par.is_equivalent(self.para_temp))

        # Copy check
        parameter_copy = self.para_temp.copy()
        self.assertFalse(parameter_copy is self.para_temp)
        self.assertTrue(parameter_copy.is_equivalent(self.para_temp))
        self.assertEqual(parameter_copy.value, self.para_temp.value)

        # Equivalent check
        self.assertFalse(self.para_cons.is_equivalent(self.para_temp))
        self.assertTrue(self.para_select.is_equivalent(self.para_temp))

        # Parameter based on template check
        self.assertEqual(self.para_select.value, "3")
        self.assertFalse(self.para_select.is_template)

    def test_no_template(self):
        self.assertFalse(self.para_no_template.is_template)
        self.assertEqual(self.para_no_template.value, "2,3,4")

    def test_eval(self):
        """Test parameter evaluation"""
        eval_para, changed = self.para_eval.substitute_and_evaluate([])
        self.assertTrue(changed)
        self.assertEqual(eval_para.value, "4")
        self.assertRaises(RuntimeError,
                          self.para_error.substitute_and_evaluate, [])

    def test_etree_repr(self):
        """Test Etree repr"""
        etree = self.para_temp.etree_repr()
        self.assertEqual(etree.tag, "parameter")
        self.assertEqual(etree.get("separator"), ",")
        self.assertEqual(etree.get("type"), "string")
        self.assertEqual(etree.text, "2,3,4")

        static_par = list(self.para_temp.expand())[2]
        etree = static_par.etree_repr(use_current_selection=True)
        self.assertEqual(etree.find("value").text, "2,3,4")
        self.assertEqual(etree.find("selection").text, "4")

        # Export check
        self.assertTrue(self.para_export.export)
        self.assertFalse(self.para_cons.export)
        etree = self.para_export.etree_repr()
        self.assertEqual(etree.get("export"), "true")

    def test_search_method(self):
        """ Test the searching of method method """
        self.assertEqual(self.para_search_method_1.search_method(
            propertyString="eval_helper",
            recursiveProperty="based_on"), True)
        self.assertEqual(self.para_search_method_3.search_method(
            propertyString="name",
            recursiveProperty="based_on"), False)


class TestParameterSet(unittest.TestCase):

    """ParameterSet test class"""

    def setUp(self):
        self.temp_values = ["2", "3", "4"]
        self.para_cons = \
            jube2.parameter.Parameter.create_parameter("test", "3")
        self.para_export = \
            jube2.parameter.Parameter.create_parameter("test2", "4",
                                                       export=True)
        self.para_temp = \
            jube2.parameter.Parameter.create_parameter(
                "test2", ",".join(self.temp_values))
        self.para_select = \
            jube2.parameter.Parameter.create_parameter("test2", "2,3,4",
                                                       selected_value="3")
        self.para_sub = \
            jube2.parameter.Parameter.create_parameter("test4", "$test2")
        self.para_eval = \
            jube2.parameter.Parameter.create_parameter("test5",
                                                       "${test4} * 2",
                                                       parameter_mode="python")
        self.para_eval2 = \
            jube2.parameter.Parameter.create_parameter("test6",
                                                       "$$test4")
        parameter3 = jube2.parameter.Parameter.create_parameter("test3", "5")

        self.parameterset = jube2.parameter.Parameterset("test")
        self.parameterset.add_parameter(self.para_cons)
        self.parameterset.add_parameter(self.para_temp)

        self.parameterset2 = jube2.parameter.Parameterset("test2")
        self.parameterset2.add_parameter(parameter3)
        self.parameterset2.add_parameter(self.para_export)

        self.parameterset3 = jube2.parameter.Parameterset("test3")
        self.parameterset3.add_parameter(parameter3)
        self.parameterset3.add_parameter(self.para_select)

    def test_set(self):
        """Test ParameterSet functionality"""
        # Test add parameter to set
        self.assertEqual(self.parameterset.name, "test")
        self.assertTrue(self.parameterset.has_templates)
        self.assertTrue(self.para_cons in self.parameterset)
        self.assertTrue((["test", "test2"] ==
                         sorted(self.parameterset.all_parameter_names)))
        constant_dict = self.parameterset.constant_parameter_dict
        self.assertTrue("test" in constant_dict)
        self.assertFalse("test2" in constant_dict)
        template_dict = self.parameterset.template_parameter_dict
        self.assertFalse("test" in template_dict)
        self.assertTrue("test2" in template_dict)

        # Test not compatible parameterset
        self.assertFalse(self.parameterset.is_compatible(self.parameterset2))
        self.assertTrue(
            "test2" in self.parameterset.get_incompatible_parameter(
                self.parameterset2))
        self.assertFalse(
            "test" in self.parameterset.get_incompatible_parameter(
                self.parameterset2))

        # Test export
        self.assertEqual(
            self.parameterset2.export_parameter_dict,
            {"test2": self.para_export})

        # Test __getitem__ failing
        self.assertEqual(self.parameterset["nonexistent"], None)

        # Test clear and copy
        parameterset = self.parameterset2.copy()
        self.assertFalse(parameterset is self.parameterset2)
        self.assertTrue(parameterset.is_compatible(self.parameterset2))
        self.assertEqual(len(parameterset), 2)
        parameterset.clear()
        self.assertEqual(len(parameterset), 0)

        # Test __repr__
        self.assertTrue(repr(self.parameterset).startswith("Parameterset"))

    def test_delete(self):
        """Test parameter deletion"""
        parameterset = self.parameterset.copy()
        self.assertFalse(self.para_export in parameterset)
        parameterset.add_parameter(self.para_export)
        self.assertTrue(self.para_export in parameterset)
        parameterset.delete_parameter(self.para_export)
        # Deleting should not raise an error
        parameterset.delete_parameter("a_parameter")
        self.assertFalse(self.para_export in parameterset)

    def test_compatible(self):
        """Test compatible parameterset"""
        parameterset = self.parameterset.copy()
        for static_par in self.para_temp.expand():
            parameterset.add_parameter(static_par)
        self.assertEqual(parameterset["test2"].value, "4")
        self.assertTrue(self.parameterset.is_compatible(parameterset))

    def test_update(self):
        """Test update_parameterset"""
        parameterset = self.parameterset.copy()
        self.assertEqual(sorted(list(parameterset.parameter_dict)),
                         ["test", "test2"])
        self.assertEqual(sorted(list(self.parameterset3.parameter_dict)),
                         ["test2", "test3"])
        parameterset.update_parameterset(self.parameterset3)
        self.assertEqual(parameterset.template_parameter_dict, dict())
        self.assertEqual(len(parameterset), 2)

        # Test add_parameterset
        parameterset.add_parameterset(self.parameterset3)
        self.assertEqual(len(parameterset), 3)

    def test_expand(self):
        """Check parameterset expand_templates"""
        parameterset = self.parameterset.copy()
        self.assertTrue("test2" in parameterset.template_parameter_dict)

        for idx, new_parameterset in (
                enumerate(parameterset.expand_templates())):
            self.assertEqual(new_parameterset.template_parameter_dict, dict())
            self.assertFalse(new_parameterset.has_templates)
            self.assertEqual(new_parameterset["test2"].value,
                             self.temp_values[idx])

        # Substitution and evaluation check
        parameterset = self.parameterset.copy()
        parameterset.add_parameter(self.para_sub)
        parameterset.add_parameter(self.para_eval)
        parameterset.add_parameter(self.para_eval2)
        self.assertFalse(
            self.para_sub.can_substitute_and_evaluate(parameterset))
        for idx, new_parameterset in (
                enumerate(parameterset.expand_templates())):
            self.assertTrue(
                self.para_sub.can_substitute_and_evaluate(new_parameterset))
            new_parameterset.parameter_substitution(final_sub=True)
            self.assertEqual(new_parameterset["test4"].value,
                             self.temp_values[idx])
            self.assertEqual(
                new_parameterset["test5"].based_on.value,
                self.para_eval.value)
            self.assertEqual(
                new_parameterset["test6"].value, "$test4")
            self.assertEqual(new_parameterset["test5"].value,
                             str(int(self.temp_values[idx]) * 2))

        parameterset = jube2.parameter.Parameterset("test")
        parameterset2 = self.parameterset2.copy()
        parameterset.add_parameter(self.para_sub)
        parameterset2.add_parameter(self.para_sub)
        parameterset.parameter_substitution(
            additional_parametersets=[parameterset2])
        self.assertEqual(parameterset[self.para_sub.name].value,
                         self.para_export.value)
        self.assertEqual(parameterset2[self.para_sub.name].value,
                         self.para_sub.value)

    def test_etree_repr(self):
        """Etree repr check"""
        etree = self.parameterset.etree_repr()
        self.assertEqual(etree.tag, "parameterset")
        self.assertEqual(len(etree.findall("parameter")), 2)

    def test_concat_parameter(self):
        """Test concat_parameter"""
        param1 = jube2.parameter.TemplateParameter(
            name='param1',
            value=['1','2','3'],
            separator=',',
            parameter_type='string',
            parameter_mode='text',
            duplicate='none')
        param2 = jube2.parameter.TemplateParameter(
            name='param1',
            value=['4','5','6'],
            separator=',',
            parameter_type='string',
            parameter_mode='text',
            duplicate='none')
        param3 = jube2.parameter.StaticParameter(
            name='param1',
            value='',
            separator=',',
            parameter_type='string',
            parameter_mode='text',
            duplicate='none')

        paramset1 = jube2.parameter.Parameterset(name='paramset1',duplicate='concat')
        paramset1.add_parameter(param1)
        self.assertEqual(paramset1.concat_parameter(param2)._value,['1','2','3','4','5','6'])
        self.assertEqual(paramset1.concat_parameter(param3)._value,['','1','2','3'])

    def test_check_parameter_options(self):
        """Test check_parameter_options"""
        param1 = jube2.parameter.TemplateParameter(
            name='param1',
            value=['1','2','3'],
            separator=',',
            parameter_type='string',
            parameter_mode='text',
            duplicate='none')
        param2 = jube2.parameter.TemplateParameter(
            name='param1',
            value=['4','5','6'],
            separator=',',
            parameter_type='string',
            parameter_mode='text',
            duplicate='none')
        param3 = jube2.parameter.TemplateParameter(
            name='param1',
            value=['7','8','9'],
            separator=',',
            parameter_type='string',
            parameter_mode='text',
            duplicate='replace')
        paramset1 = jube2.parameter.Parameterset(name='paramset1',duplicate='concat')
        paramset1.add_parameter(param1)
        paramset1.check_parameter_options(param2)
        with self.assertRaises(ValueError):
            paramset1.check_parameter_options(param3)

    def test_add_parameter(self):
        """Test add_parameter"""
        param1 = jube2.parameter.TemplateParameter(
            name='param1',
            value=['1','2','3'],
            separator=',',
            parameter_type='string',
            parameter_mode='text',
            duplicate='none')
        param2 = jube2.parameter.TemplateParameter(
            name='param1',
            value=['4','5','6'],
            separator=',',
            parameter_type='string',
            parameter_mode='text',
            duplicate='none')
        param3 = jube2.parameter.StaticParameter(
            name='param1',
            value='84',
            separator=',',
            parameter_type='int',
            parameter_mode='text',
            duplicate='error')
        param4 = jube2.parameter.StaticParameter(
            name='param2',
            value='',
            separator=',',
            parameter_type='string',
            parameter_mode='text',
            duplicate='replace')
        param5 = jube2.parameter.StaticParameter(
            name='param2',
            value='1',
            separator=',',
            parameter_type='string',
            parameter_mode='text',
            duplicate='replace')
        param6 = jube2.parameter.StaticParameter(
            name='param1',
            value='42',
            separator=',',
            parameter_type='int',
            parameter_mode='text',
            duplicate='none')
        param7 = jube2.parameter.StaticParameter(
            name='param3',
            value='3141',
            separator=',',
            parameter_type='int',
            parameter_mode='text',
            duplicate='erroneous_duplicate_type')

        paramset1 = jube2.parameter.Parameterset(name='paramset1',duplicate='concat')
        paramset1.add_parameter(param1)
        self.assertEqual(paramset1._parameters[param1._name]._value,['1','2','3'])
        paramset1.add_parameter(param2)
        self.assertEqual(paramset1._parameters[param2._name]._value,['1','2','3','4','5','6'])
        with self.assertRaises(ValueError):
            paramset1.add_parameter(param6)
        with self.assertRaises(ValueError):
            paramset1.add_parameter(param3)

        paramset1.add_parameter(param7)
        with self.assertRaises(Exception):
            paramset1.add_parameter(param7)

        paramset2 = jube2.parameter.Parameterset(name='paramset2',duplicate='replace')
        paramset2.add_parameter(param1)
        paramset2.add_parameter(param2)
        self.assertEqual(paramset2._parameters[param2._name]._value,['4','5','6'])
        paramset2.add_parameter(param6)
        self.assertEqual(paramset2._parameters[param6._name]._value,'42')
        self.assertEqual(paramset2._parameters[param6._name]._type,'int')

        paramset3 = jube2.parameter.Parameterset(name='paramset3',duplicate='error')
        paramset3.add_parameter(param1)
        with self.assertRaises(Exception):
            paramset3.add_parameter(param2)

        paramset1.add_parameter(param4)
        paramset1.add_parameter(param5)
        self.assertEqual(paramset1._parameters[param4._name]._value,'1')


if __name__ == "__main__":
    unittest.main()
