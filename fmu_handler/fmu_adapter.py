import io, sys, enum, logging
from typing import Union, Optional, List
from zipfile import ZipFile, ZIP_DEFLATED
from pathlib import Path
from lxml import etree

from .fmu_types import *

__all__ = [
    "FMUAdapter"
]

log_config: dict = {
    "log_level": "INFO",
    "format": "%(asctime)s [%(levelname)s] [%(module)s] [%(funcName)s] - %(message)s",
    "datefmt": '%y-%m-%d %H:%M:%S',
    "stream": sys.stdout,
}
log = logging.getLogger("fmu_handler")
log.setLevel(log_config["log_level"])
handler = logging.StreamHandler(log_config['stream'])
formatter = logging.Formatter(log_config['format'], datefmt=log_config['datefmt'])
handler.setFormatter(formatter)
log.addHandler(handler)


class FMUAdapter:
    """
    Helper class to handle the modelDescriptionParameter of an FMU with the following fuctions:
    - Query for defined FMUScalarVariables
    - Set start value of FMUScalarVariable
    - Remove FMUScalarVariables
    - Save a new fmu file with the updated parameters
    """
    model_description: FMIModelDescription
    _file_name: Path
    _data: io.BytesIO
    _fmu_xml: etree._ElementTree
    _fmu_tree: etree._Element
    _scalar_variables_to_be_removed: List[str] = []

    def __init__(self, fmu_file: Optional[Union[Path, str]] = None, data: Optional[io.BytesIO] = None,
                 file_name: Optional[Union[Path, str]] = None):
        """
        Instantiates a fmu that is defined by the fmu_file_path.

        :param fmu_file: Specifies the path of the fmu. Absolute path is recommended. If provided,
        data and file_name are not considered.
        :param data: Specifies the data of the fmu. If provided, file_name must also be provided.
        :param file_name: Specifies the name of the fmu.
        :return: None
        """
        self._scalar_variables_to_be_removed = []

        if fmu_file is not None:
            self._file_name = Path(fmu_file).absolute()
            if not self._file_name.is_file():
                raise FileNotFoundError(f"FMU could not be found: {self._file_name.as_posix()}")
            with open(file=self._file_name, mode="rb") as file:
                self._data = io.BytesIO(file.read())
        elif data is not None and file_name is not None:
            self._file_name = Path(file_name).absolute()
            if isinstance(data, io.BytesIO):
                self._data = data
            else:
                raise TypeError(f"Data must be of type io.BytesIO.")
        else:
            raise FileNotFoundError(f"No valid input initialization parameter for fmu initialization.")

        self.__load_fmu_data()
        self.__parse_fmu_model_description()

    def __load_fmu_data(self):
        """
        Loads fmu file and initializes the xml data (fmu_xml) and the xml tree (fmu_tree).

        :return:
        """
        if self._data:
            with ZipFile(file=self._data, mode="r") as archive:
                with archive.open("modelDescription.xml") as description:
                    fmu_xml = etree.parse(source=description)
            fmu_tree = fmu_xml.getroot()
        else:
            raise FileNotFoundError(f"Fmu_path was not set.")
        self._fmu_xml = fmu_xml
        self._fmu_tree = fmu_tree

    def __validate_fmu(self) -> bool:
        """
        Validation against the fmi2ModelDescription.xsd schema.

        :return: True if validation succeeded. False, if not.
        """
        schema_path = Path(__file__).parents[1].joinpath("data", "schema", "fmi2ModelDescription.xsd")
        xml_schema = None
        try:
            xml_schema = etree.XMLSchema(etree.parse(source=schema_path))
            if xml_schema.validate(self._fmu_xml):
                return True
            else:
                log.warning(f"fmi2ModelDescription.xsd schema validation failed.")

        except Exception:
            raise ValueError(f"Could not parse {schema_path} modelDescription xml of {self._file_name}.")

        return False

    def __parse_fmu_default_experiment_parameter(self) -> DefaultExperiment:
        """
        Parses the DefaultExperiment parameters of the FMU modelDescription.xml.

        :return: DefaultExperiment object
        """
        xml_node = self._fmu_tree.find("DefaultExperiment")
        if xml_node is not None:
            start_time = float(xml_node.get("startTime")) if "startTime" in xml_node.attrib else None
            stop_time = float(xml_node.get("stopTime")) if "stopTime" in xml_node.attrib else None
            tolerance = float(xml_node.get("tolerance")) if "tolerance" in xml_node.attrib else None
            step_size = float(xml_node.get("stepSize")) if "stepSize" in xml_node.attrib else None
            default_experiment = DefaultExperiment(start_time=start_time,
                                                   stop_time=stop_time,
                                                   tolerance=tolerance,
                                                   step_size=step_size)
        else:
            raise KeyError("Could not find DefaultExperiment parameters in FMU modelDescription.xml.")
        return default_experiment

    def __parse_fmu_simulation_type(self) -> Union[CoSimulation, ModelExchange]:
        """
        Parses FMU parameters that define the simulation type relevant for simulation master.

        :return: CoSimulation or ModelExchange parameter object
        """
        # CoSimulation
        simulation_type = None
        if self._fmu_tree.find("CoSimulation") is not None:
            xml_node = self._fmu_tree.find("CoSimulation")
            simulation_type = \
                CoSimulation(model_identifier=xml_node.get("modelIdentifier"),
                             needs_execution_tool=(xml_node.get("needsExecutionTool") == "true"),
                             can_handle_variable_communication_step_size=(xml_node.get(
                                 "canHandleVariableCommunicationStepSize") == "true"),
                             can_interpolate_inputs=(xml_node.get("canInterpolateInputs") == "true"),
                             max_output_derivative_order=xml_node.get("maxOutputDerivativeOrder"),
                             can_run_asynchronuously=(xml_node.get("canRunAsynchronuously") == "true"),
                             can_be_instantiated_only_once_per_process=(xml_node.get(
                                 "canBeInstantiatedOnlyOncePerProcess") == "true"),
                             can_not_use_memory_management_functions=(xml_node.get(
                                 "canNotUseMemoryManagementFunctions") == "true"),
                             can_get_and_set_fmu_state=(xml_node.get("canGetAndSetFMUstate") == "true"),
                             provides_directional_derivative=(xml_node.get("providesDirectionalDerivative") == "true"),
                             can_serialize_fmu_state=(xml_node.get("canSerializeFMUstate") == "true"))

        elif self._fmu_tree.find("ModelExchange") is not None:
            # TODO Model exchange
            raise NotImplementedError("Parsing ModelExchange is not implemented.")
        else:
            raise KeyError("Could not find CoSimulation parameters in FMU modelDescription.xml.")

        return simulation_type

    def __parse_fmu_scalar_variables(self, fmu_tree: etree._Element) -> List[FMUScalarVariable]:
        """
        Parses all scalar variables of the FMU.

        :param fmu_tree: xml tree of the FMU.
        :return: List of FMUScalarVariable objects.
        """
        variables = list()
        xml_variables = fmu_tree.findall("ModelVariables//ScalarVariable")
        if xml_variables:
            for index, variable in enumerate(xml_variables):
                name = variable.get("name")
                value_reference = int(variable.get("valueReference"))
                var = variable.get("causality")
                causality = Causality[var] if var is not None else None
                var = variable.get("initial")
                initial = Initial[var] if var is not None else None
                data_type = variable[0].tag
                var = variable[0].get("start")
                if data_type == "Real":
                    start = float(var) if var is not None else None
                    data_type = FMUDataTypes.real
                elif data_type == "Integer":
                    start = int(var) if var is not None else None
                    data_type = FMUDataTypes.integer
                elif data_type == "Boolean":
                    start = bool(var) if var is not None else None
                    data_type = FMUDataTypes.boolean
                elif data_type == "Enumeration":
                    # enum and string are considered equally here.
                    start = str(var) if var is not None else None
                    data_type = FMUDataTypes.enumeration
                else:
                    start = str(var) if var is not None else None
                    data_type = FMUDataTypes.string
                unit = variable.get("unit")
                description = variable.get("description")
                can_handle_multiple_set_per_time_instant = variable.get("canHandleMultipleSetPerTimeInstant")

                scalar_variable = FMUScalarVariable(
                    name=name,
                    start=start,
                    value_reference=value_reference,
                    causality=causality,
                    initial=initial,
                    data_type=data_type,
                    unit=unit,
                    description=description,
                    can_handle_multiple_set_per_time_instant=can_handle_multiple_set_per_time_instant
                )

                log.debug(f"{index}: scalar variable added: {scalar_variable}")
                variables.append(scalar_variable)
        else:
            raise KeyError("Could not find FMUScalarVariable parameters in FMU modelDescription.xml.")

        return variables

    def __parse_fmu_model_description(self):
        """
        Parsing the xml modelDescription.xml into an object for better handling.

        :return:
        """
        if self._fmu_tree is not None:
            fmu_tree = self._fmu_tree
            self.model_description = \
                FMIModelDescription(fmi_version=fmu_tree.get("fmiVersion"),
                                    model_name=fmu_tree.get("modelName"),
                                    guid=fmu_tree.get("guid"),
                                    variable_naming_convention=fmu_tree.get("variableNamingConvention"),
                                    number_of_event_indicators=fmu_tree.get("numberOfEventIndicators"),
                                    model_variables=ModelVariables(scalar_variables=
                                    self.__parse_fmu_scalar_variables(fmu_tree=fmu_tree)),
                                    default_experiment=self.__parse_fmu_default_experiment_parameter(),
                                    fmu_simulation_type=self.__parse_fmu_simulation_type(),
                                    description=fmu_tree.get("description"),
                                    author=fmu_tree.get("author"),
                                    version=fmu_tree.get("version"),
                                    copyright=fmu_tree.get("copyright"),
                                    license=fmu_tree.get("license"),
                                    generation_tool=fmu_tree.get("generationTool"),
                                    generation_date_and_time=fmu_tree.get("generationDateAndTime"))
        else:
            raise KeyError("Could not parse modelDescription parameters from FMU modelDescription.xml.")

    def query_scalar_variables(self, query: Optional[FMUScalarVariable] = None) -> list[FMUScalarVariable]:
        """
        Returns a list of all ScalarVariable that match the query request. Not queried attributes should be set None.
        If no ScalarVariable was found, list is returned empty.

        :param query: Defines parameter of attributes that should be queried.
        :return: A list of ScalarVariables that matches the query request.
        """
        if query is None:
            return self.model_description.model_variables.scalar_variables

        variables = []
        for element in self.model_description.model_variables.scalar_variables:
            if query is not None:
                if query.name and not element.name == query.name:
                    continue
                if query.value_reference and not element.value_reference == query.value_reference:
                    continue
                if query.causality and not element.causality == query.causality:
                    continue
                if query.initial and not element.initial == query.initial:
                    continue
                if query.data_type and not element.data_type == query.data_type:
                    continue
                if query.unit and not element.unit == query.unit:
                    continue
                if query.description and not element.description == query.description:
                    continue
                if query.start and not element.start == query.start:
                    continue

            variables.append(element)
        return variables

    def get_scalar_variable_by_name(self, name: Optional[str] = None) -> Optional[FMUScalarVariable]:
        """
        Returns a ScalarVariable that match the queried name.

        :param name: Name of the requested ScalarVariable.
        :return: ScalarVariable that matches the query request.
        None is returned if none or multiple ScalarVariables were found.
        """

        variable = self.query_scalar_variables(FMUScalarVariable(name=name))
        if len(variable) == 0:
            log.debug(f"No variable found")
            return None
        elif len(variable) > 1:
            log.debug(f"Some variables have the same name.")
            return None
        return variable[0]

    def __set_scalar_variable_by_name(self, set_values: FMUScalarVariable):
        """
        This method updates the values of an internal ScalarVariable.

        To select the target ScalarVariable, setting the name of set_values: FMUScalarVariable is mandatory,
        otherwise this method returns None.
        If the method does not find a corresponding ScalarVariable name, a KeyError is being raised.
        All additional parameters which are set, are being updated.
        Caution, only tags and attributes, which are present in the initial modelDescription.xml can be updated.
        Otherwise, a KeyError is being raised.

        :param set_values: Values encapsulated in a FMUScalarVariable that should be set.
        :return:
        """
        if not set_values.name:
            log.debug(f"No name was defined to set variables.")
            return None

        variable = self.get_scalar_variable_by_name(name=set_values.name)
        if variable is None:
            raise KeyError(f"Scalar variable {set_values.name} not found. Values could not be set.")

        if set_values.causality is not None:
            if variable.causality is not None:
                variable.causality = set_values.causality
            else:
                raise KeyError(f"Desired attribute is not set in original fmu. Value could not be set.")
        if set_values.unit is not None:
            if variable.unit is not None:
                variable.unit = set_values.unit
            else:
                raise KeyError(f"Desired attribute is not set in original fmu. Value could not be set.")
        if set_values.start is not None:
            if variable.start is not None:
                variable.start = set_values.start
            else:
                raise KeyError(f"Desired attribute is not set in original fmu. Value could not be set.")
        if set_values.data_type is not None:
            if variable.data_type is not None:
                variable.data_type = set_values.data_type
            else:
                raise KeyError(f"Desired attribute is not set in original fmu. Value could not be set.")
        if set_values.initial is not None:
            if variable.initial is not None:
                variable.initial = set_values.initial
            else:
                raise KeyError(f"Desired attribute is not set in original fmu. Value could not be set.")
        if set_values.description is not None:
            if variable.description is not None:
                variable.description = set_values.description
            else:
                raise KeyError(f"Desired attribute is not set in original fmu. Value could not be set.")
        if set_values.value_reference is not None:
            if variable.value_reference is not None:
                variable.value_reference = set_values.value_reference
            else:
                raise KeyError(f"Desired attribute is not set in original fmu. Value could not be set.")

    def set_start_value(self, name: str, value: Union[str, float, bool, int, enum.Enum]):
        """
        This method encapsulates setting the staring value using __set_scalar_variable_by_name().

        :param name: Name of the desired ScalarVariable, of which the start value should be edited.
        :param value: Start value to be set.
        :return:
        """
        self.__set_scalar_variable_by_name(set_values=FMUScalarVariable(name=name, start=value))

    def __update_xml_model_description_scalar_variable(self, variable: FMUScalarVariable):
        """
        Updates a single ScalarVariable from the fmu object in the xml model description (_fmu_tree).
        The updated ScalarVariable is defined by its name.

        :param variable: The ScalarVariable, which should be updated in the _fmu_tree.
        :return: None
        """
        element = self._fmu_tree.find(f"ModelVariables//ScalarVariable[@name='{variable.name}']")

        # setting attributes
        if variable.causality is not None:
            element.attrib["causality"] = variable.causality.name
        if variable.unit is not None:
            element.attrib["unit"] = str(variable.unit)
        if variable.initial is not None:
            element.attrib["initial"] = variable.initial.name
        if variable.description is not None:
            element.attrib["description"] = str(variable.description)
        if variable.value_reference is not None:
            element.attrib["valueReference"] = str(variable.value_reference)

        # setting the value tag and its attribute
        if variable.data_type is not None:
            if variable.data_type == FMUDataTypes.real:
                data_type = "Real"
            elif variable.data_type == FMUDataTypes.integer:
                data_type = "Integer"
            elif variable.data_type == FMUDataTypes.boolean:
                data_type = "Boolean"
            elif variable.data_type == FMUDataTypes.enumeration:
                data_type = "Enumeration"
            elif variable.data_type == FMUDataTypes.string:
                data_type = "String"
            else:
                raise TypeError(f"Datatype could not be parsed.")
            element[0].tag = str(data_type)

        if variable.start is not None:
            element[0].attrib["start"] = str(variable.start)

    def __update_xml_model_description(self):
        """
        Updates the entire fmu object to the xml model description (_fmu_tree).

        :return:
        """
        # remove all variables, which are marked for removal
        while self._scalar_variables_to_be_removed:
            remove_var = self._scalar_variables_to_be_removed.pop()
            self.__remove_xml_variable_by_name(name=remove_var)
            log.debug("Removed variable %s from xml model description.", remove_var)

        # update all variables, which are remaining
        for variable in self.model_description.model_variables.scalar_variables:
            self.__update_xml_model_description_scalar_variable(variable=variable)
            log.debug("Updated variable %s in xml model description.", variable.name)

    def __remove_xml_variable_by_name(self, name: str):
        """
        Deletes a ScalarVariable from the fmu object in the xml model description (_fmu_tree).
        The deleted ScalarVariable is defined by its name.

        :param name: Defines the ScalarVariable, which should be deleted in the _fmu_tree.
        :return:
        """
        element = self._fmu_tree.find(f"ModelVariables//ScalarVariable[@name='{name}']")
        element.getparent().remove(element)

    def remove_scalar_variable_by_name(self, name: str):
        """
        This method encapsulates deleting the ScalarVariable from the internal structure.

        :param name: Name of the desired ScalarVariable, which should be deleted.
        :return:
        """
        variable = self.get_scalar_variable_by_name(name=name)
        if variable is None:
            raise KeyError(f"ScalarVariable with name '{name}' could not be found.")
        else:
            self._scalar_variables_to_be_removed.append(variable.name)
            self.model_description.model_variables.scalar_variables.remove(variable)

    def get_zip_file_bytes_io(self) -> io.BytesIO:
        """
        Returns the fmu as a BytesIO object.

        :return: fmu as a BytesIO object.
        """
        # copy, edit, write fmu because files inside an archive cannot simply be changed.

        # update tree and generate modelDescription.xml
        self.__update_xml_model_description()
        new_model_description_xml = etree.tostring(self._fmu_tree, encoding="UTF-8", xml_declaration=True)

        # copy fmu and insert new modelDescription.xml
        io_file_container = io.BytesIO()
        with ZipFile(file=self._data, mode='r') as zip_in:
            with ZipFile(file=io_file_container, mode='w', compression=ZIP_DEFLATED) as zip_out:
                for item in zip_in.infolist():
                    buffer = zip_in.read(item.filename)
                    # copy all other files except for the modelDescription.xml
                    if item.filename != 'modelDescription.xml':
                        zip_out.writestr(item, buffer)
                del buffer
                del item
                # write new customized modelDescription.xml
                zip_out.writestr(zinfo_or_arcname="modelDescription.xml", data=new_model_description_xml)

        self._data = io_file_container
        return self._data

    def save_fmu(self, tar_dir_path: Union[Path, str], file_name: Optional[Union[Path, str]] = None) -> Path:
        """
        Saves a copy from the original fmu into the defined target directory including the updated modelDescription.xml
        of the current fmu instance.

        :param tar_dir_path: Target directory where the new fmu should be stored.
        :param file_name: FMU name can be specified optionally. Can be passed with or without suffix ".fmu".
        If not specified, the name of the original fmu is taken.
        :return: Full file name including path of the generated fmu.
        """
        # copy, edit, write fmu because files inside an archive cannot simply be changed.
        dir_path = Path(tar_dir_path)
        dir_path.mkdir(parents=False, exist_ok=True)
        if file_name is None:
            file_name = Path(self._file_name.name).with_suffix(".fmu")
        else:
            file_name = Path(file_name)
            file_name = file_name.with_suffix(".fmu")
        full_path = dir_path.joinpath(file_name)

        # update tree and generate modelDescription.xml
        self.get_zip_file_bytes_io()
        with open(file=full_path, mode="wb") as f:
            f.write(self._data.getbuffer())

        if not full_path.is_file():
            raise FileExistsError(f"File was not saved to {str(full_path)}")

        log.debug(f"File saved to {str(full_path)}.")
        log.info(f"Fmu {self._file_name.name} saved to {full_path}.")

        return full_path
