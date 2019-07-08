# -*- coding:utf-8 -*-
# __author__ = majing

from wtforms import SelectField
from flask_appbuilder.fieldwidgets import  Select2Widget
from flask_appbuilder.forms import DynamicForm
from .models import PubItem
from .. import db
from ..asset.models import Asset


def get_projects():
    rest = []
    pros = db.session.query(PubItem).filter_by(branch_merge="待发布").all()
    for item in pros:
        rest.append((str(item.id), item.item_name))
    return rest


def get_project_asset(env='pre'):
    """
    pre: 预发布    pro: 生产
    :param env: 
    :return: 
    """
    rest = []
    pros = db.session.query(PubItem).filter_by(branch_merge="待发布").all()
    for pro in pros:
        if env == 'pre':
            if not pro.pre_hostname:
                continue
            assets = set()
            asset_names = pro.pre_hostname.split(',')
            for name in asset_names:
                obj = db.session.query(Asset).filter_by(name=name).first()
                if obj:
                    assets.add(obj)
        else:
            assets = pro.r
        for item in assets:
            host_name = item.name + '[%s]' % pro.item_name
            rest.append((str(item.id), host_name))
    return rest


def get_current_version():
    rest = []
    pros = db.session.query(PubItem).all()
    for pro in pros:
        if pro.online_version:
            name = pro.online_version + '[%s]' % pro.item_name
            rest.append((pro.online_version, name))
    return rest


def get_histroy_version():
    rest = []
    pros = db.session.query(PubItem).all()
    for pro in pros:
        if pro.history_version:
            histroys = pro.history_version.split(',')
            for item in histroys:
                rest.append((item, item+'[%s]'% pro.item_name))
    return rest


class PreForm(DynamicForm):
    """
    预发布环境部署
    """
    project = SelectField(u'项目', choices=(), widget=Select2Widget())
    asset = SelectField(u'主机', choices=(), widget=Select2Widget())

    def validate_on_submit(self):
        """Call :meth:`validate` only if the form is submitted.
        This is a shortcut for ``form.is_submitted() and form.validate()``.
        """
        # 重写validate函数
        return self.is_submitted()


class RollbackForm(DynamicForm):
    """
    生产环境代码回滚
    """
    project = SelectField(u'项目', choices=(), widget=Select2Widget())
    curr_version = SelectField(u'当前版本', choices=(), widget=Select2Widget())
    version = SelectField(u'回退版本', choices=(), widget=Select2Widget())
    asset = SelectField(u'主机', choices=(), widget=Select2Widget())

    def validate_on_submit(self):
        """Call :meth:`validate` only if the form is submitted.
        This is a shortcut for ``form.is_submitted() and form.validate()``.
        """
        return self.is_submitted()
