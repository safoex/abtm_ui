import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="abtmui",  # Replace with your own username
    version="0.0.1",
    author="Evgenii Safronov",
    author_email="safoex@gmail.com",
    description="A package with behavior tree visualization",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/safoex/abtm_ui",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
    include_package_data=True
)
