#!/usr/bin/env python3
"""
Aegis Framework Setup

Install with: pip install -e .
"""

from setuptools import setup, find_packages
import os

# Read version from package
version = "0.1.0"

# Read README for long description
readme_path = os.path.join(os.path.dirname(__file__), 'README.md')
if os.path.exists(readme_path):
    with open(readme_path, 'r', encoding='utf-8') as f:
        long_description = f.read()
else:
    long_description = "Aegis - Lightweight AppImage Framework"

setup(
    name='aegis-appimage',
    version=version,
    author='Diego',
    author_email='diego@example.com',
    description='Lightweight AppImage framework using WebKit2GTK and Python',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/your-repo/aegis',
    license='MIT',
    
    packages=find_packages(),
    include_package_data=True,
    package_data={
        'aegis': [
            'runtime/*.js',
            'templates/*',
        ],
    },
    
    python_requires='>=3.8',
    
    install_requires=[
        'PyGObject>=3.42.0',
    ],
    
    extras_require={
        'dev': [
            'pytest',
            'black',
            'flake8',
        ],
    },
    
    entry_points={
        'console_scripts': [
            'aegis=aegis.cli.cli:main',
        ],
    },
    
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: X11 Applications :: GTK',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Topic :: Software Development :: Build Tools',
        'Topic :: Desktop Environment',
    ],
    
    keywords='appimage electron alternative webkit gtk python linux desktop',
)
