#!/usr/bin/env python
#-*- encoding:utf-8 -*-
import os
import logging
def which_encoding(text):

    try:
        biborg=text.encode('utf-8')
        logging.info('utf-8 encode:'+biborg)
    except:
        logging.info("utf-8 encode failed")

    try:
        bibutf16=text.decode('utf-16').encode('gbk')
        logging.info('utf-16 decode:'+bibutf16)
    except:
        logging.info('utf-16 failed')

    try:
        logging.info('original print:'+text)
    except:
        logging.info("origin failed")

    try:
        gbkd=text.decode('gbk')
        logging.info('gbk decode:'+gbkd)
    except:
        logging.info('gbk failed')

    try:
        utf8d=text.decode('utf-8').encode('gbk')
        logging.info('utf-8 decode:'+utf8d)
    except:
        logging.info('utf-8 decode failed')

    try:
        gb2312=text.decode('gb2312')
        logging.info('gb2312 decode:'+gb2312)
    except:
        logging.info('gb2312 failed')

    try:
        gb18030=text.decode('gb18030')
        logging.info('gb18030 decode:'+gb18030)
    except:
            logging.info('gb18030 failed')
