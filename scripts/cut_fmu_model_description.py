from pathlib import Path
from typing import Union, List, Optional
from fmu_handler.fmu_adapter import FMUAdapter
import json
import io
import fnmatch


def _combine_components_and_params(elements: List):
    components_params = []
    for element in elements:
        for component, parameters in element.items():
            for parameter in parameters:
                components_params.append(f'{component}.{parameter}')
    return components_params


def _cut_fmu_model_description_with_positive_list(positive_list: List, negative_list: List, fmu: FMUAdapter)\
        -> FMUAdapter:
    positive_elements = _combine_components_and_params(positive_list)
    negative_elements = _combine_components_and_params(negative_list)
    for scalar_variable in fmu.model_description.model_variables.scalar_variables:
        delete = False
        for negative_element in negative_elements:
            if fnmatch.fnmatch(scalar_variable.name, negative_element):
                delete = True
        for positive_element in positive_elements:
            if fnmatch.fnmatch(scalar_variable.name, positive_element):
                delete = False
        if delete:
            fmu.remove_scalar_variable_by_name(name=scalar_variable.name)
    return fmu


def reduce_fmu_model_descriptions_in_directory(dir_path: Union[str, Path], output_suffix: Optional[str] = "reduced"):
    dir_path = Path(dir_path)
    if not dir_path.is_dir():
        raise NotADirectoryError(f"Path {dir_path} is not a directory.")

    if not output_suffix:
        output_suffix = ""
    elif not output_suffix.startswith("_"):
        output_suffix = f"_{output_suffix}"

    with open("./parameter_reduction_config.json", "r") as config_file:
        config_data = json.load(config_file)
        config_file.close()

    positive_list = config_data.get("keep_elements", [])
    negative_list = config_data.get("delete_elements", [])
    for fmu_file in dir_path.iterdir():
        if fmu_file.suffix == ".fmu":
            fmu = FMUAdapter(fmu_file=fmu_file)
            fmu = _cut_fmu_model_description_with_positive_list(
                positive_list=positive_list, negative_list=negative_list, fmu=fmu)
            fmu.save_fmu_copy(file_name=f"{fmu_file.stem}{output_suffix}", tar_dir_path=dir_path)


if __name__ == "__main__":
    reduce_fmu_model_descriptions_in_directory(dir_path="./")
