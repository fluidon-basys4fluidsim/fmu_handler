# fmu_handler

The `fmu_handler` module provides functionality for handling Functional Mock-up Unit (FMU) files (".fmu").

This module encapsulates reading, deleting, and updating ScalarVariables in an FMU's `modelDescription.xml` file.
Additionally, it validates the `modelDescription.xml` against the `fmi2ModelDescription.xsd` schema.
Refer to the `ScalarVariable:` class to see the currently supported attributes. Lastly, the FMU can then be saved.

## Setup

Follow these steps to install and use the module:

1. Clone the module from the repository: [BaSy4FluidSim/fmu_handler](https://github.com/fluidon-basys4fluidsim)

2. Install the module with pip:

   ```bash
   pip install -e [module_path]
   ```

   Alternatively, you can add the module to your Python project or to the system path:

## Usage

The `fmu_handler` can be used for efficiently interacting with FMU files. Here's a simple example of how the module can be used:


```python
from fmu_handler.fmu_adapter import FMUAdapter

fmu = FMUAdapter("fmu_path")
variable = fmu.get_scalar_variable_by_name(name="Var1")
fmu.set_start_value(variable=variable.name, value=42)
fmu.save_fmu()
```

Additionally, there is function to reduce variables in the modelDescription.xml of FMUs in a folder.
For usage see [reduce_fmu_model_descriptions_parameters.py](scripts%2Freduce_fmu_model_descriptions_parameters.py).

## License

This module is under the MIT License. For more information, refer to the [LICENSE](LICENSE.txt) file.

For more information or assistance, please contact the project owner or use the contact details provided in this repository.
