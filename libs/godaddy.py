#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Contact : northdipperbig@gmail.com
Author  : North Star
Date    : 2020.07.06
Desc    : sync godaddy platform domain list and record list

development url             : https://api.ote-godaddy.com/ 
release url                 : https://api.godaddy.com
api documentation           : https://developer.godaddy.com/doc
api version                 : v1
dev api key and secret      : "3mM44Uah1rswvy_9MsqxosRuxL7tphprThPjE","S4Fi8EAaZZUV5ptFmUri9m"
release api key and secrtet : "e4XdGQ7R7whU_V97U2PRgVWD8MPysyJZtYg", "4aFKJcQCQYDygLcK1tHzHH"
exmple:
    curl -X GET -H"Authorization: sso-key e4XdGQ7R7whU_V97U2PRgVWD8MPysyJZtYg:4aFKJcQCQYDygLcK1tHzHH" "https://api.godaddy.com/v1/domains/available?domain=example.guru"
"""

import json, requests, fire

from libs.db_context import DBContext
from libs.web_logs import ins_log
from models.domain import model_to_dict, DNSDomainList, DNSDomainProvider
from datetime import datetime

class GodaddyApi():
    def __init__(self, provider, apikey, apisecret, debug=False):
        self.provider = provider
        self.__apikey = apikey
        self.__apisecret = apisecret
        self.__debug = debug
        if self.__debug:
            self.__server = "https://api.ote-godaddy.com/"
        else:
            self.__server = "https://api.godaddy.com/"
        self.__client = self.client()

    def client(self):
        self.__client = requests.Session()
        #self.__client.auth = (self.__name, self.__token)
        return self.__client

    def _getHeaders(self):
        authinfo = "sso-key {}:{}".format(self.__apikey, self.__apisecret)
        self.__headers = {"Authorization":authinfo, "Content-Type": "application/json;charset=UTF-8"}
        return self.__headers

    def get(self, path, **kw):
        url = self.__server + "/v1/" + path
        headers = self._getHeaders()
        rep = self.__client.get(url, headers=headers, **kw)
        return json.loads(rep.text)

    def post(self, path, data):
        url = self.__server + "/v1/" + path
        headers = self._getHeaders()
        rep = self.__client.post(urk, headers=headers, data=json.dumps(data))
        return json.loads(rep.text)

    def put(self, path, data):
        url = self.__server + "/v1/" + path
        headers = self._getHeaders()
        rep = self.__client.put(url, headers=headers, data=json.dumps(data))
        return json.loads(rep.text)

class GodaddyDomains(GodaddyApi):
    def getdomainlist(self):
        return self.get("domains")

    def sync_dns(self):
        today = datetime.now()
        domain_list = self.getdomainlist()
        if not domain_list or "message" in domain_list:
            ins_log.read_log('error', '没有域名需要更新:')
            return False
        with DBContext('w') as se:
            for domain in domain_list:
                dname = domain.get("domain", 'Null')
                dlocked = domain.get("locked", "Null")
                dctime = domain.get("createdAt", 'Null')
                detime = domain.get("expires", 'Null')
                dstatus = domain.get("status", "Null")
                dautorenew = domain.get("renewAuto", "Null")
                dprovider = self.provider

                is_exists = se.query(DNSDomainList).filter(DNSDomainList.domain_name == dname).first()
                if is_exists:
                    update_dict = {
                        DNSDomainList.domain_locked  : dlocked,
                        DNSDomainList.create_time    : dctime,
                        DNSDomainList.expired_time   : detime,
                        DNSDomainList.domain_status  : dstatus,
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
                        dctime = today.strftime("%Y-%m-%dT%H:%M:%SZ")
                    else:
                        dctime = datetime.fromisoformat(dctime[:-1])

                    if detime == "Null":
                        detime = today.replace(year=today.year+1).strftime("%Y-%m-%dT%H:%M:%SZ")
                    else:
                        detime = datetime.fromisoformat(detime[:-1])

                    se.add(DNSDomainList(
                        domain_name         = dname,
                        domain_provider     = dprovider,
                        domain_locked       = dlocked,
                        create_time         = dctime,
                        expired_time        = detime,
                        domain_status       = dstatus,
                        auto_renew          = dautorenew
                        ))
            se.commit()

def getproviderlist():
    """
        Get id, key, secret
    """
    provider_list = []
    with DBContext('r') as se:
        provider_info = se.query(DNSDomainProvider).filter(DNSDomainProvider.pro_platform == 'godaddy').all()
        for provider in provider_info:
            data_dict = model_to_dict(provider)
            provider_list.append(data_dict)
    return provider_list

def main():
    provider_list = getproviderlist()
    if not provider_list:
        ins_log.read_log('error', "没有狗爹平台账户，跳过。")
        return False
    for privider in provider_list:
        provider_id = privider.get("id")
        provider_apikey = privider.get("pro_api_key")
        provider_apisecret = privider.get("pro_api_secret")

        obj = GodaddyDomains(provider_id, provider_apikey, provider_apisecret)
        obj.sync_dns()

if __name__ == "__main__":
    fire.Fire(main)