#!/usr/bin/env python3
"""
Setup script for Rival Agent
"""

from setuptools import setup, find_packages
import os

# Read the contents of README file
def read_file(filename):
    with open(os.path.join(os.path.dirname(__file__), filename), encoding='utf-8') as f:
        return f.read()

# Read requirements
def read_requirements():
    with open('requirements.txt', 'r') as f:
        return [line.strip() for line in f if line.strip() and not line.startswith('#')]

setup(
    name="rival-agent",
    version="1.0.0",
    author="Rival Agent Team",
    author_email="contact@rival-agent.com",
    description="A blockchain-powered AI agent with search capabilities",
    long_description=read_file("README.md"),
    long_description_content_type="text/markdown",
    url="https://github.com/your-org/rival-agent",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Internet :: WWW/HTTP :: Indexing/Search",
    ],
    python_requires=">=3.8",
    install_requires=read_requirements(),
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
            "black>=22.0.0",
            "flake8>=4.0.0",
            "mypy>=0.991",
            "pre-commit>=2.20.0",
        ],
        "test": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
            "pytest-cov>=4.0.0",
        ]
    },
    entry_points={
        "console_scripts": [
            "rival-agent=rival_agent.rival_agent:main",
        ],
    },
    include_package_data=True,
    package_data={
        "rival_agent": ["../abi.json"],
    },
    keywords="blockchain ai agent search web3 ethereum smart-contracts",
    project_urls={
        "Bug Reports": "https://github.com/your-org/rival-agent/issues",
        "Source": "https://github.com/your-org/rival-agent",
        "Documentation": "https://rival-agent.readthedocs.io/",
    },
)
