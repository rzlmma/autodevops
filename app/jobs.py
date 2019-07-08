# -*- coding:utf-8 -*-
# __author__ = majing
from flask_apscheduler import APScheduler

scheduler = APScheduler()
scheduler.add_job('job1', 'app.asset.base:test', args='', trigger='interval', seconds=200)
