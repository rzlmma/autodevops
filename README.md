# autodevops
使用flaskappbuilder开发的简版运维管理平台

它包含3大功能：用户管理，资产管理和项目部署，其中用户管理使用的是flask-appbuilder自带的功能

资产管理包含：主机管理，数据库管理，脚本管理，任务管理

项目部署包含：预发布环境部署，线上部署，线上代码回滚

用到的模块：
flask-appbuilder, ansible,sqlalchemy,paramiko

启动项目：

1.修改config.py中的sqlalchemy的配置

2.创建新用户，邮箱不能重复

flask fab create-admin

3.运行命令

开发环境：

python run.py

线上环境：

bash start.sh

项目日志：
logs目录下
