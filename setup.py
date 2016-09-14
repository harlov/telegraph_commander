import os
from setuptools import setup, find_packages

with open(os.path.join(os.path.dirname(__file__), 'README.md')) as readme:
    README = readme.read()

with open(os.path.join(os.path.dirname(__file__), 'requirements.txt')) as readme:
    DEPS_LIST = readme.read().split('\n')

os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

VERSION = '0.0.3'
DESCRIPTION = 'Telegram Bot framework'
REPO_NAME = 'telegraph_commander'

setup(
    name='telegraph_commander',
    version=VERSION,
    packages=find_packages(),
    install_requires=DEPS_LIST,
    include_package_data=True,
    license='MTI License',
    description=DESCRIPTION,
    long_description=README,
    url='https://github.com/harlov/{}'.format(REPO_NAME),
    download_url = 'https://github.com/harlov/{}/archive/v{}.tar.gz'.format(REPO_NAME, VERSION),
    author='Nikita Harlov',
    author_email='nikita@harlov.com',
    classifiers=[
        'Environment :: Console',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Topic :: Education'
    ]
)