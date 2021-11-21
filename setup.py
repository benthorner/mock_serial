import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="mock_serial",
    version="0.0.1",
    author="Ben Thorner",
    author_email="benthorner@users.noreply.github.com",
    description="A mock utility for testing serial devices",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/benthorner/mock_serial",
    project_urls={
        "Bug Tracker": "https://github.com/benthorner/mock_serial/issues",
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: Unix",
        "Framework :: Pytest"
    ],
    package_dir={"": "src"},
    packages=setuptools.find_packages(where="src"),
    python_requires=">=3.7",
    entry_points={
        "pytest11": ["pytest-mock-serial = mock_serial.pytest"]
    },
)
