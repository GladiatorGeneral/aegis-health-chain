from setuptools import setup, find_packages

setup(
    name="aegis-health-chain",
    version="0.1.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "torch>=2.0.0",
        "transformers>=4.30.0",
        "datasets>=2.12.0",
        "fhir.resources>=6.4.0",
        "pandas>=1.5.0",
        "numpy>=1.24.0",
        "scikit-learn>=1.2.0",
        "python-dotenv>=1.0.0",
    ],
    python_requires=">=3.9",
)
