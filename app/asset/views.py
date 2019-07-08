# -*- coding:utf-8 -*-
# __author__ = majing

from flask_appbuilder.models.sqla.interface import SQLAInterface
from flask import redirect, make_response
from flask_appbuilder.actions import action

from ..common.util import CustomModelView
from ..common.ans_api import CustomAsi

from .base import gen_ansible_resource, execute_script_remote_hosts, execute_sql_script
from .models import Asset, Script, ScriptTask, DbModel

SQL_HOST_DEFAUTL = [
            {"hostname": "", "port": "", "username": "", "password": "",
             "ip": ''}]


class ScriptTaskView(CustomModelView):
    base_permissions = ['can_list', 'can_show']
    datamodel = SQLAInterface(ScriptTask)

    list_title = u"任务列表"
    edit_title = u"任务编辑"
    show_title = u"任务详情"
    add_title = u"任务添加"

    label_columns = {"name": u"任务名称", "status": u"是否执行完毕", "detail": u"详情",
                     u"created_by": u"创建者", u"created_on": u"创建时间", "changed_by": u"更新者",
                     "changed_on": u"更新时间", "asset_detail": u"关联主机", "asset_num": u"关联的主机数"}
    list_columns = ['name', 'status', 'asset_num', 'detail', 'created_by', 'created_on']
    show_columns = ['name', 'status', 'asset_detail', 'detail', 'created_by', 'created_on', 'changed_by', 'changed_on']
    order_columns = ['name', 'created_on']


class ScriptView(CustomModelView):
    datamodel = SQLAInterface(Script)

    list_title = u"脚本列表"
    edit_title = u"脚本编辑"
    show_title = u"脚本详情"
    add_title = u"脚本添加"

    list_columns = ['name', 'comment', 'file_path', 'category', 'created_by', 'created_on']
    show_columns = CustomModelView.show_columns.extend(['name', 'comment', 'file_path', 'creator', 'category'])
    add_columns = ['name', 'comment', 'creator', 'file_path', 'category']      # 控制添加表单中字段的顺序
    edit_columns = ['name',  'comment', 'creator', 'file_path', 'category']     # 控制编辑表单中字段的顺序
    order_columns = ['name', 'created_on']


class AssetView(CustomModelView):
    datamodel = SQLAInterface(Asset)
    related_views = [ScriptView]

    list_title = u"主机列表"
    edit_title = u"主机编辑"
    show_title = u"主机详情"
    add_title = u"主机添加"

    list_columns = ['name', 'ip', 'port', 'script_num', 'created_by', 'created_on']
    show_columns = CustomModelView.show_columns.extend(['name', 'ip', 'port','username'])
    add_columns = ['name', 'ip','port', 'username', 'password',  'script']      # 控制添加表单中字段的顺序
    edit_columns = ['name', 'ip', 'port', 'username', 'password',  'script']     # 控制编辑表单中字段的顺序
    description_columns = {"script": u"目前主机只能执行shell脚本，选择sql脚本无效"}
    order_columns = ['name', 'ip', 'port','created_on']

    @action("execute_shell", u"执行sh脚本", u"你确定要在所选机器上执行本机所关联的shell脚本？如果你不清楚，"
                                     u"可以在show里查看机器所关联的shell脚本", "fa-folder-open")
    def execute_shell(self, items):
        # 生成ansible所需的资源
        resources = gen_ansible_resource(items)

        # 初始化ansible接口
        api = CustomAsi(resources)

        # 在远程主机上执行脚本
        execute_script_remote_hosts('shell', items, api)
        return redirect('scripttaskview/list/')


class DbModelView(CustomModelView):
    datamodel = SQLAInterface(DbModel)

    list_title = u"数据库列表"
    edit_title = u"数据库编辑(保存后就执行sql脚本)"
    show_title = u"数据库详情"
    add_title = u"数据库添加"

    list_columns = ['name', 'host', 'port', 'created_by', 'created_on']
    show_columns = ['name', 'host', 'port', 'db_user', 'db_passwd', 'script', 'created_by', 'created_on', 'changed_by',
                    'changed_on']
    add_columns = ['name', 'host', 'port',  'db_user', 'db_passwd', 'script']  # 控制添加表单中字段的顺序
    edit_columns = ['name', 'host', 'port', 'db_user', 'db_passwd', 'script']  # 控制编辑表单中字段的顺序
    order_columns = ['name', 'created_on']

    def post_add(self, item):
        if item.script:
            resources = SQL_HOST_DEFAUTL
            api = CustomAsi(resources)
            execute_sql_script([item], api, host_list_str=[resources[0].get('ip')])

    def post_update(self, item):
        if item.script:
            resources = SQL_HOST_DEFAUTL
            api = CustomAsi(resources)
            execute_sql_script([item], api, host_list_str=[resources[0].get('ip')])

