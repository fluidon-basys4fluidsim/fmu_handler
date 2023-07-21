from setuptools import setup, find_packages

with open('requirements.txt') as f:
    required = f.read().splitlines()

with open('README.md') as f:
    long_description = f.read()

setup(
    name='fmu_handler',
    version='0.1.0',
    author='Raphael Alt',
    author_email='Raphael.Alt@fluidon.com',
    license='MIT',
    description='Modules to handle Functional Mock-up Unit (FMU) files (".fmu").',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/fluidon-basys4fluidsim',
    packages=find_packages(),
    install_requires=required,
)
