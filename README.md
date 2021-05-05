# Chromium Updater
Script to fetch the latest version of the Chromium binary. Basically the process describe [here](https://www.chromium.org/getting-involved/download-chromium) under the section `Not-as-easy steps:`.

# Example Usage
Installation (copying the unzipped content) is only implemented on Windows.

## Options
```
python main.py --help
```
```
usage: main.py [-h] -o OUTPUT_DIRECTORY -p {mac,win,linux} [-i INSTALL] [--proxy PROXY] [-ca ROOT_CA] [-v]

Fetches the latest builds of Chromium for Windows, Mac, Linux

optional arguments:
  -h, --help            show this help message and exit
  -o OUTPUT_DIRECTORY, --output_directory OUTPUT_DIRECTORY
                        Directory where the output file is written
  -p {mac,win,linux}, --platform {mac,win,linux}
                        Platform where Chromium should run
  -i INSTALL, --install INSTALL
                        Where to clean and install chromium
  --proxy PROXY         use proxy
  -ca ROOT_CA, --root_ca ROOT_CA
                        path to a root ca of the proxy for example
  -v, --version         show program's version number and exit

Examples
--------

Fetch the latest archive for a Mac and store the file in the current directory
    > python main.py --platform mac --output_directory .

Fetch the latest archive for a Mac using a proxy and store the file in the current directory
    > python main.py --platform mac --output_directory . --proxy http://proxy.example.com:80

Fetch the latest archive for Windows using a proxy, store the file in
the current directory, and install it to C:\chromium
    > python main.py --platform win --output_directory .  --install C:\chromium --proxy http://proxy.example.com:80 --root_ca root_ca.cer
```