#coding: utf8

import urlfetch
import re

def pub2fanfou(username, password, status):
    #获取表单token
    s = urlfetch.Session(headers={'Referer': 'http://m.fanfou.com/'})
    response = s.fetch(
        "http://m.fanfou.com/"
    )
    token = re.search('''name="token".*?value="(.*?)"''', response.body).group(1)
    
    #登录
    response = s.fetch(
        "http://m.fanfou.com/",
        data = {
            'loginname': username,
            'loginpass': password,
            'action': 'login',
            'token': token,
            'auto_login': 'on',
        },
    )
    
    #cookies
    print s.cookiestring
    
    #获取表单token
    response = s.fetch(
        "http://m.fanfou.com/home",
    )
    token = re.search('''name="token".*?value="(.*?)"''', response.body).group(1)
    
    #发布状态
    response = s.fetch(
        "http://m.fanfou.com/",
        data = {
            'content': status,
            'token': token,
            'action': 'msg.post',
        },
    )

if __name__ == '__main__':
    import sys
    pub2fanfou(*sys.argv[1:4])
    


