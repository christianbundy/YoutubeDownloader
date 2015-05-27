# YoutubeDownloader 

A library for developers to easily search and download youtube videos.

## Installation

First, install [youtube-dl](https://github.com/rg3/youtube-dl), which we shell
out to for the direct downloads.

OS X:
```sh
brew install youtube-dl
```

Other Systems:
```sh
sudo pip install youtube-dl
```

Next, all we need to do to get access to the library is run
```sh
pip install git+https://github.com/dean/YoutubeDownloader.git
```

## Usage

The primary function to take advantage of is ```YoutubeDownloader.downloader.find_and_download(song)```.

The argument ```song``` must be a dictionary with both ```title``` and
```artist``` keys. From there it looks up songs relating to the query with
v3 of Youtube's Data Analysis API, finds the best result, then attempts to
download it with youtube-dl.

## Support

Please [open an issue](https://github.com/dean/YoutubeDownloader/issues/new) for questions and concerns.

## Contributing

Fork the project, commit your changes, and [open a pull request](https://github.com/dean/YoutubeDownloader/compare/).
