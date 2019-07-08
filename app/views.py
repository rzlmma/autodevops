# -*- coding:utf-8 -*-
from flask import render_template
from . import appbuilder, db
from .asset.views import ScriptTaskView, AssetView, ScriptView, DbModelView
from .projects.views import ProjectView, PreView, NginxView, RecordView, ProView, ProRollbackView, JoinColonyView

db.create_all()

# assets
appbuilder.add_view(ScriptView, "script", icon="fa-clipboard", category="Assets", category_icon="fa-desktop")
appbuilder.add_view(AssetView, "host", icon="fa-laptop", category="Assets", category_icon="fa-desktop")
appbuilder.add_view(DbModelView, "db", icon="fa-database", category="Assets", category_icon="fa-desktop")
appbuilder.add_view(ScriptTaskView, "task", icon="fa fa-bell-o", category="Assets", category_icon="fa-desktop")

# projects
appbuilder.add_view(ProjectView, "project", icon="fa-reorder", category="Projects", category_icon="fa-th-large")
appbuilder.add_view(NginxView, "nginx", icon="fa-newspaper-o", category="Projects", category_icon="fa-th-large")
appbuilder.add_view(PreView, "preproject", icon="fa-building-o", category="Projects", category_icon="fa-th-large")
appbuilder.add_view(ProView, "proproject", icon="fa-shopping-bag", category="Projects", category_icon="fa-th-large")
appbuilder.add_view(ProRollbackView, "prorollback", icon="fa-university", category="Projects", category_icon="fa-th-large")
appbuilder.add_view(JoinColonyView, "joincolony", icon="fa-cubes", category="Projects", category_icon="fa-th-large")
appbuilder.add_view(RecordView, "record", icon="fa-list-alt", category="Projects", category_icon="fa-th-large")

# monitor
appbuilder.add_link('LBS', '', icon="fa-rocket",
                    category="Monitor", category_icon="fa-sitemap")

appbuilder.add_link('ECS', '', icon="fa-magic",
                    category="Monitor", category_icon="fa-sitemap")

appbuilder.add_link('consume', '', icon="fa-microchip",
                    category="Monitor", category_icon="fa-sitemap")
appbuilder.add_link('service', '', icon="fa-lemon-o",
                    category="Monitor", category_icon="fa-sitemap")


@appbuilder.app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html', base_template=appbuilder.base_template, appbuilder=appbuilder), 404