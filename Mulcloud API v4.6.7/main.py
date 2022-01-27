import requests.sessions, requests.cookies
import json
from hashlib import md5
from Crypto.Cipher import AES
from binascii import unhexlify
from base64 import b64encode,b64decode
from pkcs7 import PKCS7Encoder

from PIL import Image, ImageTk
from tkinter import Tk, Label, BOTH
from tkinter.ttk import Frame, Style
from string import ascii_letters
from random import choices, randint
from os.path import isfile
from os import remove
from shutil import copyfileobj

import dbManager as db
from dbManager import  User_Data, Defaults

from requests.packages import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

import logging
log = logging.getLogger(__name__)

class Session(requests.Session):
    def __init__(self, headers = {}):
        super().__init__()
        self.headers = {**headers, 'User-Agent' : 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:92.0) Gecko/20100101 Firefox/92.0'}
        self.user_data = {}
        self.drive_data = {}
        self.current_account = 0
        self.cookies.set("x-cd","cd1=KDA&cd2=/", domain = "app.multcloud.com", path = "/")
        self.verify = False
        

    def update_user_data(self, current_account, user_data, drive_data):
        if not isinstance(user_data, dict):
            raise Exception('user data should be a dictionary')
        self.user_data = user_data
        self.current_account = current_account
        self.drive_data = drive_data
        
    def reset(self):
        self.__init__()
        
    
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

        

def calculate_hash(dic, pop_default = True, **kwargs):
    dic = {**dic, **kwargs}
    dic.pop('s', None)
    param = sorted(dic.keys())
    ln = len(param)
    fin  = ""
    for i in range(ln):
        val = dic[param[ln- i - 1]]
        if isinstance(val, bool):
            val = str(val).lower()
        elif isinstance(val, (list, dict)):
            val = calc_object_hash(val)
        fin += str(param[i]) + str(val)
    out = md5(fin.encode('utf8')).hexdigest()[1:-2]
    dic['s'] = out
    if pop_default:
        dic.pop('aesKey', None)
        dic.pop('salt', None)
    return dic
      
def calc_object_hash(val):
    val = json.dumps(val, separators=(',', ':'))
    val = m = "".join(sorted(val))
    return md5(val.encode('utf8')).hexdigest()


def login(_id = None, command_mode = False):
    if not _id:
        username = input('Enter you email: ')
        password = input('Enter you password: ')
        user_data, drive_data = hot_login_no_captcha(username, password)
        
    else:
        if _id == sess.current_account:
            return print('Already logged in with the account.')
        result, user_data, drive_data, db_session = cold_login(_id)
    
    cookies = [{'name':cook.name, 'value':cook.value, 'domain': cook.domain, 'path': cook.path} for cook in sess.cookies]
    
    if user_data:
        user_data =  {'id':user_data['id'],
                'username':user_data['username'],
                'salt': user_data['salt']}

    cookies, data = str(cookies), str(user_data)

    if not _id:
        result, db_session = db.query(User_Data, {'email' : username}, True)
    
    if result:
        result.cookies = cookies
        result.password = password
        result.data = data
        if not drive_data:
            drive_data = result.drive_data
        db_session.commit()

    else:
        x = db.insert_record(User_Data(email = username, password = password, cookies = cookies, data = data, drive_data = str(drive_data)))
        _id = db.query(User_Data, {'email' : username}, True)
    
    if not (drive_data and isinstance(drive_data, dict)):
        drive_data = eval(result.drive_data)

    sess.update_user_data(_id, user_data, drive_data)
    
    if not command_mode: return
    while True:
        inp = input('\nEnter the command: ')
        try:
            exec(inp)
        except:
            log.exception('Data failed under exec.')

def cold_login(_id):
    # print('Cold Login ...')
    sess.reset()
    result, db_session = db.query(User_Data, {'id' : _id}, True)
    if not result:
        raise Exception("User with the following id couldn't be found.")

    for cook in eval(result.cookies):
        sess.cookies.set(cook['name'], cook['value'], domain = cook['domain'], path = cook['path'])
    
    # check if default url is being fetched
    user_data  = eval(result.data)
    dic = {
        'ud': user_data['id'],
        'salt' : user_data['salt'],
        }
    dic = calculate_hash(dic, False)
    
    # getting data without signing in (with previous session data)
    res = sess.post('https://app.multcloud.com/api/user/get', json = dic)
    success, user_data = convert_response(res, 'user')
    
    if success:
        return result, user_data, None, db_session
    
    # signing in with direct sign in link (with previous session data)
    res = sess.post('https://app.multcloud.com/api/user/direct_sign_in', json = dic)
    success, user_data = convert_response(res, 'user')
    if success:
        return result, user_data, None, db_session

    # if no success hot login

    return (result, *hot_login_no_captcha(result.email, result.password), db_session)


def hot_login_no_captcha(username, password):
    # print('Hot Login, no captcha ...')
    dic = { 'email': username,
            'password': password,
            'rememberMe': True,
            }

    dic = calculate_hash(dic, aesKey = aesKey)

    sess.reset()
    res  = sess.post('https://www.multcloud.com/api/user/sign_in', json = dic)
    success, user_data = convert_response(res, 'user')

    if not(success):
        # print('hot login without captcha failed !.\nTrying with captcha')
        sess.reset()
        return hot_login_captcha(dic, 1)
    drive_data = get_default_drive(user_data['id'], user_data['salt'])
    return user_data, drive_data
    

def hot_login_captcha(dic, try_count = 0):
    # print('Hot login, with captcha ...')
    if try_count == 4:
        raise Exception('Error in program, too many login attempts failed !!!')

    random_digit = randint(1,9)
    vkey = str(random_digit) + ''.join(choices(ascii_letters, k = 14)) + str(9 - random_digit)
    image = sess.get(f"https://www.multcloud.com/api/verify_code/generate?vkey={vkey}", stream=True)
    
    if isfile(image_file):
        remove(image_file)

    with open(image_file, 'wb+') as out_file:
        copyfileobj(image.raw, out_file)

    image_frame =  ImageFrame(image_file)
    captcha  = input('Enter the captcha: ')
    image_frame.close()

    # Try logging in
    dic = calculate_hash(dic, vkey = vkey, vcode = captcha, aesKey = aesKey)
    
    res = sess.post('https://www.multcloud.com/api/user/sign_in', json = dic)
    success, user_data = convert_response(res, 'user')
    if not(success):
        # print('hot login without captcha failed !.\nTrying with captcha')
        return hot_login_captcha(dic, try_count + 1)
    drive_data = get_default_drive(user_data['id'], user_data['salt'])
    return user_data, drive_data

def convert_response(res, key = None):
    res = res.json()
    if isinstance(res, str):
        res = decode_enc_response(res)
    status = res['status'] ==200
    if status:
        if key: res = res[key]
        return status, res
    return status, None


def get_default_drive(user_id, user_salt):
    dic = {'ud': user_id,  'sa' : False}
    dic = calculate_hash(dic, salt = user_salt)

    res = sess.post('https://app.multcloud.com/api/drives/list', json = dic)
    
    success, drive_data = convert_response(res, 'drives')
    if not (success and drive_data):
        raise('Drive link not added. Please try to add a google drive and try again')
    if len(drive_data) > 1:
        print('Please select a drive for default actions')
        for ind, i in enumerate(drive_data):
            print('Option:', ind+1, i['name'], i['email'])
        option = int(input())
        drive_data = drive_data[option - 1]

    else:
        drive_data = drive_data[0]
    return drive_data

def decode_enc_response(res):
    return json.loads( encoder.decode( AES.decrypt(unhexlify(res) ) ).decode('utf8') )


def print_users(print_data = True):
    res, db_session = db.query(User_Data)
    id_list = {}
    for i in res:
        id_list[i.id] = i.email
        if print_data:
            print('id : ', i.id, ', \temail : ', i.email, sep = '')
    return id_list


def change_default_account(_id = None):
    id_list = print_users(not _id)
    if not _id:
        _id = int(input('Enter the new account ID: '))
    
    if _id not in id_list:
        raise Exception('_id not in id list')
    
    data, db_session = db.query(Defaults, {'id':1})
    if not data:
        raise Exception('No data found in defaults table')
    data.value = _id
    db_session.commit()
    return _id


def switch_account(_id = None):
    id_list = print_users(False)
    if not _id:
        for i in id_list:
            print('id : ', i, ', \temail : ', id_list[i], sep = '')
        
    while _id!=0 and (_id not in id_list):
        print("\nEnter '0' to login with a new account, else select the accounts by entering a id.")
        _id = int(input("Enter ID to switch accounts: "))

    if _id:
        return login(_id)
    return login()

def delete_user(_id = None):
    id_list = print_users(False)
    if not _id:
        for i in id_list:
            print('id : ', i, ', \temail : ', id_list[i], sep = '')
        
    while _id not in id_list:
        _id = int(input("Enter the account ID to delete (Ensure the ID is present): "))
    
    del id_list[_id]
    res, db_session = db.query(Defaults)

    if res[0].value == _id:
        print('The account you are deleting is your default account.')
        new_id = 0
        while new_id not in id_list:
            new_id = int(input("Choose another default account (Ensure the ID is present).: "))
        change_default_account(new_id)
    
    if sess.current_account == _id:
        print('The account you are deleting is the current logged in account.')
        new_id = 0
        while new_id not in id_list:
            new_id = int(input('Login with another acccount (Ensure the ID is present): '))
        login(new_id)

    db.delete_record(User_Data, {'id': _id})
    print('Delete account success.')


def login_init(id_list, _id = None):
    if not(id_list):
        return login(command_mode = True)
    if _id:
        return login(_id, command_mode = True)
        
def init_default_conf():
    res, db_session = db.query(Defaults)
    id_list = print_users()

    if not res:
        db.insert_record(Defaults(value = 1))
        login_init(id_list)
    else:
        res = res[0]

    if id_list == {}:
        return login_init(id_list)
    
    if res.value in id_list:
        print(f'Logging with the default account with email: {id_list[res.value]}')
        login_init(id_list, res.value)
    else:
        print('Default id not present in database. Please login with the default account.\n')
        _id = change_default_account()
        login_init(id_list, _id)



## -- DRIVE FUNCTIONALITIES START HERE --

# Works only for google drive
def upload_url(file_url = None, file_name = None, _id = None):
    if _id and _id != sess.current_account:
        login(_id)
    if not file_url:
        file_url = input('Enter the file URL: ')
    if not file_name:
        file_name = input('Enter the file Name: ')
    dic = {
        'ud': sess.user_data['id'],
        'type': int(sess.drive_data['categoryId']),
        'n': file_name,
        'url': file_url,
        'toItems': [{"driveType":"google_drive","driveId":sess.drive_data['id'],
                    "pid":"root","fileId":"root","filename":"Google Drive","isDir":True,
                    "nodes":[{"fileId":"root","filename":"Google Drive"}]}],
        'salt': sess.user_data['salt']      
    }

    dic = calculate_hash(dic)

    res = sess.post('https://app.multcloud.com/api/tasks/add', json = dic)
    success, resp = convert_response(res, 'tasks')
    if success:
        print('Upload Success')


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
        id_list = print_users()
        for i in range(len(url_list)):
            acc.append(int(input(f'Enter the account for file {url_list[i][1]}: ')))

    for index, account_id in enumerate(acc):
        upload_data = url_list[index]
        if len(upload_data) !=2:
            raise Exception('data should be in form or tupple or list with length 2')
        upload_url(*upload_data, account_id)


def get_list(_id):
    dic = {
        'ud': sess.user_data['id'],
        'type':3,
        'salt': sess.user_data['salt']      
    }
    dic = calculate_hash(dic) 
    res = sess.post('https://app.multcloud.com/api/tasks/list', json = dic)
    success, resp = convert_response(res, 'tasks')
    if not success:
        raise Exception('Task list fetch failed')
    
    return resp


def status(_id = None):
    if _id and _id != sess.current_account:
        login(_id)
    resp = get_list(_id)

    for _file in resp:
        file_id, name, status, size  = _file['id'], _file['name'], _file['result'], get_size(_file['filesize'])
        print(f'{name} {size} {status}',end='')
        if status.lower() == 'running':
            file_progress(file_id)
        print('\n')
    else:
        if len(resp)==0:
            print('Empty Status\n')
    
def status_all():
    id_list = print_users(False)
    for _id in id_list:
        status(_id)


def file_progress(file_id):
    dic = {
        'ud': sess.user_data['id'],
        'id': file_id,
        'type': 3,
        'salt': sess.user_data['salt']
    }
    
    dic = calculate_hash(dic)
    res = sess.post('https://app.multcloud.com/api/tasks/get_progress', json = dic)
    success, progress = convert_response(res, 'progress')
    if success:
        return print(f' Progress : {progress} %', end = '')
    return print("Can't get progress for the file")


def get_size(size):
    size = int(size)
    count = 0
    while size >= 1:
        size = size/1024
        count+=1
    size = '{:.2f}'.format(size*1024)+f' {size_list[count]}'
    return size


def clear(_id = None):
    if _id and _id != sess.current_account:
        login(_id)
    resp = get_list(_id)

    for _file in resp:
        file_id, name, status, size  = _file['id'], _file['name'], _file['result'], get_size(_file['filesize'])
        if status.lower() != 'running':
            delete_task(file_id, name)
    print('Deletion Success')

def clear_all():
    id_list = print_users(False)
    for _id in id_list:
        clear(_id)

def delete_task(task_id, file_name):
    dic = {
        'ud': sess.user_data['id'],
        'id': task_id,
        'type': 3,
        'salt': sess.user_data['salt']
    }

    dic = calculate_hash(dic)
    res = sess.post('https://app.multcloud.com/api/tasks/delete', json = dic)
    success, progress = convert_response(res, 'message')
    if not success:
        raise Exception(f'File deletion failed, Name: {file_name}')


aesKey = 'Ns1F8bpJ1LJcHvvcH2sqFA=='
image_file = 'image.jpg'
size_list = {0:'Bytes',1:'Bytes', 2:'KB', 3:'MB', 4:'GB', 5:'TB'}
encoder = PKCS7Encoder()
AES = AES.new( b64decode(aesKey), AES.MODE_ECB)
sess =  Session() 

init_default_conf()
