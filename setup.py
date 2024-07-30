from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="x12-edi-tools",
    version="0.1.1",
    author="Don Johnson",
    author_email="dj@codetestcode.io",
    description="A comprehensive set of tools for working with X12 EDI files",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/copyleftdev/x12-edi-tools",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
    ],
    python_requires=">=3.7",
    install_requires=[
        # List your dependencies here
        "requests>=2.25.1",
        "cryptography>=3.4.7",
        # Add other dependencies as needed
    ],
)