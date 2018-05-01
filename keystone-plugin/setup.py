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

with open('README.rst') as file:
    long_description = file.read()

setup(
    name='keystone-adjutant-mfa',
    version='0.3.0',
    description='An auth plugin for Keystone with password+totp support.',
    long_description=long_description,
    url='https://github.com/catalyst-cloud/adjutant-mfa',
    author='Adrian Turjak',
    author_email='adriant@catalyst.net.nz',
    license='Apache 2.0',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 2.7',
    ],
    keywords='keystone auth mfa totp openstack',
    packages=find_packages(),
    entry_points={
        'keystone.auth.password': [
            'mitaka.password_totp = keystone_mfa.mitaka.password_totp:PasswordTOTP',
            'newton.password_totp = keystone_mfa.newton.password_totp:PasswordTOTP',
            'ocata.password_totp = keystone_mfa.ocata.password_totp:PasswordTOTP',
            'pike.password_totp = keystone_mfa.pike.password_totp:PasswordTOTP',
            'queens.password_totp = keystone_mfa.queens.password_totp:PasswordTOTP',
        ]}
)
