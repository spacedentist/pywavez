from setuptools import setup

with open("README.rst", "r") as fh:
    long_description = fh.read()

with open("pywavez/__version__.py", "r") as fh:
    versiondict = {"__builtins__": {}}
    exec(fh.read(), versiondict)
    version = versiondict["version"]

setup(
    name="pywavez",
    version=version,
    description="Native Python implementation of the ZWave protocol",
    long_description=long_description,
    long_description_content_type="text/x-rst",
    url="https://github.com/spacedentist/pywavez",
    download_url=(
        f"https://github.com/spacedentist/pywavez/archive/{ version }.tar.gz"
    ),
    author="Sven Over",
    author_email="sp@cedenti.st",
    license="MIT",
    packages=["pywavez"],
    install_requires=["asyncinit", "pyserial", "pyserial-asyncio"],
    entry_points={
        "console_scripts": [
            "pywavez-remote-serial-server=pywavez.RemoteSerialDevice:main"
        ]
    },
    test_suite="pywavez.tests",
    setup_requires=["tox"],
)
