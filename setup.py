from setuptools import setup

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
    python_requires=">=3.7"
)