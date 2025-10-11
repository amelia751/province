"""Setup configuration for Tax Rules Connector."""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="tax-rules-connector",
    version="1.0.0",
    author="Your Organization",
    author_email="contact@yourorg.com",
    description="Fivetran connector for IRS tax rules and regulations",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/your-org/tax-rules-connector",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "tax-rules-connector=tax_rules_connector.main:main",
        ],
    },
    include_package_data=True,
    zip_safe=False,
)
