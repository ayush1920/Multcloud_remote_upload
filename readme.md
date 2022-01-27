# Multcloud remote upload API (Gdrive)

![Alt text](./images/multcloud.png)

![A test image](https://img.shields.io/static/v1?label=status&message=completed&logo=github&color=F8523B) ![GitHub issues](https://img.shields.io/github/issues/ayush1920/Multcloud_remote_upload)

The repo conins script to remotly upload link to google drive using multcloud account.

## Features
- Supports multiple account login.
- Supports bulk upload (multiple url in different account)
- Logging in with captcha 
- Multiple level logging to reduce login time and captcha trails.

## Running the application
Read the respective readme files of new and old version to understand various functionalities.

## FAQ

**Why are there two versions?**<br>

The site has changed its code and UI which urged me to write new script. The new js code uses AES encryption to trasfer data. Old version of the site is also available so you can use both the scripts as of now.

**Why only remote upload with GDrive is supported?**<br>

As per my requirement, the only task I do is, to fetch slow downloading files to my google Drive. You can pretty much change the request code by using suitable parameter while sending drive data.  The encrypted response comming from from the website can by easily seen in any browser using developer Tools -> Network Tab. The file `decode_response.py` can decode those encrypted string. **Any contribution to the project is welcomed.**

*Multcloud images and graphics used in the used in the repo belong to their respective owners.*