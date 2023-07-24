import json
import fnmatch
from pathlib import Path
from typing import Union, List, Optional
from fmu_handler.fmu_adapter import FMUAdapter, log
from fmu_handler.fmu_types import FMUScalarVariable, Causality

__all__ = [
    "reduce_fmu_model_descriptions_in_directory"
]


def _cut_fmu_model_description_with_lists(keep_list: List, delete_list: List, fmu: FMUAdapter)\
        -> FMUAdapter:
    """
    Function to delete defined elements.

    Generally, all elements are selected not to be deleted.
    First, all elements that fit to the delete_list are tagged to be deleted.
    Then, elements to be kept might untag those again.
    Finally, all tagged scalar variables are deleted from the fmu model description xml.

    :param keep_list: Elements that should be kept.
    :param delete_list: Elements that should be deleted.
    :param fmu: FMUAdapter object.
    :return:
    """
    for scalar_variable in fmu.query_scalar_variables(query=FMUScalarVariable(causality=Causality.parameter)):
        delete = False
        for negative_element in delete_list:
            if fnmatch.fnmatch(scalar_variable.name, negative_element):
                delete = True
        for positive_element in keep_list:
            if fnmatch.fnmatch(scalar_variable.name, positive_element):
                delete = False
        if delete:
            fmu.remove_scalar_variable_by_name(name=scalar_variable.name)
    return fmu


def reduce_fmu_model_descriptions_in_directory(fmu_dir: Union[str, Path],
                                               output_dir: Optional[Union[str, Path]] = None,
                                               output_suffix: Optional[str] = None):
    """
    According to the parameter_reduction_config.json file in the directory, the model description of all fmus in this
    directory are reduced.

    :param fmu_dir: Path to the directory containing the fmus.
    :param output_dir: If None, the reduced fmus are saved and possibly overwritten
    in the same directory as the original ones.
    :param output_suffix: If None, the reduced fmus are saved and possibly overwritten. Otherwise, the suffix is added
    to the modified fmu files.
    :return:
    """
    fmu_dir = Path(fmu_dir)
    if not fmu_dir.is_dir():
        raise NotADirectoryError(f"Path {fmu_dir} is not a directory.")

    if not output_suffix:
        output_suffix = ""
    elif not output_suffix.startswith("_"):
        output_suffix = f"_{output_suffix}"

    with open(fmu_dir.joinpath("parameter_reduction_config.json"), "r") as config_file:
        config_data = json.load(config_file)
        config_file.close()

    keep_list = config_data.get("keep_elements", [])
    delete_list = config_data.get("delete_elements", [])

    log.info(f"Reducing fmu model descriptions in {fmu_dir}.")

    for fmu_file in fmu_dir.iterdir():
        if fmu_file.suffix == ".fmu":
            fmu = FMUAdapter(fmu_file=fmu_file)
            fmu = _cut_fmu_model_description_with_lists(
                keep_list=keep_list, delete_list=delete_list, fmu=fmu
            )

            if output_dir is not None:
                save_dir_path = Path(output_dir).absolute()
                save_dir_path.mkdir(exist_ok=True, parents=True)
            else:
                save_dir_path = fmu_dir

            fmu.save_fmu(file_name=f"{fmu_file.stem}{output_suffix}", tar_dir_path=save_dir_path)


