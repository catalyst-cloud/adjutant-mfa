# Copyright (C) 2016 Catalyst IT Ltd
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

from setuptools import setup, find_packages

with open('requirements.txt') as f:
    required = f.readlines()

with open('README.rst') as file:
    long_description = file.read()

setup(
    name='adjutant-mfa',
    version='0.2.0',
    description='A plugin for Adjutant with MFA credential managment.',
    long_description=long_description,
    url='https://github.com/catalyst/adjutant-mfa',
    author='Amelia Cordwell',
    author_email='ameliacordwell@catalyst.net.nz',
    license='Apache 2.0',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: Apache Software License',
        'Framework :: Django :: 1.11',
        'Programming Language :: Python :: 2.7',
    ],
    keywords='mfa totp openstack task adjutant workflow',
    packages=find_packages(),
    install_requires=required,
)
