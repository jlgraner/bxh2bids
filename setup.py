from setuptools import setup

pck_data = {
            'bxh2bids': ['info_field_files/*.json',
                         'Template_files/*.json',
                         'Documentation/*.md'
                         ]
            }

setup(
    name="bxh2bids",
    version="1.0",
    description="Convert Duke BIAC imaging data to BIDS",
    author="John Graner",
    author_email="john.graner@duke.edu",
    url="http://github.com/jlgraner/bxh2bids",
    py_modules=['bxh2bids', 'bxh_pick_fields'],
    install_requires=['xmltodict'],
    package_data=pck_data
)
