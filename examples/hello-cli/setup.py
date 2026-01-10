"""Setup configuration for Hello CLI."""

from setuptools import setup, find_packages
import os

# Read version from __init__.py
here = os.path.abspath(os.path.dirname(__file__))
about = {}
with open(os.path.join(here, 'hello_cli', '__init__.py'), 'r',
          encoding='utf-8') as f:
    for line in f:
        if line.startswith('__version__'):
            about['__version__'] = line.split('"')[1]
            break

# Read long description from README
long_description = ''
readme_path = os.path.join(here, 'README.md')
if os.path.exists(readme_path):
    with open(readme_path, 'r', encoding='utf-8') as f:
        long_description = f.read()

setup(
    name='hello-cli',
    version=about.get('__version__', '1.0.0'),
    description='A simple command-line tool example',
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='Kerrigan Example',
    author_email='example@kerrigan.dev',
    url='https://github.com/Kixantrix/kerrigan',
    packages=find_packages(exclude=['tests', 'tests.*']),
    install_requires=[
        'click>=8.0',
        'pyyaml>=6.0',
    ],
    entry_points={
        'console_scripts': [
            'hello=hello_cli.cli:main',
        ],
    },
    python_requires='>=3.8',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
    ],
)
