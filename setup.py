from setuptools import setup, Extension
import pybind11
import sys

cpp_args = ['-std=c++11']
if sys.platform == 'win32':
    cpp_args = ['/std:c++14'] # MSVC flag

ext_modules = [
    Extension(
        'novolang_core',
        sources=[
            'c++/src/scope.cpp',
            'c++/src/ast_exec.cpp',
            'c++/src/io.cpp',
            'c++/src/py_bind.cpp',
        ],
        include_dirs=[
            pybind11.get_include(),
            'c++/include'
        ],
        language='c++',
        extra_compile_args=cpp_args,
    ),
]

setup(
    name='novolang_core',
    version='0.1',
    ext_modules=ext_modules,
)
