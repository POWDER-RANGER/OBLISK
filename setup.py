"""Setup configuration for OBLISK."""
from setuptools import setup, find_packages
import pathlib

here = pathlib.Path(__file__).parent.resolve()
long_description = (here / "README.md").read_text(encoding="utf-8")

# Read requirements
with open("requirements.txt") as f:
    requirements = [line.strip() for line in f if line.strip() and not line.startswith("#")]

setup(
    name="oblisk",
    version="1.0.0",
    description="Multi-agent AI orchestration framework with encrypted vaults, governance, and symbolic planning",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/POWDER-RANGER/OBLISK",
    author="POWDER-RANGER",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    keywords="ai, agents, multi-agent, orchestration, governance, symbolic-ai, planning",
    packages=find_packages(exclude=["tests", "docs", "examples"]),
    python_requires=">=3.8",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-cov>=4.1.0",
            "pytest-asyncio>=0.21.0",
            "black>=23.0.0",
            "ruff>=0.1.0",
            "mypy>=1.5.0",
            "pre-commit>=3.4.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "oblisk=oblisk_cli:main",
        ],
    },
    project_urls={
        "Bug Reports": "https://github.com/POWDER-RANGER/OBLISK/issues",
        "Source": "https://github.com/POWDER-RANGER/OBLISK",
        "Documentation": "https://github.com/POWDER-RANGER/OBLISK/blob/main/docs/README.md",
    },
)
