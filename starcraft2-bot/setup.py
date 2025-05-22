from setuptools import setup, find_packages

setup(
    name="starcraft2-bot",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "ares-sc2",
        "sc2",
        "loguru",
    ],
    entry_points={
        "console_scripts": [
            "starcraft2-bot=run:main",
        ],
    },
)