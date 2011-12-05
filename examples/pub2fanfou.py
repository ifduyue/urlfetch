#coding: utf8

from urlfetch import fetch, fetch2, sc2cs
import re


def pub2fanfou(username, password, status):
    #获取表单token
    response = fetch(
        "http://m.fanfou.com/"
    )
    token = re.search('''name="token".*?value="(.*?)"''', response.body).group(1)
    
    #登录
    response = fetch(
        "http://m.fanfou.com/",
        data = {
            'loginname': username,
            'loginpass': password,
            'action': 'login',
            'token': token,
            'auto_login': 'on',
        },
        headers = {
            "Referer": "http://m.fanfou.com/",
        }
    )
    
    #cookies
    cookies = sc2cs(response.getheader('Set-Cookie'))
    print cookies
    
    #获取表单token
    response = fetch(
        "http://m.fanfou.com/home",
        headers = {
            'Cookie': cookies,
            'Referer': "http://m.fanfou.com/home",
        }
    )
    token = re.search('''name="token".*?value="(.*?)"''', response.body).group(1)
    
    #发布状态
    response = fetch(
        "http://m.fanfou.com/",
        data = {
            'content': status,
            'token': token,
            'action': 'msg.post',
        },
        headers = {
            'Cookie': cookies,
            'Referer': "http://m.fanfou.com/home",
        }
    )

if __name__ == '__main__':
    import sys
    pub2fanfou(*sys.argv[1:4])
    


