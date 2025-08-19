#!/usr/bin/env python3
"""
Setup script for Ethereum Real-Time Dashboard
"""

from setuptools import setup, find_packages
import os
import re

# Read version from __init__.py
def get_version():
    version_file = os.path.join(os.path.dirname(__file__), 'src', 'ethereum_dashboard', '__init__.py')
    if os.path.exists(version_file):
        with open(version_file, 'r') as f:
            content = f.read()
            version_match = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]", content, re.M)
            if version_match:
                return version_match.group(1)
    return '0.1.0'

# Read long description from README
def get_long_description():
    readme_file = os.path.join(os.path.dirname(__file__), 'README.md')
    if os.path.exists(readme_file):
        with open(readme_file, 'r', encoding='utf-8') as f:
            return f.read()
    return ''

# Read requirements
def get_requirements(filename='requirements.txt'):
    requirements_file = os.path.join(os.path.dirname(__file__), filename)
    if os.path.exists(requirements_file):
        with open(requirements_file, 'r') as f:
            return [line.strip() for line in f if line.strip() and not line.startswith('#')]
    return []

setup(
    name='ethereum-dashboard',
    version=get_version(),
    description='Enterprise-grade real-time Ethereum dashboard using Microsoft Fabric',
    long_description=get_long_description(),
    long_description_content_type='text/markdown',
    author='Your Team',
    author_email='team@yourcompany.com',
    url='https://github.com/yourcompany/ethereum-dashboard',
    license='MIT',
    
    # Package discovery
    packages=find_packages('src'),
    package_dir={'': 'src'},
    
    # Python version requirement
    python_requires='>=3.9',
    
    # Dependencies
    install_requires=get_requirements('requirements-prod.txt'),
    
    # Optional dependencies
    extras_require={
        'dev': get_requirements('requirements-dev.txt'),
        'test': [
            'pytest>=7.4.0',
            'pytest-cov>=4.0.0',
            'pytest-asyncio>=0.21.0',
            'pytest-mock>=3.10.0',
            'factory-boy>=3.3.0',
            'faker>=20.0.0',
        ],
        'docs': [
            'sphinx>=7.2.0',
            'sphinx-rtd-theme>=1.3.0',
            'mkdocs>=1.5.0',
            'mkdocs-material>=9.4.0',
        ],
        'monitoring': [
            'prometheus-client>=0.19.0',
            'statsd>=4.0.0',
            'grafana-client>=4.0.0',
        ],
    },
    
    # Entry points for CLI commands
    entry_points={
        'console_scripts': [
            'ethereum-collector=ethereum_dashboard.collector.main:main',
            'ethereum-monitor=ethereum_dashboard.monitoring.main:main',
            'ethereum-quality-check=ethereum_dashboard.quality.main:main',
            'ethereum-deploy=ethereum_dashboard.deployment.cli:main',
        ],
    },
    
    # Package data
    include_package_data=True,
    package_data={
        'ethereum_dashboard': [
            'config/*.yaml',
            'config/*.json',
            'templates/*.j2',
            'sql/*.sql',
            'kql/*.kql',
        ],
    },
    
    # Classifiers for PyPI
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Intended Audience :: Financial and Insurance Industry',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Office/Business :: Financial',
        'Topic :: Scientific/Engineering :: Information Analysis',
        'Topic :: System :: Monitoring',
    ],
    
    # Keywords for PyPI
    keywords=[
        'ethereum', 'blockchain', 'real-time', 'dashboard', 'microsoft-fabric',
        'azure', 'data-engineering', 'streaming', 'analytics', 'monitoring'
    ],
    
    # Project URLs
    project_urls={
        'Bug Reports': 'https://github.com/yourcompany/ethereum-dashboard/issues',
        'Source': 'https://github.com/yourcompany/ethereum-dashboard',
        'Documentation': 'https://ethereum-dashboard.readthedocs.io/',
        'Funding': 'https://github.com/sponsors/yourcompany',
    },
    
    # Additional metadata
    zip_safe=False,
    platforms=['any'],
    
    # Tests
    test_suite='tests',
)