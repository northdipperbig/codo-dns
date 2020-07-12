#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Contact : northdipperbig@gmail.com
Author  : North Star
Date    : 2020/07/12
Desc    :
    SSL certificate info
"""

import ssl, socket, datetime

class SslCertificate:
    def getSslCertificateInfo(self, hostname):
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
            return None
        return conn.getpeercert()
    
    def sslCertificateExpiredTime(self, domain):
        #datetime.datetime.strptime(certificate_time, r'%b %d %H:%M:%S %Y %Z')
        cert_info = self.getSslCertificateInfo(domain)
        if cert_info:
            return cert_info.get("notAfter", None)
        else:
            return None