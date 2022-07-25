# fmu_handler
Modules to handle Functional Mock-up Unit (FMU) files (".fmu").

The Module encapuslates reading and writing of ScalarVariables of the FMU modelDescription.xml.
Also, the modelDescription.xml gets validated against the fmi2ModelDescription.xsd schema.
Check out the ScalarVariable: class to see the currently supportet attributes.
Finally, a copy of the fmu can be saved.

Setup:
This module is part of the BaSys4FluidSim SDK.
From the SDK, it depends on the utils.utils.custom_logger.

Clone the module from the https://github.com/fluidon-basys4fluidsim repository.
Use pip install -e [module_path] or add the module to the sys.path:
import sys
sys.path.append(r"[module_path]")
