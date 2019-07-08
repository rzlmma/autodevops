# -*- coding:utf-8 -*-
# 项目启动脚本

gunicorn -c gunicorn_conf.py app:app
