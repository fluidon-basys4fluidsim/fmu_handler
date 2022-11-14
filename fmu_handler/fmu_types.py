from dataclasses import dataclass
from enum import Enum
from typing import Optional, Union

__all__ = [
    "FMUScalarVariable", "Causality", "Variability", "Initial", "FMUDataTypes", "FMUUnit", "ModelVariables"
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

    # TODO some properties not yet included.
    # TODO describe variables.
    """
    name: Optional[str] = None
    data_type: Optional[FMUDataTypes] = None
    value_reference: Optional[int] = None
    start: Optional[Union[str, float, bool, int, Enum]] = None
    causality: Optional[Causality] = None
    initial: Optional[Initial] = None
    unit: Optional[FMUUnit] = None
    description: Optional[str] = None


class ModelVariables:
    """
    Wrapper class that contains ScalarVariables and more according to FMI2.0 standard.

    """
    def __init__(self):
        self.scalar_variables: list[FMUScalarVariable] = []
