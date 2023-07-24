# fmu_handler

The `fmu_handler` module provides functionality for handling Functional Mock-up Unit (FMU) files (".fmu").

This module encapsulates reading, deleting, and updating ScalarVariables in an FMU's `modelDescription.xml` file.
Additionally, it validates the `modelDescription.xml` against the `fmi2ModelDescription.xsd` schema.
Refer to the `ScalarVariable:` class to see the currently supported attributes. Lastly, the FMU can then be saved.

## Setup

Install the [BaSy4FluidSim/fmu_handler](https://github.com/fluidon-basys4fluidsim/fmu_handler)
repository (https://github.com/fluidon-basys4fluidsim/fmu_handler.git).

Direct installation via
```bash
pip install git+https://github.com/fluidon-basys4fluidsim/fmu_handler.git
```

or

clone and bind to project or make local installation with modifications.
```bash
pip install -e [local_repo_path]
```


## Usage

The `fmu_handler` can be used for efficiently interacting with FMU files.  
Here's a simple example of how the module can be used:


```python
from fmu_handler.fmu_adapter import FMUAdapter

fmu = FMUAdapter("fmu_path")
variable = fmu.get_scalar_variable_by_name(name="Var1")
fmu.set_start_value(variable=variable.name, value=42)
fmu.save_fmu()
```

Additionally, there is a function to reduce variables in the modelDescription.xml of FMUs in a folder:  
For usage from python IDE see [reduce_fmu_model_descr_pars.py](scripts%2Freduce_fmu_model_descr_pars.py).  
For usage from console see [reduce_fmu_model_descr_pars_console.py](scripts%2Freduce_fmu_model_descr_pars_console.py).


## License

This module is under the MIT License. For more information, refer to the [LICENSE](LICENSE.txt) file.

For more information or assistance, please contact the project owner or use the contact details provided in this repository.
