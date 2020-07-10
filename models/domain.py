#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Contact : 191715030@qq.com
Author  : shenshuo
Date    : 2019年5月7日
Desc    : 数据库ORM
"""

from sqlalchemy import Column, String, Integer, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import class_mapper
from datetime import datetime

Base = declarative_base()


def model_to_dict(model):
    model_dict = {}
    for key, column in class_mapper(model.__class__).c.items():
        model_dict[column.name] = getattr(model, key, None)
    return model_dict


class DNSDomainName(Base):
    __tablename__ = 'dns_domain_name'

    domain_id = Column('domain_id', Integer, primary_key=True, autoincrement=True)
    domain_name = Column('domain_name', String(255) ,unique=True ,nullable=False)
    domain_code = Column('domain_code', String(80))
    domain_state = Column('domain_state', String(10), default='running')
    create_time = Column('create_time', DateTime(), default=datetime.now)


class DNSDomainZone(Base):
    __tablename__ = 'dns_domain_zone'

    ###
    zone_id = Column('zone_id', Integer, primary_key=True, autoincrement=True)
    zone = Column('zone', String(255))
    region = Column('region', String(100))
    host = Column('host', String(255))
    type = Column('type', String(8))
    ttl = Column('ttl', Integer)
    data = Column('data', String(255))
    mx = Column('mx', Integer)
    state = Column('state', String(10), default='running')
    update_time = Column('update_time', DateTime(), default=datetime.now, onupdate=datetime.now)


class DNSDomainConf(Base):
    __tablename__ = 'dns_domain_conf'

    ### 配置
    id = Column('id', Integer, primary_key=True, autoincrement=True)
    conf_name = Column('conf_name', String(100), nullable=False)
    conf_value = Column('conf_value', Text())
    update_time = Column('update_time', DateTime(), default=datetime.now, onupdate=datetime.now)

class DNSDomainLog(Base):
    __tablename__ = 'dns_domain_log'

    ### 日志
    id = Column('id', Integer, primary_key=True, autoincrement=True)
    domain_name = Column('domain_name', String(255))
    log_data= Column('log_data', Text())
    update_time = Column('update_time', DateTime(), default=datetime.now, onupdate=datetime.now)

class DNSDomainProvider(Base):
    __tablename__ = "dns_domain_provider"

    id = Column('id', Integer, primary_key=True, autoincrement=True)
    pro_name = Column('pro_name', String(255))  #供应商名称
    pro_platform = Column('pro_platform', String(100)) #域名平台商：name：Name, godaddy: 狗爹, dnspod: DNSPOD
    pro_type = Column('pro_type', Integer, default=0)  #供应商类型： 0: 全部，1: 只够买，2: 只解析
    pro_user = Column('pro_user', String(255))  #供应商用户名
    pro_pwd = Column('pro_password', String(255)) #供应商用户密码
    pro_api_token = Column('pro_api_token', String(255))
    pro_api_key = Column('pro_api_key', String(255)) #供应商API KEY或者API ID
    pro_api_secret = Column('pro_api_secret', String(255)) #供应商Secret KEY
    pro_remarks = Column('pro_remarks', String(255)) #描述信息

class DNSDomainList(Base):
    __tablename__ = "dns_domain_list"

    id = Column('id', Integer, primary_key=True, autoincrement=True)
    domain_name = Column("domain_name", String(255)) #域名名称
    domain_provider = Column('domain_provider', Integer) #域名供应商ID, 必须在DNSDomainProvider表中存在
    domain_locked = Column('domain_locked', Integer) #域名锁定，锁定状态不能转到其他平台
    domain_ns1  = Column('domain_ns1', String(50)) #NS服务器一
    domain_ns2  = Column('domain_ns2', String(50)) #NS服务器二
    create_time = Column('create_time', DateTime()) # 购买时间
    expired_time = Column('expired_time', DateTime()) #过期时间
    domain_status = Column('domain_status', String(20), default="ACTIVE") #域名状态，ACTIVE is default
    auto_renew = Column('auto_renew', Integer) #域名到期是否自动更新

class DNSDomainRecord(Base):
    __tablename__ = 'dns_domain_record'

    id = Column('id', Integer, primary_key=True, autoincrement=True)
    record_key = Column('record_name', String(50)) #记录KEY
    record_type = Column('record_type', String(10)) #记录类型：A/TXT/MAX/CNAME
    record_value = Column('record_value', String(255)) #记录值
    record_remarks = Column('record_remarks', String(255)) #描述信息

