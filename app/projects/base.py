# -*- coding:utf-8 -*-
# __author__ = majing
import paramiko
import smtplib
from email.header import Header
from email.mime.text import MIMEText
import time
from concurrent.futures import ThreadPoolExecutor

from flask import g

from ..asset.models import Asset
from .. import db, logger
from .models import PubItem, Record, Nginx


class ParamikoAPI(object):
    def __init__(self, hostname, port=22, username=None, password=None):
        self.hostname = hostname
        self.port = port
        self.username = username
        self.password = password

    def _client(self):
        client = paramiko.client.SSHClient()
        client.set_missing_host_key_policy(paramiko.client.AutoAddPolicy())
        client.connect(self.hostname, self.port, self.username, self.password)
        return client

    def execute_cmd(self, cmd):
        stdin, stdout, stderr = self.client.exec_command(cmd)
        return stdin, stdout, stderr

    def __enter__(self):
        self.client = self._client()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.client.close()
        del self


def pre_deploy(project_id, asset_id):
    """
    预发布部署
    :return: 
    """

    project = db.session.query(PubItem).get(project_id)
    asset = db.session.query(Asset).get(asset_id)
    record = Record(name=project.item_name, operate=u"部署", env=u"预发布", resource=asset.name)
    if not project or not asset:
        record.status = False
        record.detail = u"project or asset is None: project_id: %s     asset_id: %s" % (project_id, asset_id)
        db.session.add(record)
        db.session.commit()
        return

    type = project.item_type
    branch = project.new_version
    msg = ''
    logger.info("project_name: %s        project_type: %s    branch: %s" % (project.item_name, type, branch))
    cmds = []
    try:
        with ParamikoAPI(asset.ip, asset.port, asset.username, asset.password) as client:
            if type == 1:  # 如果是tomcat
                # kill process
                kill_process = " " % project.item_name

                rm_package = "cd %s && rm -rf %s  && sleep 1" % (project.pre_deploy_path, project.item_name) # 移除旧包

                # 最新代码解压到指定目录
                mv_newpackage = "cd %s && mkdir %s  && scp -P 22 xxxx@xxxxx:/data/%s/target_pre/%s . && unzip %s -d ./%s" % (
                project.pre_deploy_path, project.item_name, project.item_name, branch, branch, project.item_name)

                # 启动tomcat
                start_tomcat = "sh %s" % (project.pre_startsh)
                cmds = [kill_process, rm_package, mv_newpackage, start_tomcat]
            elif type == 2:  # 微服务
                kill_process = " "  # 杀死进程
                rm_package = "cd %s && rm -rf %s  && sleep 3" % (project.pre_deploy_path,
                                                                                         project.item_name)  # 删除旧包

                mv_newpackage = "cd %s  && scp -P 22 xxxx@xxxxxx:/data//%s/target_pre/%s" \
                                " . && tar zxvf  %s " % (project.pre_deploy_path, project.item_name, branch, branch)     # 复制新包
                start_service = "sh %s" % project.pre_startsh       # 重启服务
                cmds = [kill_process, rm_package, mv_newpackage, start_service]
            elif type == 3:  # 静态资源
                rm_package = "cd %s && rm -rf * " % (project.pre_deploy_path)  # 删除旧静态资源
                mv_newpackage = "cd %s && scp -P 22 xxxx@xxxx:/data/%s/target_pre/%s . && tar zxvf  %s " % (
                project.pre_deploy_path, project.item_name, branch, branch)
                cmds = [rm_package, mv_newpackage]

            for cmd in cmds:
                _, stdout, stderr = client.execute_cmd(cmd)
                logger.info("cmd: [%s]  result: %s" % (cmd, stdout.read()))
                if stderr.read():
                    msg += "%s  " % stderr.read()

    except Exception as exc:
        record.status = False
        record.detail = exc.message
    finally:
        if msg.strip():
            record.detail = msg
            record.status = False
        db.session.add(record)
        db.session.commit()
        return msg.strip()


def get_new_version(project):
    """
    更新生产代码版本
    """

    project.online_version = project.new_version                  # 线上版本存到数据库
    db.session.commit()


def get_old_version(project, version):
    """
    点击回滚后，把线上版本号更新为要回滚的版本号
    """

    project.online_version=version
    db.session.commit()


def ssh_login(asset, cmd):
    """
    建立需要sudo的ssh连接
    """
    pwd = ""
    content = errmsg = ''
    try:
        with ParamikoAPI(asset.ip, asset.port, asset.username, asset.password) as client:
            stdin, stdout, stderr = client.execute_cmd(cmd)
            stdin.write("%s\n"%pwd)
            stdin.flush()
            content = stdout.read()
            if stderr.read():
                errmsg = stderr.read()
    except Exception as e:
        errmsg = "ssh_login: cmd: %s   error:%s" % (cmd, e.message)
    return content, errmsg


def nginxconfig(item_obj, nginx_obj):
    """
    注释配置文件后reload  添加Nginx注释
    """
    error = ''
    nginx_proxy = item_obj.nginx_proxy
    nginx_proxys = nginx_proxy.split(",")
    for i in nginx_proxys:
        host_obj = db.session.query(Asset).filter_by(name=i).first()
        if not host_obj:
            msg = "asset is None: name: %s " % i
            error += ' %s\n' % msg
            continue
        nginx_cmd = "sudo %s" % nginx_obj.command  # 没有加reload
        reload_nginx_cmd = "sudo /usr/nginx -s reload"
        for cmd in [nginx_cmd, reload_nginx_cmd]:
            content, errmsg = ssh_login(host_obj, cmd)
            logger.info("[nginxconfig]  cmd:[%s]    content: %s" % (cmd, content))
            if errmsg:
                error += "%s\n" % errmsg
    return error


def kill_process(res_pid, host_obj):
    """
    杀服务进程
    """
    errmsg = ''
    pid_list = res_pid.split("\n")
    pid_list.pop()
    for i in pid_list:
        kill_tomcat = "sudo kill -9 %s" % i
        content, msg = ssh_login(host_obj, kill_tomcat)
        logger.info("[kill_process]  cmd: %s    content:%s " % (kill_tomcat, content))
        if msg:
            errmsg += "%s\n" % msg
    return errmsg


def code_online(item_obj, host_obj):
    """生产发版"""
    item_name = item_obj.item_name
    host = host_obj.name
    nginx_obj = db.session.query(Nginx).filter_by(item=item_name, host=host).first()
    errmsg = ''
    commands = []
    if item_obj.item_type == 1:   # tomcat项目
        msg = nginxconfig(item_obj, nginx_obj)            # 修改nginx
        if msg:
            errmsg += msg

        # 操作tomcat
        cmd = "ps -ef |grep -w %s |grep -v grep |awk '{print $2}' " % item_name   # kill tomcat
        content, err = ssh_login(host_obj, cmd)
        if not err:
            message = kill_process(content.decode(), host_obj)
            if message:
                errmsg += "  %s\n" % message
        else:
            errmsg += " kill tomcat failed:%s" % err

        # 返回产品库最新的版本
        new_package = item_obj.new_version
        cmd1 = "sudo  rm -rf %s/*" % item_obj.prd_deploy_path
        cmd2 = "sh /data/copy.sh %s %s %s"%(item_obj.prd_deploy_path,item_name,new_package)
        cmd3 = "cd %s && sudo unzip %s"%(item_obj.prd_deploy_path,new_package)
        cmd4 = "cd %s && sudo rm -rf  %s"%(item_obj.prd_deploy_path,new_package)
        commands = [cmd1, cmd2, cmd3, cmd4]

    elif item_obj.item_type == 2:
        cmd6 = "ps -ef |grep -w %s |grep -v grep |awk '{print $2}'"%item_name  #获取进程号
        res_pid, msg = ssh_login(host_obj, cmd6)
        if msg:
            errmsg += '%s\n' % msg
        else:
            message = kill_process(res_pid.decode(), host_obj)
            if message:
                errmsg += " %s\n" % message

        new_package = db.session.query(PubItem).filter_by(item_name=item_name).first().new_version
        cmd1 = "sudo  rm -rf %s/%s"%(item_obj.prd_deploy_path,item_name)  #删除老代码
        cmd2 = "sh /data/copy.sh %s %s %s"%(item_obj.prd_deploy_path,item_name,new_package)  #复制最新的包到部署目录
        cmd3 = "cd %s && sudo tar zxvf %s"%(item_obj.prd_deploy_path,new_package)  # 解压到部署目录
        cmd4 = "cd %s && sudo rm -rf  %s"%(item_obj.prd_deploy_path,new_package)  # 删除项目路径下的压缩包
        commands = [cmd1, cmd2, cmd3, cmd4]

    elif item_obj.item_type == 3:
        new_package = item_obj.new_version
        cmd1 = "''sudo  rm -rf %s/*" % (item_obj.prd_deploy_path)  # 删除老代码
        cmd2 = "sh /data/copy.sh %s %s %s"%(item_obj.prd_deploy_path,item_name,new_package)  # 复制最新的包到部署目录
        cmd3 = "cd %s && sudo tar zxvf %s" % (item_obj.prd_deploy_path, new_package)  # 解压到部署目录
        commands = [cmd1, cmd2, cmd3]

    for cmd in commands:
        content, msg = ssh_login(host_obj, cmd)
        logger.info("cmd: %s     content:%s" % (cmd, content))
        if msg:
            errmsg += " %s\n" % msg
    return errmsg


def sendmail_RD(username,item_name):
    """
    发邮件
    """
    from_addr = "xxxx@xxx.com"
    password = ""
    to_addr = [username]
    to = ','.join(to_addr)
    smtp_server = "mail.xxxx.com"
    content = '<div>上线提醒： %s项目 代码上线验证通过后请及时合并回 master 点击跳转到合并分支页面.如已合并请忽略该提示</div> '%(item_name)
    msg = MIMEText(content, _subtype='html', _charset='utf-8')
    msg['From'] = 'xxxx@xxxx.com'
    msg['To'] = to
    msg['Subject'] = Header('上线提醒', 'utf-8').encode()
    logger.info("启动定时器，邮件提醒10分钟后发送")
    time.sleep(600)
    try:
        server = smtplib.SMTP(smtp_server, 25)
        server.sendmail(from_addr, to_addr, msg.as_string())
        logger.info("send email successful")
        return True
    except smtplib.SMTPException as e:
        logger.info("sendemail Error : ", e)
        return False


def pro_deplay(project_id, asset_id):
    """
    生产环境部署
    :return: 
    """
    project = db.session.query(PubItem).get(project_id)
    asset = db.session.query(Asset).get(asset_id)
    record = Record(name=project.item_name, operate=u"部署", env=u"生产", resource=asset.name)
    if not project or not asset:
        record.status = False
        record.detail = u"project or asset is None: project_id: %s     asset_id: %s" % (project_id, asset_id)
        db.session.add(record)
        db.session.commit()
        return
    try:
        get_new_version(project)  # 处理版本号
        message = code_online(project, asset)  # 生产代码发布

        if message.strip():
            record.status = False
            record.detail = message

        pool1 = ThreadPoolExecutor(1)
        pool1.submit(sendmail_RD, g.user.username, project.item_name)
    except Exception as exc:
        record.status = False
        record.detail = exc.message
    finally:
        db.session.add(record)
        db.session.commit()
        return message.strip()


def pro_rollback(asset_id, project_id, version):
    """
    代码回滚
    :return: 
    """
    project = db.session.query(PubItem).get(project_id)
    asset = db.session.query(Asset).get(asset_id)
    record = Record(name=project.item_name, operate=u"回滚", env=u"生产", resource=asset.name)
    if not project or not asset:
        record.status = False
        record.detail = u"project or asset is None: project_id: %s     asset_id: %s" % (project_id, asset_id)
        db.session.add(record)
        db.session.commit()
        return
    errmsg = ''
    try:
        if project.item_type == 1:  #tomcat项目
            cmd = "ps -ef |grep %s |grep -v grep |awk '{print $2}' " % project.item_name  # kill tomcat
            res_pid, msg = ssh_login(asset, cmd)
            if not msg:
                message = kill_process(res_pid.decode(), asset)  # 杀死进程
                if message:
                    errmsg += ' kill process error: %s\n' % message
            else:
                errmsg += '%s\n' % msg

            cmd1 = "sudo  rm -rf %s/*" % (project.prd_deploy_path)  # 删除就得代码
            contet, msg = ssh_login(asset, cmd1)
            logger.info("cmd:%s    content: %s" %(cmd1, contet))

            get_old_version(project, version)  # 更新生产环境的代码版本号

            cmd2 = "sh /data/copy.sh %s %s %s" % (
            project.prd_deploy_path, project.item_name, version)

            cmd3 = "cd %s && sudo unzip %s" % (project.prd_deploy_path, version)
            cmd4 = "cd %s && sudo rm -rf  %s" % (project.prd_deploy_path, version)
            cmd5 = "sudo sh %s" % project.prd_startsh  # 执行启动脚本

            for cmd in [cmd2, cmd3, cmd4, cmd5]:
                content, msg = ssh_login(asset, cmd)
                logger.info("cmd: %s         content:%s" % (contet, msg))
                if msg:
                    errmsg += ' %s\n' % msg

        elif project.item_type == 2:
            cmd = "ps -ef |grep %s |grep -v grep |awk '{print $2}' " % project.item_name  # kill tomcat
            res_pid, msg = ssh_login(asset, cmd)
            if msg:
                errmsg += ' %s\n' % msg
            else:
                message = kill_process(res_pid.decode(), asset)  # 杀死进程
                if message:
                    errmsg += ' %s\n' % message

            cmd1 = "sudo  rm -rf %s/%s" % (project.prd_deploy_path, project.item_name)  # 删除就得代码
            contet, msg = ssh_login(asset, cmd1)
            logger.info("cmd: %s         content: %s" %(cmd1, contet))
            if msg:
                errmsg += ' %s\n' % msg

            get_old_version(project, version)  # 更新生产环境的代码版本号

            cmd2 = "sh /data/copy.sh %s %s %s" % (project.prd_deploy_path,
                                                                        project.item_name, version)  # 复制最新的包到部署目录
            cmd3 = "cd %s && sudo tar zxvf %s" % (project.prd_deploy_path, version)  # 解压到部署目录

            cmd4 = "cd %s && sudo rm -rf  %s" % (project.prd_deploy_path, version)  # 删除项目路径下的压缩包
            cmd5 = "sudo sh %s" % project.prd_startsh  # 执行启动脚本

            for cmd in [cmd2, cmd3, cmd4, cmd5]:
                content, msg = ssh_login(asset, cmd)
                logger.info("cmd: %s         content: %s" % (cmd1, contet))
                if msg:
                    errmsg += ' %s\n' % msg

        elif project.item_type == 3:
            cmd1 = "sudo  rm -rf %s/*" % (project.prd_deploy_path)  # 删除旧代码
            content, msg = ssh_login(asset, cmd1)
            logger.info("cmd: %s         content: %s" % (cmd1, content))
            if msg:
                errmsg += ' %s\n' % msg

            get_old_version(project, version)

            cmd2 = "sh /data/copy.sh %s %s %s" % (project.prd_deploy_path, project.item_name, version)  # 复制最新的包到部署目录
            cmd3 = "cd %s && sudo tar zxvf %s" % (project.prd_deploy_path, version)  # 解压到部署目录
            for cmd in [cmd2, cmd3]:
                content, msg = ssh_login(asset, cmd)
                logger.info("cmd: %s         content: %s" % (cmd1, content))
                if msg:
                    errmsg += ' %s\n' % msg
        if errmsg.strip():
            record.status = False
            record.detail = errmsg
    except Exception as exc:
        record.status = False
        record.detail = exc.message
    finally:
        db.session.add(record)
        db.session.commit()
        return errmsg.strip()


def nginxconfig_2(item_obj, nginx_obj):
    """
    取消注释后reload
    """
    tmp = item_obj.nginx_proxy
    list = tmp.split(",")
    errmsg = ''
    for i in list:
        host_obj = db.session.query(Asset).filter_by(name=i).first()
        cmd = "sudo %s" % nginx_obj.command_re  # 没有加reload
        reload_nginx_cmd = "''sudo /usr/nginx -s reload"
        for cmd in [cmd, reload_nginx_cmd]:
            content, msg = ssh_login(host_obj, cmd)
            logger.info("cmd: %s           content:%s" % (cmd, content))
            if msg:
                errmsg += ' %s\n' % msg
    return errmsg


def nginx_to_join(pro_id, host_id):
    """
    用来取消Nginx的注释，加入到集群
    """
    project = db.session.query(PubItem).get(pro_id)
    asset = db.session.query(Asset).get(host_id)
    record = Record(name=project.item_name, operate=u"加入集群", env=u"生产", resource=asset.name)
    msg = ''
    if not project or not asset:
        record.status = False
        record.detail = u"project or asset is None: project_id: %s     asset_id: %s" % (pro_id, host_id)
        db.session.add(record)
        db.session.commit()
        return

    if project.item_type == 2:
        record.detail = u"项目类型为2 不做处理"
        db.session.add(record)
        db.session.commit()
        return
    try:
        nginx_obj = db.session.query(Nginx).filter_by(item=project.item_name, host=asset.name).first()
        msg = nginxconfig_2(project, nginx_obj)
        if msg.strip():
            record.status = False
            record.detail = msg
    except Exception as exc:
        record.status = False
        record.detail = exc.message
    finally:
        db.session.add(record)
        db.session.commit()
        return msg.strip()
