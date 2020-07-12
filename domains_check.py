#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Contact : northdipperbig@gmail.com
Author  : North Star
Date    : 2020/05/12
Desc    :
    Update domain from domain platform
    Check domain expired time
    Check ssl cert ecpory time
    Send telegram message to group
"""

import telegram, os, ssl, socket, datetime

from libs.godaddy import main as godaddy_domain_update
from libs.namecom import main as namecomd_domain_update
from libs.db_context import DBContext
from libs.web_logs import ins_log

from models.domain import model_to_dict, DNSDomainList

def getSslCertificateInfo(hostname):
    context = ssl.create_default_context()
    conn = context.wrap_socket(
        socket.socket(socket.AF_INET),
        server_hostname=hostname,
    )
    # 3 second timeout because Lambda has runtime limitations
    conn.settimeout(3.0)
    try:
        conn.connect((hostname, 443))
    except Exception as e:
        #ins_log.read_log('error', e)
        return None
    return conn.getpeercert()

def sslCertificateExpiredTime(domain):
    cert_info = getSslCertificateInfo(domain)
    if cert_info:
        return cert_info.get("notAfter", None)
    else:
        return None

if __name__ == "__main__":

    expired_domains = []
    expired_certificate = []
    todaytime = datetime.datetime.now()
    Nossldomains = 0
    hasssldomains = 0

    TgApiToken = "1063249430:AAFjdQYajKzIX70RgYZnMv8Y0zIVtpqZ-ps"
    #TgChatId = "837951069" #To only North
    TgChatId = "-403702424" #测试级
    TgBot = telegram.Bot(TgApiToken)
    
    #Update all domain list
    godaddy_domain_update()
    namecomd_domain_update()

    #Get domainlist
    with DBContext('r') as se:
        domain_info = se.query(DNSDomainList).all()
        if not domain_info:
            ins_log.read_log("error", "Not domain list or get domain list faield. {}".format(domain_info))
            os.exit(-1)
        for domain in domain_info:
            data_dict = model_to_dict(domain)
            dName = data_dict.get('domain_name')
            DExpiredTime = data_dict.get('expired_time')
            DExpiredDays = (DExpiredTime - todaytime).days
            if DExpiredDays < 15:
                expired_domains.append({'domain_name': dName, 'expired_time': str(DExpiredTime)})
            certificate_time = sslCertificateExpiredTime(dName)
            if certificate_time:
                hasssldomains += 1
                certtime = datetime.datetime.strptime(certificate_time, r'%b %d %H:%M:%S %Y %Z')
                certdays = (certtime - todaytime).days
                if certdays < 30:
                    expired_certificate.append({'domain_name': dName, 'certificate_expired_time': str(certtime)})
                #print("info", "ID:{}   Nname:{}  ExpiredDays: {}    CertificateExpiredTime:{}   CertificateDays:{}".format(data_dict.get('id'), dName, DExpiredDays, certtime, certdays))
            else:
                Nossldomains += 1
                #print("info", "ID:{}   Nname:{}  ExpiredDays: {}".format(data_dict.get('id'), dName, DExpiredDays))
        #print("No ssl domains: {}".format(Nossldomains))
        #print("Has ssl domains: {}".format(hasssldomains))
        #print("Expired domain list: {}".format(expired_domains))
        #print("Certificate expired domain list: {}".format(expired_certificate))
        msg = '''共检查域名数: {}个
15天到期域名: {}个
含有证书域名: {}个
30天证书到期: {}个'''.format(len(domain_info), len(expired_domains), hasssldomains, len(expired_certificate))
        TgBot.send_message(TgChatId, msg)
        if len(expired_domains) > 0:
            msg = "十五天到期域名：\n"
            for d in expired_domains:
                msg += "{} : {}\n".format(d.get('domain_name'), d.get('expired_time'))
            TgBot.send_message(TgChatId, msg)
        if len(expired_certificate) > 0:
            msg = '三十天证书到期域名: \n'
            for d in expired_certificate:
                msg += "{} : {}\n".format(d.get('domain_name'), d.get('certificate_expired_time'))
            TgBot.send_message(TgChatId, msg)