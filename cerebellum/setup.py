from setuptools import setup, find_packages

setup(
    name='cerebellum',
    version='0.1',
    packages=find_packages(),
    install_requires=[
        'playwright',
        'cssutils',
        'beautifulsoup4'
    ],
    python_requires='>=3.8',
)