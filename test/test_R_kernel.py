#!/usr/bin/env python3
#
# Copyright (c) Bo Peng and the University of Texas MD Anderson Cancer Center
# Distributed under the terms of the 3-clause BSD License.

#
# NOTE: for some namespace reason, this test can only be tested using
# nose.
#
# % nosetests test_kernel.py
#
#
import os
import unittest
from ipykernel.tests.utils import assemble_output, execute, wait_for_idle
from sos_notebook.test_utils import sos_kernel, get_result, get_display_data, \
    clear_channels

class TestRKernel(unittest.TestCase):
    #
    # Beacuse these tests would be called from sos/test, we
    # should switch to this directory so that some location
    # dependent tests could run successfully
    #
    def setUp(self):
        self.olddir = os.getcwd()
        if os.path.dirname(__file__):
            os.chdir(os.path.dirname(__file__))

    def tearDown(self):
        os.chdir(self.olddir)

    def testGetPythonDataFrameFromR(self):
        # Python -> R
        with sos_kernel() as kc:
            iopub = kc.iopub_channel
            # create a data frame
            execute(kc=kc, code='''
import pandas as pd
import numpy as np
arr = np.random.randn(1000)
arr[::10] = np.nan
df = pd.DataFrame({'column_{0}'.format(i): arr for i in range(10)})
''')
            clear_channels(iopub)
            execute(kc=kc, code="%use R")
            wait_for_idle(kc)
            execute(kc=kc, code="%get df")
            wait_for_idle(kc)
            execute(kc=kc, code="dim(df)")
            res = get_display_data(iopub)
            self.assertEqual(res, '[1] 1000   10')
            execute(kc=kc, code="%use sos")
            wait_for_idle(kc)
            #

    def testGetPythonDictWithSpecialKeyFromR(self):
        # Python -> R
        with sos_kernel() as kc:
            iopub = kc.iopub_channel
            # create a data frame
            execute(kc=kc, code='''
special_dict = {}
special_dict['11111'] = 1
special_dict['_1111'] = 'a'
special_dict[11112] = 2
special_dict[(1,2)] = 3
''')
            wait_for_idle(kc)
            execute(kc=kc, code='''%use R
%get special_dict
keys = names(special_dict)
''')
            wait_for_idle(kc)
            execute(kc=kc, code='''%use sos
%get keys --from R            
%dict keys
''')
            res = get_result(iopub)['keys']
            for key in ["X11111",  "X_1111",  "X11112",  "X_1__2_"]:
                self.assertTrue(key in res, f"Expecting {key}")

    def testGetPythonDataFromR(self):
        with sos_kernel() as kc:
            iopub = kc.iopub_channel
            execute(kc=kc, code='''
null_var = None
num_var = 123
import numpy
import pandas
num_arr_var = numpy.array([1, 2, 3])
logic_var = True
logic_arr_var = [True, False, True]
char_var = '1"23'
char_arr_var = ['1', '2', '3']
list_var = [1, 2, '3']
dict_var = dict(a=1, b=2, c='3')
set_var = {1, 2, '3'}
mat_var = numpy.matrix([[1,2],[3,4]])
recursive_var = {'a': {'b': 123}, 'c': True}
comp_var = 1+2j
seri_var = pandas.Series([1,2,3,3,3,3])
''')
            wait_for_idle(kc)
            execute(kc=kc, code='''\
%use R
%get null_var num_var num_arr_var logic_var logic_arr_var char_var char_arr_var mat_var set_var list_var dict_var recursive_var comp_var seri_var
%dict -r
%put null_var num_var num_arr_var logic_var logic_arr_var char_var char_arr_var mat_var set_var list_var dict_var recursive_var comp_var seri_var
%use sos
seri_var = list(seri_var)
''')
            wait_for_idle(kc)
            execute(kc=kc, code='''\
%dict null_var num_var num_arr_var logic_var logic_arr_var char_var char_arr_var mat_var set_var list_var dict_var recursive_var comp_var seri_var
''')
            res = get_result(iopub)
            self.assertEqual(res['null_var'], None)
            self.assertEqual(res['num_var'], 123)
            self.assertEqual(res['num_arr_var'].tolist(), [1, 2, 3])
            self.assertEqual(res['logic_var'], True)
            self.assertEqual(res['logic_arr_var'], [True, False, True])
            self.assertEqual(res['char_var'], '1"23')
            self.assertEqual(res['char_arr_var'], ['1', '2', '3'])
            self.assertEqual(res['list_var'], [1,2,'3'])
            self.assertEqual(res['dict_var'], {'a': 1, 'b': 2, 'c': '3'})
            self.assertEqual(res['mat_var'].shape, (2,2))
            self.assertEqual(res['recursive_var'],  {'a': {'b': 123}, 'c': True})
            self.assertEqual(res['comp_var'], 1+2j)
            self.assertEqual(res['seri_var'], [1,2,3,3,3,3])

    def testPutRDataFrameToPython(self):
        # R -> Python
        with sos_kernel() as kc:
            iopub = kc.iopub_channel
            # create a data frame
            execute(kc=kc, code='%use R')
            wait_for_idle(kc)
            execute(kc=kc, code="%put mtcars")
            assemble_output(iopub)
            # the message can contain "Loading required package feathre"
            #self.assertEqual(stderr, '')
            execute(kc=kc, code="%use sos")
            wait_for_idle(kc)
            execute(kc=kc, code="mtcars.shape")
            res = get_result(iopub)
            self.assertEqual(res, (32, 11))
            execute(kc=kc, code="mtcars.index[0]")
            res = get_result(iopub)
            self.assertEqual(res, 'Mazda RX4')

    def testPutRDataToPython(self):
        with sos_kernel() as kc:
            iopub = kc.iopub_channel
            # create a data frame
            execute(kc=kc, code="""\
%use R
null_var = NULL
num_var = 123
num_arr_var = c(1, 2, 3)
logic_var = TRUE
logic_arr_var = c(TRUE, FALSE, TRUE)
char_var = '1\"23'
char_arr_var = c(1, 2, '3')
list_var = list(1, 2, '3')
named_list_var = list(a=1, b=2, c='3')
mat_var = matrix(c(1,2,3,4), nrow=2)
recursive_var = list(a=1, b=list(c=3, d='whatever'))
comp_var = 1+2i
seri_var = setNames(c(1,2,3,3,3,3),c(0:5))
""")
            wait_for_idle(kc)
            execute(kc=kc, code='''\
%put null_var num_var num_arr_var logic_var logic_arr_var char_var char_arr_var mat_var list_var named_list_var recursive_var comp_var seri_var
%use sos
seri_var = list(seri_var)
''')
            wait_for_idle(kc)
            execute(kc=kc, code="%dict null_var num_var num_arr_var logic_var logic_arr_var char_var char_arr_var mat_var list_var named_list_var recursive_var comp_var seri_var")
            res = get_result(iopub)
            self.assertEqual(res['null_var'], None)
            self.assertEqual(res['num_var'], 123)
            self.assertEqual(res['num_arr_var'], [1,2,3])
            self.assertEqual(res['logic_var'], True)
            self.assertEqual(res['logic_arr_var'], [True, False, True])
            self.assertEqual(res['char_var'], '1"23')
            self.assertEqual(res['char_arr_var'], ['1', '2', '3'])
            self.assertEqual(res['list_var'], [1,2,'3'])
            self.assertEqual(res['named_list_var'], {'a': 1, 'b': 2, 'c': '3'})
            self.assertEqual(res['mat_var'].shape, (2,2))
            self.assertEqual(res['recursive_var'], {'a': 1, 'b': {'c': 3, 'd': 'whatever'}})
            self.assertEqual(res['comp_var'], 1+2j)
            self.assertEqual(res['seri_var'], [1,2,3,3,3,3])
            execute(kc=kc, code="%use sos")
            wait_for_idle(kc)


if __name__ == '__main__':
    unittest.main()
