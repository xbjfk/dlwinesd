from setuptools import setup, find_packages
import pathlib

here = pathlib.Path(__file__).parent.resolve()

long_description = (here / 'README.md').read_text(encoding='utf-8')

setup(
    name='dlwinesd',
    version='0.1',
    license='MIT',
    author_email='xbjfk.github@gmail.com',
    package_dir={'': '.'},
    packages=find_packages('.'),
    url='https://github.com/xbjfk/dlwinesd',
    keywords='ESD windows',
    install_requires=[
          'requests',
          'xmltodict',
    ],
    entry_points={
        'console_scripts': [
            'dlwinesd=dlwinesd:main',
        ],
    }

)
