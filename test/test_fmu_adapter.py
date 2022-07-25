import unittest
import os
from utils.utils.custom_logger import *
from fmu_handler.fmu_adapter import FMUAdapter
from fmu_handler.fmu_types import *

# change debugging here
log.setLevel(logging.INFO)

class TestFMUAdapter(unittest.TestCase):
    test_fmu_path = os.path.abspath(f"{os.path.dirname(__file__)}/test_data/Src_Test.fmu")
    tar_dir = os.path.abspath(f"{os.path.dirname(__file__)}/test_data")
    number_inputs = 3
    number_outputs = 4
    number_scalar_variabes = 179

    def setUp(self):
        self.fmu = FMUAdapter(fmu_file_path=self.test_fmu_path)

    def tearDown(self) -> None:
        del self.fmu

    def test_query_scalar_variables(self):
        fmu = self.fmu

        query_scalar_variables = fmu.query_scalar_variables(query=FMUScalarVariable())
        self.assertEqual(len(query_scalar_variables), self.number_scalar_variabes)

        query_inputs = fmu.query_scalar_variables(query=FMUScalarVariable(causality=Causality.input))
        self.assertEqual(len(query_inputs), self.number_inputs)

        query_outputs = fmu.query_scalar_variables(query=FMUScalarVariable(causality=Causality.output))
        self.assertEqual(len(query_outputs), self.number_outputs)

        query_name = fmu.query_scalar_variables(query=FMUScalarVariable(name="invalid_name"))
        self.assertEqual(query_name, list())

        query_name = fmu.query_scalar_variables(query=FMUScalarVariable(name="xCyl"))
        self.assertEqual(query_name[0].name, "xCyl")
        self.assertEqual(len(query_name), 1)

    def test_get_scalar_variable_by_name(self):
        fmu = self.fmu

        query_name = fmu.get_scalar_variable_by_name(name="xCyl")
        self.assertEqual(query_name.name, "xCyl")

        query_name = fmu.get_scalar_variable_by_name(name="invalid name")
        self.assertIsNone(query_name)

    def test_set_start_value(self):
        fmu = self.fmu

        fmu.set_start_value(name="QAInput", value=69)
        self.assertEqual(fmu.get_scalar_variable_by_name(name="QAInput").start, 69)

        with self.assertRaises(KeyError):
            fmu.set_start_value(name="xCyl", value=69)

    def test_save_fmu_copy(self):
        fmu = self.fmu

        self.test_set_start_value()
        file_name = fmu.save_fmu_copy(file_name="dummy_fmu", tar_dir_path=self.tar_dir)

        fmu = FMUAdapter(fmu_file_path=file_name)
        self.assertEqual(fmu.get_scalar_variable_by_name(name="QAInput").start, str(69))

        # TODO check how to close the file before removing
        os.remove(path=r"D:\01_Git\01_BaSys4FluidSim\fmu_handler\test\test_data\dummy_fmu.fmu")
