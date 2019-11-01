from setuptools import setup

setup(
    name="pywavez",
    version="0.1",
    description="Native Python implementation of the ZWave protocol",
    url="https://github.com/spacedentist/pyimmutable",
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
