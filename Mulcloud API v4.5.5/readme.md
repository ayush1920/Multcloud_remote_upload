# Multcloud remote upload API (Gdrive) [v4.5.5]

![Alt text](./images/multcloud.png)

![A test image](https://img.shields.io/static/v1?label=status&message=completed&logo=github&color=F8523B) ![GitHub issues](https://img.shields.io/github/issues/ayush1920/Multcloud_remote_upload)

The repo conins script to remotly upload link to google drive using **old** multcloud account.
### Features
- Supports multiple account login.
- Supports bulk upload (multiple url in different account)
- Logging in with captcha 
- Multiple level logging to reduce login time and captcha trails.

### Installing the requirements.
Install the requirements from requirements.txt by using `python -m pip install -r requirements.txt` in main or virtual enviornment.

### Running with command prompt
To run the old version, enter your credentials in `config.py` file in format -<br>
`account_map = {   'id1': 'email_id', 'password'),
    'id2':('email_id', 'password')}`

**Sample login credentials are given.**

Set `default_account` as the id of account which you want to log into when running the script for first time.

Run the *main.py* file using `main.py` (windows) or `python3 main.py` (linux) command.
*When logging in for first time the script will ask for captcha, a new image window will open for captcha. Enter the captcha in command line*
## Functions
### upload_file
Uploads the file with link to the root folder of google drive.

![Upload example](../images/upload_old.png)

### status
Status of all the task present in the list.

![status example](../images/status_old.png)

### clear
Clears all 'completed' and 'failed' task present in the list. Running tasks will keep running.

![clear example](../images/clear_old.png)


### bulk_upload
Bulk upload command can be used to upload multiple link in different accounts. The command can be used in 2 formats.<br>

#### 1. No parameter with function
You can just call the function and give diffrent file_name, url and account ID for respective upload. *Enter a blank url to break input cycle.*
Example -

![bulk_upload_1 example](../images/bulk_upload_old_1.png)

#### 2. Using parameterized input for account ids and '___' for url and name.
Faster way to input the url is to provide account ids as patameters in bulk_upload function. The bulkupload string could be given in form of `{url}___{file Name}`. Example -

![bulk_upload_2 example](../images/bulk_upload_old_2.png)

### switch_account
Switch between accounts mannualy.

![switch_account example](../images/switch_account_old.png)


### status_all
Provides Status of all the task present from all your accounts.

![status_all example](../images/status_all_old.png)

### clear_all
Clears all 'completed' and 'failed' task present in the list of all the account. Running tasks will keep running.

![clear_all example](../images/clear_all_old.png)

<br>*Currently the script uses text file to store data. For a more rhobust scrpit use the new version.*
