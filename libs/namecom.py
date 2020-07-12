#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Contact : northdipperbig@gmail.com
Author  : North Star
Date    : 2020.07.06
Desc    : sync name.com domain list and record list

development url         : https://api.dev.name.com
release url             : https://api.name.com
api documentation       : https://www.name.com/api-docs
api version             : v4
dev account token       : "pangzi201808@gmail.com-test", "2ddeecb98ae54e44fb3ffe0aa53d8febabe93ca4"
release account token   : "pangzi201808@gmail.com","89b6994c38aff48c658dd04aa887a43164e0b0cf"
"""

import json, requests

from libs.db_context import DBContext
from libs.web_logs import ins_log

from models.domain import model_to_dict, DNSDomainProvider, DNSDomainList
from datetime import datetime

class NameComApi:

    def __init__(self, provider, name, token, debug=False):
        self.provider = provider
        self.__name = name
        self.__token = token
        self.__debug = debug

        if self.__debug:
            self.__server = "https://api.dev.name.com"
        else:
            self.__server = "https://api.name.com"
        self.__client = self.client()

    def client(self):
        self.__client = requests.Session()
        self.__client.auth = (self.__name, self.__token)
        return self.__client

    def get(self, path, **kw):
        url = self.__server + "/v4/" + path
        rep = self.__client.get(url, **kw)
        return json.loads(rep.text)

    def post(self, path, data):
        url = self.__server + "/v4/" + path
        rep = self.__client.post(urk, data)
        return json.loads(rep.text)

    def put(self, path, data):
        url = self.__server + "/v4/" + path
        rep = self.__client.put(url, data)
        return json.loads(rep.text)

class NameDomains(NameComApi):
    def getdomainlist(self):
        return self.get("domains")

    def getdomain(self, domain):
        path = "domains/{}".format(domain)
        return self.get(path)

    def sync_dns(self):
        today = datetime.now()
        domain_list = self.getdomainlist()
        if not domain_list or "message" in domain_list:
            ins_log.read_log('error', '没有域名需要更新或者认证失败: {}'.format(domain_list))
            return False
        
        with DBContext('w') as se:
            for domain in domain_list["domains"]:
                dname = domain.get("domainName","Null")
                dlocked = domain.get("locked","Null")
                dctime = domain.get("expireDate", 'Null')
                detime = domain.get("expireDate", 'Null')
                dautorenew = domain.get("autorenewEnabled", False)
                dprovider = self.provider

                is_exists = se.query(DNSDomainList).filter(DNSDomainList.domain_name == dname, DNSDomainProvider.pro_status == dprovider).first()
                if is_exists:
                    update_dict = {
                        DNSDomainList.domain_locked  : dlocked,
                        DNSDomainList.create_time    : dctime,
                        DNSDomainList.expired_time   : detime,
                        DNSDomainList.auto_renew     : dautorenew,
                        DNSDomainList.domain_provider: dprovider
                        }
                    if dctime == 'Null':
                        update_dict.pop(DNSDomainList.create_time)
                    else:
                        update_dict[DNSDomainList.create_time] = datetime.fromisoformat(dctime[:-1])

                    if detime == "Null":
                        update_dict.pop(DNSDomainList.expired_time)
                    else:
                        update_dict[DNSDomainList.expired_time] = datetime.fromisoformat(detime[:-1])

                    se.query(DNSDomainList).filter(DNSDomainList.domain_name == dname).update(update_dict)
                else:
                    if dctime == 'Null':
                        dctime = today.strftime("%Y-%m-%dT%H:%M:%S")
                    else:
                        dctime = datetime.fromisoformat(dctime[:-1])

                    if detime == "Null":
                        detime = today.replace(year=today.year+1).strftime("%Y-%m-%dT%H:%M:%S")
                    else:
                        detime = datetime.fromisoformat(detime[:-1])
                    se.add(DNSDomainList(
                        domain_name         = dname,
                        domain_provider     = dprovider,
                        domain_locked       = dlocked,
                        create_time         = dctime,
                        expired_time        = detime,
                        auto_renew          = dautorenew
                        ))
            se.commit()

def getproviderlist():
    """
        Get id, key, secret
    """
    provider_list = []
    with DBContext('r') as se:
        provider_info = se.query(DNSDomainProvider).filter(DNSDomainProvider.pro_platform == 'name', DNSDomainProvider.pro_status).all()
        for provider in provider_info:
            data_dict = model_to_dict(provider)
            provider_list.append(data_dict)
    return provider_list

def main():
    provider_list = getproviderlist()
    if not provider_list:
        ins_log.read_log('error', "没有Name.com平台账户，跳过。")
        return False
    for privider in provider_list:
        provider_id = privider.get("id")
        provider_apikey = privider.get("pro_user")
        provider_apisecret = privider.get("pro_api_token")

        obj = NameDomains(provider_id, provider_apikey, provider_apisecret)
        obj.sync_dns()

if __name__ == "__main__":
    fire.Fire(main)