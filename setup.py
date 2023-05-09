from setuptools import setup, find_packages

setup(
    name="bxh2bids",
    version="2.0",
    description="Convert Duke BIAC imaging data to BIDS",
    author="John Graner",
    author_email="john.graner@duke.edu",
    url="http://github.com/jlgraner/bxh2bids",
    install_requires=['xmltodict'],
    packages=find_packages(),
    entry_points={
        "console_scripts": [
            "bxh2bids=bxh2bids.cli:main",
        ]
    },
)
