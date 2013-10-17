from setuptools import setup, find_packages
import sys, os

version = '0.1'

setup(
	name='ckanext-utilities',
	version=version,
	description="Assorted command-line utitiles for Open Data",
	long_description="""\
	""",
	classifiers=[], # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
	keywords='',
	author='Ross Thompson',
	author_email='ross.thompson@statcan.gc.ca',
	url='http://data.gc.ca',
	license='MIT',
	packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
	namespace_packages=['ckanext', 'ckanext.utilities'],
	include_package_data=True,
	zip_safe=False,
	install_requires=[
		# -*- Extra requirements: -*-
	],
	entry_points=\
	"""
	[paste.paster_command]
	ckan_util=ckanext.utilities.commands:UtilCommand
        [ckan.plugins]
	# Add plugins here, eg
	# myplugin=ckanext.utilities:PluginClass
	""",
)
