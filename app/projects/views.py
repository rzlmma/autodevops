# -*- coding:utf-8 -*-
# __author__ = majing
import os
from flask import flash

from flask_appbuilder.models.sqla.interface import SQLAInterface
from flask_appbuilder import PublicFormView
from flask import redirect

from ..common.util import CustomModelView
from .models import PubItem, Nginx, Record
from .forms import PreForm, RollbackForm, get_projects, get_project_asset, get_current_version, get_histroy_version
from .base import pre_deploy, pro_deplay, pro_rollback, nginx_to_join
from flask_appbuilder.security.sqla.models import User

class ProjectView(CustomModelView):
    datamodel = SQLAInterface(PubItem)

    list_title = u"项目列表"
    edit_title = u"项目编辑"
    show_title = u"项目详情"
    add_title = u"项目添加"

    label_columns = {"item_name": u"项目名称", u"format_item_type": u"项目类型", "format_r": u"线上主机", 'created_by': u"创建者",
                     'created_on':u"创建时间", "branch":u"分支", "prd_build_status": u"构建状态", 'new_version': u"最新版本",
                     'online_version': u'当前版本', 'pre_hostname': u'预发布主机'}

    list_columns = ['item_name', 'format_item_type', 'format_r', 'branch', 'prd_build_status', 'online_version',
                    'new_version', 'pre_hostname', 'created_by', 'created_on']

    description_columns = {"item_type": "1:tomcat   2:server    3:php      4:other", "r": u"项目上线要部署的主机",
                           "clone_path": u"默认路径"}

    show_columns = ['item_name', 'format_item_type', 'pre_log_file_path', 'prd_log_file_path', 'clone_path', 'build_dir',
                   'build_command', 'pre_deploy_path', 'pre_startsh', 'prd_build_command', 'prd_deploy_path', 'git_repo',
                   'branch', 'deploy_time', 'pre_hostname', 'format_r', 'nginx_proxy', 'vhost_file', 'prd_startsh',
                   'prd_build_status', 'new_version', 'online_version', 'history_version', 'branch_merge', 'is_elk',
                   'is_pinpoint', 'is_disconf', 'is_docker', 'created_by', 'created_on', 'changed_by', 'changed_on']
    add_columns = ['item_name', 'item_type', 'pre_log_file_path', 'prd_log_file_path', 'clone_path', 'build_dir',
                   'build_command', 'pre_deploy_path', 'pre_startsh', 'prd_build_command', 'prd_deploy_path', 'git_repo',
                   'branch', 'deploy_time', 'pre_hostname', 'r', 'nginx_proxy', 'vhost_file', 'prd_startsh',
                   'prd_build_status', 'new_version', 'online_version', 'history_version', 'branch_merge', 'is_elk',
                   'is_pinpoint', 'is_disconf', 'is_docker']  # 控制添加表单中字段的顺序
    edit_columns = ['item_name', 'item_type', 'pre_log_file_path', 'prd_log_file_path', 'clone_path', 'build_dir',
                   'build_command', 'pre_deploy_path', 'pre_startsh', 'prd_build_command', 'prd_deploy_path', 'git_repo',
                   'branch', 'deploy_time', 'pre_hostname', 'r', 'nginx_proxy', 'vhost_file', 'prd_startsh',
                   'prd_build_status', 'new_version', 'online_version', 'history_version', 'branch_merge', 'is_elk',
                   'is_pinpoint', 'is_disconf', 'is_docker']  # 控制编辑表单中字段的顺序
    order_columns = ['item_name', 'created_on']

    def pre_add(self, item):
        if item.item_name:
            if item.build_dir:
                item.build_dir = os.path.join(item.build_dir, item.item_name)
            if item.git_repo:
                item.git_repo = os.path.join(item.git_repo, item.item_name)


class PreView(PublicFormView):
    """
    预发布部署
    """
    form = PreForm
    form_title = u'预发布-部署(保存后就执行部署操作)'
    form_template = ''

    def form_get(self, form):
        form.project.choices = get_projects()
        form.asset.choices = get_project_asset(env='pre')

    def form_post(self, form):
        msg = pre_deploy(form.project.data, form.asset.data)
        if msg:
            flash('error: %s' % msg, 'info')
        else:
            flash('success', 'info')
        return redirect('recordview/list/')


class ProView(PublicFormView):
    """
    生产部署
    """
    form = PreForm
    form_title = u'生产环境-部署(保存后就执行部署操作)'

    def form_get(self, form):
        form.project.choices = get_projects()
        form.asset.choices = get_project_asset(env='pro')

    def form_post(self, form):
        msg = pro_deplay(form.project.data, form.asset.data)
        if msg:
            flash('error: %s' % msg, 'info')
        else:
            flash('success', 'info')
        return redirect('recordview/list/')


class ProRollbackView(PublicFormView):
    """
    生产回滚
    """
    form = RollbackForm
    form_title = u'生产环境-回滚(保存后就执行回滚操作)'

    def form_get(self, form):
        form.project.choices = get_projects()
        form.curr_version.choices = get_current_version()
        form.version.choices = get_histroy_version()
        form.asset.choices = get_project_asset(env='pro')

    def form_post(self, form):
        msg = pro_rollback(form.asset.data, form.project.data, form.version.data)
        if msg:
            flash('error: %s' % msg, 'info')
        else:
            flash('success', 'info')
        return redirect('recordview/list/')


class JoinColonyView(PublicFormView):
    """
    主机加入到集群    
    """
    form = PreForm
    form_title = u'生产环境-加入到集群(保存后执行加入集群操作)'

    def form_get(self, form):
        form.project.choices = get_projects()
        form.asset.choices = get_project_asset(env='pro')
        form.input.data = 'xcvbnm'

    def form_post(self, form):
        pro_id = form.project.data
        host_id = form.asset.data
        msg = nginx_to_join(pro_id, host_id)
        if msg:
            flash('error: %s' % msg, 'info')
        else:
            flash('success', 'info')
        return redirect('recordview/list/')


class NginxView(CustomModelView):
    datamodel = SQLAInterface(Nginx)

    list_title = u"nginx列表"
    edit_title = u"nginx编辑"
    show_title = u"nginx详情"
    add_title = u"nginx添加"

    list_columns = ['item', 'host', 'command', 'command_re', 'created_by', 'created_on']
    add_columns = ['item', 'host', 'command', 'command_re']
    edit_columns = ['item', 'host', 'command', 'command_re']
    show_columns = ['item', 'host', 'command', 'command_re', 'created_by', 'created_on']
    order_columns = ['item', 'host', 'created_on']


class RecordView(CustomModelView):
    base_permissions = ['can_list', 'can_show']
    datamodel = SQLAInterface(Record)

    list_title = u"操作记录列表"
    show_title = u"操作详情"

    list_columns = ['name', 'operate', 'env', 'resource', 'my_status', 'detail', 'created_by', 'created_on']
    show_columns = ['name', 'operate', 'env', 'resource','my_status', 'detail', 'created_by', 'created_on']
    order_columns = ['name', 'created_on']


