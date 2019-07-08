# -*- coding:utf-8 -*-
import multiprocessing

bind = "%s:%s" % ('0.0.0.0', '8080')
workers = multiprocessing.cpu_count()
worker_class = "gevent"
errorlog = "logs/error.log"
