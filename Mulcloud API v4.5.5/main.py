import requests
import time
import re
import sys
import json
from os.path import isfile
from os import remove
from shutil import copyfileobj
import copy

from PIL import Image, ImageTk
from tkinter import Tk, Label, BOTH
from tkinter.ttk import Frame, Style

import logging
log = logging.getLogger(__name__)

from requests.packages import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

from conf import default_acc, account_map

class Session(requests.Session):
    def __init__(self, headers = {}, user_data= {}, current_acc = 0):
        super().__init__()
        self.headers = {**headers, 'User-Agent' : 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:92.0) Gecko/20100101 Firefox/92.0'}
        self.user_data = user_data
        self.current_acc = current_acc
        self.verify = False
        

    def reset(self):
        self.__init__(
            user_data=self.user_data, 
            current_acc = self.current_acc)

class ImageFrame:
    def __init__(self, path):
        self.root = Tk()
        self.frame = Frame(self.root)
        self.frame.pack(fill = BOTH, expand = 1)
        self.label1 = Label(self.frame)
        self.label1.photo= ImageTk.PhotoImage(Image.open(path))
        self.label1.config(image=self.label1.photo)
        self.label1.pack(fill=BOTH, expand=1)
    
    def close(self):
        self.label1.destroy()
        self.frame.destroy()
        self.root.destroy()

# load cookies

def load_cookies():
    if not isfile('cred.txt'):
        return
    with open('cred.txt', 'r+', encoding = 'utf-8') as f:
        sess.user_data = eval(f.read())
    

def get_time():
    return round(time.time())

def verify_account_map():
    if not account_map:
        print('''The account map in not configured properly please read the documentation.
        Example of config file:
        
        default_acc = 1
        account_map = {
            1: ('randomMail123@gmail.com', 'password@123'),
        }''')

        sys.exit()

def print_users(show_user = True):
    if show_user:
        print('\n'.join([f'{key}: {account_map[key][0]}' for key in account_map]))


def switch_account(_id = None):
    if not _id:
        print_users()
        _id = int(input('Account ID:'))
    login(_id)


def login(_id, command_mode = False):
    if _id and _id != sess.current_acc:
        sess.reset()
        dry_login(_id)
        sess.current_acc = _id
    else:
        return print('Already Logged in')

    if not command_mode: return
    while True:
        inp = input('\nEnter the command: ')
        try:
            exec(inp)
        except:
            log.exception('Data failed under exec.')



def get_drive_info():
    res = sess.get(f'https://www.multcloud.com/index.jsp?rl=en-US&tmp={get_time()}#home')
    hekk = res.text.find('hekk')
    hekk = re.findall('value="(.*?)"', res.text[hekk:hekk + 100])[0]
    userid = sess.cookies.get_dict()['gaUserId']
    final_key = f'{"".join([hekk[i]+userid[i] for i in range(len(hekk))])}'
    drive_data = sess.post(f'https://www.multcloud.com/action/drives!getService?code={final_key}').json()
    return drive_data[0]
    

def dry_login(_id):
    # print('Dry Logging')
    if _id not in sess.user_data:
        return relogin(_id)
        
    cookies = sess.user_data[_id]['cookies']
    for cook in cookies:
        sess.cookies.set(cook['name'], cook['value'], domain = cook['domain'], path = cook['path'])
    drive_token = sess.user_data[default_acc]['drive_token']
    
    # test login
    res = sess.get(f'https://www.multcloud.com/index.jsp?rl=en-US&tmp={get_time()}#home', allow_redirects = False)
    
    if res.status_code !=200:
        return relogin(_id)
        
    return drive_token

def update_cred(_id , drive_token):
    sess.user_data[_id] =  {'drive_token': drive_token,
                         'cookies':[{'name':cook.name, 'value':cook.value, 'domain': cook.domain, 'path': cook.path} for cook in sess.cookies]}
    with open('cred.txt', 'w+') as f:
        f.write(str(sess.user_data))
        

def relogin(_id, verifyCode=''):
    # print('Hot Logging')

    res = sess.post('https://www.multcloud.com/action/userinfo!userLogin',
               data = {'userEmail': account_map[_id][0],
                       'userPassword':  account_map[_id][1],
                       'verifyCode':verifyCode,
                       'isChecked':True,
                       'loginLang':'en-US',
                       'loginDevice': 'pc'
               })
    
    if 'success' not in res.text:
        if isfile(image_file):
            remove(image_file)

        image = sess.get(f"https://www.multcloud.com/action/userinfo!printValidateCode?time={get_time()}", stream=True)
        with open(image_file, 'wb+') as out_file:
            copyfileobj(image.raw, out_file)
    
        image_frame =  ImageFrame(image_file)
        captcha  = input('Enter the captcha: ')
        image_frame.close()
        return relogin(_id, verifyCode)
        
    drive_data = get_drive_info()
    drive_token = drive_data['tokenId']
    drive_username = drive_data['username']
    drive_capacity = sess.post('https://www.multcloud.com/action/drives!getStorageQuota', 
                                data = {'drives.cloudType':'google_drive',
                                'drives.tokenId': drive_token}).text.split('=')[1]
    print('Drive is at capacity:', get_size(drive_capacity))
    print('saving data...')
    
    return update_cred(_id, drive_token)

def upload_file(file_url = None, file_name = None, _id = None):
    if not _id:
        _id = sess.current_acc
    else:
        if _id != sess.current_acc:
            login(_id)

    if file_url == None:
        file_url = input('File URL: ')

    if file_name == None:
        file_name = input('File Name: ')
    drive_token = sess.user_data[sess.current_acc]['drive_token']
    res = sess.post('https://www.multcloud.com/action/offline!add', data= {'offline.url': file_url,
                                                                      'offline.name': file_name,
                                                                      'offline.state': drive_token,
                                                                      'offline.node': json.dumps([{'fileName': 'Google+Drive', 'fileId': 'root',
                                                                            'cloudType': 'google_drive', 'tokenId': drive_token}])})
    print(res.text)

def get_size(size):
    size = int(size)
    count = 0
    while size >= 1:
        size = size/1024
        count+=1
    size = '{:.2f}'.format(size*1024)+f' {size_list[count]}'
    return size

def status():
    r = sess.post('https://www.multcloud.com/action/offline!load')
    if r.text == 'success':
        print('Empty Status')
        return
    
    out = r.json()
    lis = out['list']
    if 'running' in out.keys():
        runn = out['running']
        _id, read, total = runn['id'], int(runn['read']), int(runn['total'])
        for i in lis:
            if i['id'] == _id:
                running_name = i['name']
                break
        
        print(f'{running_name} {get_size(read)} / {get_size(total)}')
        return True
    # if nothing is running
    for i in lis:
        print(f'{i["name"]} State:{i["state"]}')
    return False
    
def clear():
    r = sess.post('https://www.multcloud.com/action/offline!deleteDone')
    print(r.text)


def bulk_upload(*accounts):
    acc = list(accounts)
    url_list = []
    if acc:
        print('Enter the bulk url string:\n')
        url = []
        while True:
            inp = input()
            if inp:
                url.append(inp)
            else:
                break
        url_list = [i.split('___') for i in url if (i.count('___') == 1)]

    if len(url_list) == 0:
        while(True):
            url = input('Enter URL: ')
            if not url: break
            name = input('Enter Name: ')
            url_list.append((url, name))
    if not acc:
        print_users()
        for i in range(len(url_list)):
            acc.append(int(input(f'Enter the account for file {url_list[i][1]}: ')))

    for index, account_id in enumerate(acc):
        upload_data = url_list[index]
        if len(upload_data) !=2:
            raise Exception('data should be in form or tupple or list with length 2')
        upload_file(*upload_data, account_id)

def status_all():
    for i in account_map:
        login(i)
        status()

def clear_all():
    for i in range(len(account_map)):
        switch_account(i+1)
        clear()

image_file = 'cap_image.jpg'
size_list = {0:'Bytes',1:'Bytes', 2:'KB', 3:'MB', 4:'GB', 5:'TB'}

sess = Session()
load_cookies()
verify_account_map()
login(default_acc, command_mode = True)
