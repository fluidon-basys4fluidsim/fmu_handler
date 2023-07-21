from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Union, List

__all__ = [
    "ModelVariables", "FMUScalarVariable", "ModelExchange", "FMIModelDescription", "FMUSimulationType",
    "DefaultExperiment", "CoSimulation",
    "Causality", "Variability", "Initial", "FMUDataTypes", "FMUUnit",
]


class Causality(Enum):
    parameter = 0
    calculatedParameter = 1
    input = 2
    output = 3
    local = 4
    independent = 5


class Variability(Enum):
    constant = 0
    fixed = 1
    tunable = 2
    discrete = 3
    continuous = 4


class Initial(Enum):
    exact = 0
    approx = 1
    calculated = 2


class FMUDataTypes(Enum):
    real = 0
    integer = 1
    boolean = 2
    string = 3
    enumeration = 4


class FMUUnit(str):
    pass


@dataclass
class FMUScalarVariable:
    """
    ScalarVariable definitions according to FMI2.0 standard.
    Caution, some properties not yet included.
    All properties get default None for querieing the object
    # TODO some properties not yet included.

    """
    name: str = None
    value_reference: int = None
    causality: Causality = None
    data_type: FMUDataTypes = None
    variability: Variability = None
    description: Optional[str] = None
    initial: Optional[Initial] = None
    can_handle_multiple_set_per_time_instant: Optional[bool] = None
    # data_type attributes
    start: Optional[Union[str, float, bool, int, Enum]] = None
    unit: Optional[FMUUnit] = None


@dataclass
class ModelVariables:
    """
    Wrapper class that contains ScalarVariables and more according to FMI2.0 standard.

    """
    scalar_variables: List[FMUScalarVariable] = field(default_factory=list)


@dataclass
class CoSimulation:
    model_identifier: str
    needs_execution_tool: bool = False
    can_handle_variable_communication_step_size: bool = False
    can_interpolate_inputs: bool = False
    max_output_derivative_order: int = 0
    can_run_asynchronuously: bool = False
    can_be_instantiated_only_once_per_process: bool = False
    can_not_use_memory_management_functions: bool = False
    can_get_and_set_fmu_state: bool = False
    provides_directional_derivative: bool = False
    can_serialize_fmu_state: bool = False


@dataclass
class ModelExchange:
    pass


FMUSimulationType = Union[CoSimulation, ModelExchange]


@dataclass
class DefaultExperiment:
    start_time: Optional[float] = None
    stop_time: Optional[float] = None
    tolerance: Optional[float] = None
    step_size: Optional[float] = None


@dataclass
class FMIModelDescription:
    fmi_version: str
    model_name: str
    guid: str
    variable_naming_convention: str
    number_of_event_indicators: int

    model_variables: ModelVariables

    default_experiment: DefaultExperiment
    fmu_simulation_type: FMUSimulationType

    description: Optional[str] = None
    author: Optional[str] = None
    version: Optional[str] = None
    copyright: Optional[str] = None
    license: Optional[str] = None
    generation_tool: Optional[str] = None
    generation_date_and_time: Optional[str] = None
