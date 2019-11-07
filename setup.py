from setuptools import setup, find_packages


if __name__ == "__main__":
    setup(
        name="pupil_invisible_lsl_relay",
        version="0.1",
        packages=['pupil_invisible_lsl_relay'],
        install_requires=[
            "pylsl>=1.12.2",
            "click>=7.0",
        ],
        url="https://github.com/labstreaminglayer/App-PupilLabs",
        author="Pupil Labs",
        author_email="info@pupil-labs.com",
        entry_points={
            'console_scripts': [
                'pupil_invisible_lsl_relay = pupil_invisible_lsl_relay.cli:main',
            ]
        }
    )
