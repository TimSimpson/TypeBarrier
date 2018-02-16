import setuptools


setuptools.setup(
    name='TypeBarrierScripts',
    entry_points={
        'console_scripts': [
            "typebarrier-tests = runner:main",
        ],
    }
)
