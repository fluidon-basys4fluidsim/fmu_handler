from typing import Union, Optional
from enum import Enum
from zipfile import ZipFile, ZIP_DEFLATED
from pathlib import Path
from utils.custom_logger import *
import lxml.etree
from fmu_handler.fmu_types import *
from lxml import etree

__all__ = [
    "FMUAdapter"
]

log = get_logger("FMU_Handler")


class FMUAdapter:
    """
    Helper class to handle the modelDescriptionParameter of an FMU with the following fuctions:
    - Query all FMU ScalarVariables
    - Set start value of FMU
    - Save a new copy of the FMU with the updated parameters

    """

    def __init__(self, fmu_file_path: Union[Path, str]):
        """
        Instantiates an fmu that is defined by the fmu_file_path.

        :param fmu_file_path: Specifies the path of the fmu. Absolute path is recommended.
        :return:
        """
        self._fmu_path = Path(fmu_file_path).absolute()
        if not self._fmu_path.is_file():
            raise FileNotFoundError(f"FMU could not found: {self._fmu_path.as_posix()}")
        self._model_variables: ModelVariables = ModelVariables()
        self._fmu_xml: etree._ElementTree = None
        self._fmu_tree: etree._Element = None

        self._fmu_xml, self._fmu_tree = self.__load_fmu(fmu_file_path=self._fmu_path)
        schema_validation = self.__validate_fmu(fmu_xml=self._fmu_xml)
        self.__parse_fmu(fmu_tree=self._fmu_tree)

    def __load_fmu(self, fmu_file_path: Path) -> (lxml.etree._ElementTree, lxml.etree._Element):
        """
        Loads fmu file and initializes the xml data (fmu_xml) and the xml tree (fmu_tree).
        If no fmu file is found, FileNotFoundError is raised.

        :param fmu_file_path: Specifies the path of the fmu. Absolute path is recommended.
        :return: fmu_xml: ElementTree Object, root if the ElementTree, containing _Element
        """
        if fmu_file_path:
            with ZipFile(fmu_file_path, "r") as archive:
                with archive.open("modelDescription.xml") as description:
                    fmu_xml = etree.parse(source=description)
            fmu_tree = fmu_xml.getroot()
        else:
            raise FileNotFoundError(f"Fmu_path was not set.")

        return fmu_xml, fmu_tree

    def __validate_fmu(self, fmu_xml: lxml.etree._ElementTree) -> bool:
        """
        Validation against the fmi2ModelDescription.xsd schema.
        If validation failed, only a log info is transmitted.

        :param fmu_xml: xml Description as _ElementTree to be validated.
        :return: True if validation succeeded. False, if not.
        """

        schema_path = Path(__file__).parents[1].joinpath("data", "schema", "fmi2ModelDescription.xsd")
        xml_schema = None
        try:
            xml_schema = etree.XMLSchema(etree.parse(source=schema_path))
            if xml_schema.validate(fmu_xml):
                return True
            else:
                log.info(f"fmi2ModelDescription.xsd schema validation failed.")

        except Exception:
            log.error(f"Could not parse {schema_path}.")

        return False

    def __parse_fmu(self, fmu_tree: lxml.etree._Element):
        """
        Parsing the xml structure into a List of ScalarVariable Objects for better handling.

        :return:
        """

        variables = list()
        xml_variables = fmu_tree.findall("ModelVariables//ScalarVariable")

        for index, variable in enumerate(xml_variables):
            name = variable.get("name")
            value_reference = int(variable.get("valueReference"))
            var = variable.get("causality")
            causality = Causality[var] if var else None
            var = variable.get("initial")
            initial = Initial[var] if var else None
            data_type = variable[0].tag
            var = variable[0].get("start")
            if data_type == FMUDataTypes.Real:
                start = float(var) if var else None
            elif data_type == FMUDataTypes.Integer:
                start = int(var) if var else None
            elif data_type == FMUDataTypes.Boolean:
                start = bool(var) if var else None
            else:  # enum and string are considered equally here.
                start = str(var) if var else None
            unit = variable.get("unit")
            description = variable.get("description")
            can_handle_multiple_set_per_time_instant = variable.get("canHandleMultipleSetPerTimeInstant")
            prefix = variable.get("valueReference")
            range = variable.get("range")

            scalar_variable = FMUScalarVariable(
                name=name,
                start=start,
                value_reference=value_reference,
                causality=causality,
                initial=initial,
                data_type=data_type,
                unit=unit,
                description=description,
            )

            log.debug(f"{index}: scalar variable added: {scalar_variable}")
            variables.append(scalar_variable)

        self._model_variables.scalar_variables = variables

    def query_scalar_variables(self, query: FMUScalarVariable) -> list[FMUScalarVariable]:
        """
        Returns a list of all ScalarVariable that match the query request. Not queried attributes should be set None.
        If no ScalarVariable was found, list is returned empty.

        :param query: Defines parameter of attributes that should be queried.
        :return: A list of ScalarVariables that matches the query request.
        """
        variables = []

        for element in self._model_variables.scalar_variables:
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

    def get_scalar_variable_by_name(self, name: str) -> Optional[FMUScalarVariable]:
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

    def set_start_value(self, name: str, value: Union[str, float, bool, int, Enum]):
        """
        This method encapsulates setting the staring value using __set_scalar_variable_by_name().

        :param name: Name of the desired ScalarVariable, of which the start value should be edited.
        :param value: Start value to be set.
        :return:
        """
        self.__set_scalar_variable_by_name(set_values=FMUScalarVariable(name=name, start=value))

    def __update_xml_model_description_by_name(self, name: str):
        """
        Updates a single ScalarVariable from the fmu object in the xml model description (_fmu_tree).
        The updated ScalarVariable is defined by its name.

        :param name: Defines the ScalarVariable, which should be updated in the _fmu_tree.
        :return:
        """
        variable = self.get_scalar_variable_by_name(name=name)
        element = self._fmu_tree.find(f"ModelVariables//ScalarVariable[@name='{name}']")

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
            element[0].tag = str(variable.data_type)
        if variable.start is not None:
            element[0].attrib["start"] = str(variable.start)

    def __update_xml_model_description(self):
        """
        Updates the entire fmu object to the xml model description (_fmu_tree).

        :return:
        """
        for variable in self._model_variables.scalar_variables:
            self.__update_xml_model_description_by_name(name=variable.name)

    def save_fmu_copy(self, tar_dir_path: Union[Path, str], file_name: Optional[Union[Path, str]] = None) -> Path:
        """
        Saves a copy from the original fmu into the defined target directory including the updated modelDescription.xml
        of the current fmu instance.

        :param tar_dir_path: Target directory where the new fmu should be stored.
        :param file_name: Fmu name can be specified optionally. Can be passed with or without suffix ".fmu".
        If not specified, the name of the original fmu is taken.
        :return: Full file name including path of the generated fmu.
        """
        # copy, edit, write fmu because files inside an archive cannot simply be changed.
        # if no name is given, the original name is taken

        if file_name:
            file_name = Path(file_name)
        else:
            file_name = self._fmu_path
        if file_name.suffix == "":
            file_name = file_name.with_suffix(suffix=".fmu")

        tar_file_path = Path.joinpath(Path(tar_dir_path).absolute(), file_name)

        # update tree and generate modelDescription.xml
        self.__update_xml_model_description()
        new_model_description_xml = etree.tostring(self._fmu_tree, encoding="UTF-8", xml_declaration=True)

        # copy fmu and insert new modelDescription.xml
        with ZipFile(self._fmu_path, 'r') as zip_in:
            with ZipFile(tar_file_path, 'w', compression=ZIP_DEFLATED) as zip_out:
                for item in zip_in.infolist():
                    buffer = zip_in.read(item.filename)
                    # copy all other files except for the modelDescription.xml
                    if item.filename != 'modelDescription.xml':
                        zip_out.writestr(item, buffer)
                del buffer
                del item
                # write new customized modelDescription.xml
                zip_out.writestr(zinfo_or_arcname="modelDescription.xml", data=new_model_description_xml)
        log.info(f"New fmu generated: {tar_file_path}")

        return tar_file_path
