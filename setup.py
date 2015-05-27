from setuptools import setup, find_packages

requires = open('requirements.txt').read().split('\n')

setup(
    name='YoutubeDownloader',
    version='0.2.0',
    description='Downloads music from Youtube based off a title and artist. Optimized for correctness.',
    install_requires=requires,
    author='Dean Johnson',
    author_email='deanjohnson222@gmail.com',
    url='https://www.github.com/dean/YoutubeDownloader',
    packages=['YoutubeDownloader'],
    package_dir={'YoutubeDownloader': 'YoutubeDownloader'},
)
