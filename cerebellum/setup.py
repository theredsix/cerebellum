from setuptools import setup, find_packages

setup(
    name='cerebellum',
    version='0.1',
    packages=find_packages(),
    install_requires=[
        # List your dependencies here
    ],
    extras_require={
        'browser': [
            'playwright',
            'cssutils',
            'beautifulsoup4'
        ]
    },
    python_requires='>=3.8',
)