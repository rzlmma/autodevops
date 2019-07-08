# -*- coding:utf-8 -*-
# __author__ = majing
import os
import json
import datetime
from concurrent import futures

from .models import ScriptTask



upload_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'static/uploads/')
dest_sql = '/opt/ansible/sql/'
dest_shell = '/opt/ansible/sh/'


def parse_asset_related_script(ca, assets):
    """
    {"new.sh": ['172.16.30.1', '172.16.30.2']}
    """
    rest = {}
    for asset in assets:
        scripts = asset.script
        for sc in scripts:
            if sc.category == ca:
                if sc.file_path not in rest:
                    rest[sc.file_path] = []
                rest[sc.file_path].append(asset)
    return rest


def gen_ansible_resource(assets):
    """
    获取主机的资源
    :param assets: 
    """
    rest = []
    for asset in assets:
        rest.append({"hostname": asset.ip, "ip": asset.ip, "port": asset.port, "username": asset.username,
                     "password": asset.password})
    return rest


def execute_script_remote_hosts(category, hosts, api):
    """
    在远程主机上执行脚本
    :return: 
    """
    from .. import db
    from .. import logger
    script_asset_relations = parse_asset_related_script(category, hosts)
    logger.info("execute_script_remote_hosts: %s" % script_asset_relations)

    for file, host_list in script_asset_relations.items():
        if not host_list:
            continue
        file_path = os.path.join(upload_dir, file)

        task = ScriptTask()
        task.name = "execute_%s_%s" % (category, file)
        task.assets.extend(host_list)
        db.session.add(task)
        db.session.commit()

        unique_id = task.id
        host_list_str = [asset.ip for asset in host_list]
        try:
            dest_path = dest_sql if category == 'sql' else dest_shell
            co_result = api.copy_file(host_list_str, src=file_path, dest=dest_path)
            logger.info("copy result: %s" % co_result)
        except Exception as exc:
            old_task = db.session.query(ScriptTask).filter_by(id=unique_id).first()
            old_task.status = True
            old_task.detail = "copy file error msg: %s" % (exc.message)
        else:
            try:
                cmd = "bash %s" % os.path.join(dest_shell, file)
                logger.info('cmd: %s' % cmd)

                exc_result = api.exec_script(host_list_str, cmd)
                logger.info("execute shell result: %s" % exc_result)
            except Exception as exc:
                old_task = db.session.query(ScriptTask).filter_by(id=unique_id).first()
                old_task.status = True
                old_task.detail = "execute file error msg: %s" % (exc.message)
            else:
                msg = "copy: %s         execute: %s " % (json.dumps(co_result), json.dumps(exc_result))
                old_task = db.session.query(ScriptTask).filter_by(id=unique_id).first()
                old_task.status = True
                old_task.detail = msg
        db.session.commit()


def async_execute_script(category, task_id, hosts, file_path, api):
    with futures.ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(execute_script_remote_hosts, category, task_id, hosts, file_path, api)
        print("future: ", future.done())
        future.result()


def execute_sql_script(dbs, api, host_list_str):
    """
    执行sql脚本 
    """
    from .. import db

    instance = dbs[0]
    file_name = instance.script
    src_path = os.path.join(upload_dir, file_name)
    task = ScriptTask()
    task.name = "execute_%s" % file_name
    db.session.add(task)
    db.session.commit()

    unique_id = task.id
    try:
        dest_path = dest_sql
        co_result = api.copy_file(host_list_str, src=src_path, dest=dest_path)
    except Exception as exc:
        old_task = db.session.query(ScriptTask).filter_by(id=unique_id).first()
        old_task.status = True
        old_task.detail = "copy file error msg: %s" % (exc.message)
    else:
        try:
            cmd = "mysql -u%s -p%s -h%s -P%s<%s" %(instance.db_user, instance.db_passwd, instance.host, instance.port,
                                                 os.path.join(dest_path, file_name))
            exc_result = api.exec_script(host_list_str, cmd)
        except Exception as exc:
            old_task = db.session.query(ScriptTask).filter_by(id=unique_id).first()
            old_task.status = True
            old_task.detail = "execute file error msg: %s" % (exc.message)
        else:
            msg = "copy: %s         execute: %s " % (json.dumps(co_result), json.dumps(exc_result))
            old_task = db.session.query(ScriptTask).filter_by(id=unique_id).first()
            old_task.status = True
            old_task.detail = msg
    db.session.commit()