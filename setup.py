from setuptools import setup

pck_dir = {'bxh2bids': 'bxh2bids'}
pck_data = {
            'bxh2bids': ['info_field_files/*.json',
                         'Template_files/*.json'
                         ]
            }

setup(
    name="bxh2bids",
    version="2.0",
    description="Convert Duke BIAC imaging data to BIDS",
    author="John Graner",
    author_email="john.graner@duke.edu",
    url="http://github.com/jlgraner/bxh2bids",
    py_modules=['bxh_pick_fields'],
    install_requires=['xmltodict'],
    packages=['bxh2bids'],
    package_dir=pck_dir,
    package_data=pck_data
)
