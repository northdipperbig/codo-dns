#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Contact : northdipperbig@gmail.com
Author  : North Star
Date    : 2020.07.05
Desc    :  域名供应商管理
"""

import json
import re
import tornado.web
import time

from sqlalchemy import or_
from tornado import gen
from concurrent.futures import ThreadPoolExecutor
from tornado.concurrent import run_on_executor

from libs.base_handler import BaseHandler
from libs.godaddy import main as godaddy_domain_update
from libs.namecom import main as namecom_domain_update
from websdk.base_handler import LivenessProbe
from websdk.db_context import DBContext
from models.domain import model_to_dict, DNSDomainProvider, DNSDomainList


def check_contain_chinese(check_str):
    for ch in check_str:
        if u'\u4e00' <= ch <= u'\u9fff':
            return True
    return False


def is_ip(ip):
    # p = re.compile('^((25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}(25[0-5]|2[0-4]\d|[01]?\d\d?)$')

    p = re.compile('^(1\d{2}|2[0-4]\d|25[0-5]|[1-9]\d|[1-9])\.(1\d{2}|2[0-4]\d|25[0-5]|[1-9]\d|\d)\.(1\d{2}|2[0-4]\d|25[0-5]|[1-9]\d|\d)\.(1\d{2}|2[0-4]\d|25[0-5]|[1-9]\d|\d)$')
    if p.match(ip):
        return True
    else:
        return False


def is_domain(domain):
    domain_regex = re.compile(r'(?:[A-Z0-9_](?:[A-Z0-9-_]{0,247}[A-Z0-9])?\.)+(?:[A-Z]{2,6}|[A-Z0-9-]{2,}(?<!-))\Z',
                              re.IGNORECASE)
    return True if domain_regex.match(domain) else False


class DNSPrivate(BaseHandler):
    def get(self, *args, **kwargs):
        key = self.get_argument('key', default=None, strip=True)
        value = self.get_argument('value', default=None, strip=True)
        page_size = self.get_argument('page', default=1, strip=True)
        limit = self.get_argument('limit', default=888, strip=True)
        limit_start = (int(page_size) - 1) * int(limit)

        plist = []
        if key and value:
            with DBContext('r') as se:
                count = se.query(DNSDomainProvider).filter(getattr(DNSDomainProvider, key).ilike("%{}%".format(value))).count()
                pinfo = se.query(DNSDomainProvider).filter(getattr(DNSDomainProvider, key).ilike("%{}%".format(value))).offset(limit_start).limit(int(limit))

        else:
            with DBContext('r') as se:
                count = se.query(DNSDomainProvider).count()
                pinfo = se.query(DNSDomainProvider).offset(limit_start).limit(int(limit))

        for p in pinfo:
            data_dict = model_to_dict(p)
            plist.append(data_dict)
        return self.write(dict(code=0, msg="获取供应商成功", count=count, data=plist))

    def post(self, *args, **kwargs):
        data = json.loads(self.request.body.decode("utf-8"))
        priname = data.get('pro_name', None)
        priplat = data.get('pro_platform', None)
        pritype = data.get('pro_type', None)
        priuser = data.get('pro_user', None)
        pripwd = data.get('pro_password', None)
        priapitoken = data.get('pro_api_token', None)
        priapikey = data.get('pro_api_key', None)
        priapisecret = data.get('pro_api_secret', None)
        priremarks = data.get('pro_remarks', None)

        if not priname or pritype is None:
            return self.write(dict(code=-1, msg="参数不能为空"))

        with DBContext('w', None, True) as se:
            is_exists = se.query(DNSDomainProvider).filter(DNSDomainProvider.pro_name == priname).first()
            if is_exists:
                return self.write(dict(code=-2, msg="供应商已经存在"))
            se.add(DNSDomainProvider(
                pro_name = priname,
                pro_platform = priplat,
                pro_type = pritype,
                pro_user = priuser,
                pro_pwd = pripwd,
                pro_api_token = priapitoken,
                pro_api_key = priapikey,
                pro_api_secret = priapisecret,
                pro_remarks = priremarks
                ))
        
        return self.write(dict(code=0, msg="添加供应商成功"))

    def put(self, *args, **kwargs):
        data = json.loads(self.request.body.decode("utf-8"))
        priid = data.get('id', None)
        priname = data.get('pro_name', None)
        priplat = data.get('pro_platform', None)
        pritype = data.get('pro_type', None)
        priuser = data.get('pro_user', None)
        pripwd = data.get('pro_password', None)
        priapitoken = data.get('pro_api_token', None)
        priapikey = data.get('pro_api_key', None)
        priapisecret = data.get('pro_api_secret', None)
        priremarks = data.get('pro_remarks', None)

        if not priid or not priname or pritype is None:
            return self.write(dict(code=-1, msg="参数不能为空"))

        with DBContext('w', None, True) as se:
            se.query(DNSDomainProvider).filter(DNSDomainProvider.id == priid).update({
                DNSDomainProvider.pro_name : priname,
                DNSDomainProvider.pro_platform : priplat,
                DNSDomainProvider.pro_type : pritype,
                DNSDomainProvider.pro_user : priuser,
                DNSDomainProvider.pro_pwd : pripwd,
                DNSDomainProvider.pro_api_token: priapitoken,
                DNSDomainProvider.pro_api_key : priapikey,
                DNSDomainProvider.pro_api_secret : priapisecret,
                DNSDomainProvider.pro_remarks : priremarks
                })
        
        return self.write(dict(code=0, msg="修改供应商成功"))

    def delete(self, *args, **kwargs):
        data = json.loads(self.request.body.decode("utf-8"))
        priid = data.get('id', None)
        idlist = data.get('id_list', None)

        if priid:
            with DBContext('w', None, True) as se:
                is_exists_domain = se.query(DNSDomainList).filter(DNSDomainList.domain_provider == priid).first()
                if is_exists_domain:
                    return self.write(dict(code=-1, msg="供应商存在域名，不可删除"))
                else:
                    se.query(DNSDomainProvider).filter(DNSDomainProvider.id == priid).delete(synchronize_session=False)
                    return self.write(dict(code=0, msg="删除供应商成功"))
        
        if idlist:
            with DBContext('w', None, True) as se:
                is_exists_domain = se.query(DNSDomainList).filter(DNSDomainList.domain_provider.in_(idlist)).first()
                if is_exists_domain:
                    return self.write(dict(code=-2, msg="供应商存在域名，不可删除"))
                else:
                    se.query(DNSDomainProvider).filter(DNSDomainProvider.id.in_(idlist)).delete(synchronize_session=False)
                    return self.write(dict(code=0, msg="删除供应商成功"))
        
        return self.write(dict(code=-3, msg="参数不能为空"))

class DNSPrivateTree(BaseHandler):
    def get(self, *args, **kwargs):
        _tree = [{
            "expand": True,
            "title": "root",
            "children":[]
            }]
        with DBContext('r') as se:
            private_info = se.query(DNSDomainProvider).order_by(DNSDomainProvider.id).all()
            for p in private_info:
                private_dict = {}
                data_dict = model_to_dict(p)
                domain_providers = se.query(DNSDomainProvider.id).outerjoin(DNSDomainList, DNSDomainList.domain_provider == DNSDomainProvider.id).filter(DNSDomainList.domain_provider == p.id).all()
                private_dict["id"] = data_dict["id"]
                private_dict["the_len"] = len(domain_providers)
                private_dict["title"] = "{} ({})".format(data_dict["pro_name"], len(domain_providers))
                private_dict["pro_name"] = data_dict["pro_name"]
                private_dict["node"] = "root"
                _tree[0]['children'].append(private_dict)
        self.write(dict(code=0, msg="获取供应商列表成功", data=_tree))

class DNSDomainUpdate(tornado.web.RequestHandler):
    '''前端手动触发从云厂商更新资产,使用异步方法'''
    _thread_pool = ThreadPoolExecutor(3)

    @run_on_executor(executor='_thread_pool')
    def handler_update_task(self):
        godaddy_domain_update()
        time.sleep(2)
        namecom_domain_update()

    @gen.coroutine
    def get(self, *args, **kwargs):
        yield self.handler_update_task()
        return self.write(dict(code=0, msg='域名列表更新完成'))


private_urls = [
    (r"/v1/dns/private/", DNSPrivate),
    (r"/v1/dns/private/tree/", DNSPrivateTree),
    (r"/v1/dns/private/update/domains/", DNSDomainUpdate)
]
