from setuptools import setup, find_packages

setup(
    name="task-tracker",
    version="1.0.0",
    description="A CLI task management tool demonstrating Kerrigan M3/M4 features",
    author="Kerrigan Agent System",
    packages=find_packages(),
    install_requires=[
        "click>=8.0.0",
    ],
    entry_points={
        "console_scripts": [
            "task-tracker=task_tracker.cli:cli",
        ],
    },
    python_requires=">=3.8",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
)
