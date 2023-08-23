import os, sys, site
from setuptools import setup
from setuptools.command.develop import develop
from setuptools.command.install import install

def binaries_directory():
    """Return the installation directory, or None"""
    if '--user' in sys.argv:
        paths = (site.getusersitepackages(),)
    else:
        py_version = '%s.%s' % (sys.version_info[0], sys.version_info[1])
        paths = (s % (py_version) for s in (
            sys.prefix + '/lib/python%s/dist-packages/',
            sys.prefix + '/lib/python%s/site-packages/',
            sys.prefix + '/local/lib/python%s/dist-packages/',
            sys.prefix + '/local/lib/python%s/site-packages/',
            '/Library/Python/%s/site-packages/',
        ))

    for path in paths:
        if os.path.exists(path):
            return path
    return None

class PostDevelopCommand(develop):
    """Post-installation for development mode."""
    def run(self):
        develop.run(self)
        # PUT YOUR POST-INSTALL SCRIPT HERE or CALL A FUNCTION
        os.system(f"sudo raspi-config nonint do_spi 0")
        os.system(f"sudo rm /etc/systemd/system/pi_clock.service")
        os.system(f"ln -s {binaries_directory()}/pi_clock/pi_clock.service /etc/systemd/system/pi_clock.service")
        os.system(f"sudo systemctl daemon-reload")
        os.system(f"sudo systemctl start pi_clock.service")
        os.system(f"sudo systemctl enable pi_clock.service")

class PostInstallCommand(install):
    """Post-installation for installation mode."""
    def run(self):
        install.run(self)
        # PUT YOUR POST-INSTALL SCRIPT HERE or CALL A FUNCTION
        os.system(f"sudo raspi-config nonint do_spi 0")
        os.system(f"sudo rm /etc/systemd/system/pi_clock.service")
        os.system(f"ln -s {binaries_directory()}/pi_clock/pi_clock.service /etc/systemd/system/pi_clock.service")
        os.system(f"sudo systemctl daemon-reload")
        os.system(f"sudo systemctl start pi_clock.service")
        os.system(f"sudo systemctl enable pi_clock.service")

setup(
    name="pi-clock",
    version="0.0.1",
    description="Digital clock for Raspberry Pi",
    package_data={'': ["main","*.bmp","*.service","*.ttf"]},
    include_package_data=True,
    long_description="This will be a long description of the package.",
    author="IoT Connect",
    url="https://github.com/aviralverma-8877/pi-clock",
    author_email="support@iot-connect.in",
    license="MIT",
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.10",
        "Operating System :: OS Independent",
    ],
    install_requires=["adafruit-circuitpython-pcd8544", "psutil", "gpiozero", "python-apt", "Pillow"],
    python_requires=">=3.7",
    cmdclass={'develop': PostDevelopCommand,'install': PostInstallCommand}
)