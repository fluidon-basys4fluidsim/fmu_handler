import unittest, logging
from pathlib import Path
from fmu_handler.fmu_adapter import FMUAdapter
from fmu_handler.fmu_types import *

# change debugging here
log = logging.getLogger("fmu_adapter")
log.setLevel(logging.INFO)

test_data_path = Path(__file__).parents[0].joinpath("test_data").absolute()


class TestFMUAdapter(unittest.TestCase):
    test_fmu_path = test_data_path.joinpath("Src_Test.fmu").absolute()
    tar_dir = test_data_path
    number_inputs = 3
    number_outputs = 4
    number_scalar_variables = 179

    def setUp(self):
        self.fmu = FMUAdapter(fmu_file=self.test_fmu_path)

    def tearDown(self) -> None:
        del self.fmu

    def test_query_scalar_variables(self):
        fmu = self.fmu

        query_scalar_variables = fmu.query_scalar_variables(query=FMUScalarVariable())
        self.assertEqual(len(query_scalar_variables), self.number_scalar_variables)

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
        print(fmu)

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

    def test_remove_scalar_variable_by_name(self):
        fmu = self.fmu
        for scalar_variable in fmu.query_scalar_variables().copy():
            fmu.remove_scalar_variable_by_name(name=scalar_variable.name)
        self.assertEqual(len(fmu.query_scalar_variables()), 0)
        file_name = fmu.save_fmu(file_name="deleted_parameter", tar_dir_path=self.tar_dir)
        with self.assertRaises(KeyError):
            FMUAdapter(fmu_file=file_name)
        file_name.unlink(missing_ok=False)

    def test_save_fmu_copy(self):
        fmu = self.fmu
        fmu.set_start_value(name="QAInput", value=69)
        file_name = fmu.save_fmu(file_name="dummy_fmu", tar_dir_path=self.tar_dir)
        fmu = FMUAdapter(fmu_file=file_name)
        self.assertEqual(69, fmu.get_scalar_variable_by_name(name="QAInput").start)
        file_name.unlink(missing_ok=False)


class TestOtherFMUs(unittest.TestCase):
    all_fmus = list()
    for file in test_data_path.iterdir():
        if file.suffix == ".fmu":
            all_fmus.append(file.absolute())

    def test_general_fmu_operations(self):
        for fmu_file in self.all_fmus:
            log.debug(fmu_file)
            fmu = FMUAdapter(fmu_file=fmu_file)
            log.debug(fmu.model_description)
            for scalar_variable in fmu.model_description.model_variables.scalar_variables:
                log.debug(scalar_variable)
