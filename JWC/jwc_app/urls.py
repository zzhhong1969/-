from django.urls import path
from . import views

urlpatterns = [
    # 登录/登出
    path('', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    # 学生功能
    path('student/dashboard/', views.student_dashboard, name='student_dashboard'),
    path('student/scores/', views.student_scores, name='student_scores'),
    path('student/change_password/', views.student_change_password, name='student_change_password'),

    # 教师功能
    path('teacher/dashboard/', views.teacher_dashboard, name='teacher_dashboard'),
    path('teacher/class_scores/', views.class_scores, name='class_scores'),
    path('teacher/student_scores/', views.student_scores_teacher, name='student_scores_teacher'),
    path('teacher/download_template/', views.download_template, name='download_template'),
    path('teacher/import_scores/', views.import_scores, name='import_scores'),
    path('teacher/change_password/', views.teacher_change_password, name='teacher_change_password'),

    # 管理员功能
    path('admin/dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin/manage_semester/', views.manage_students, name='manage_semester'),
    path('admin/manage_students/', views.manage_students, name='manage_students'),
    path('admin/manage_teachers/', views.manage_teachers, name='manage_teachers'),
    path('admin/manage_teaching/', views.manage_teaching, name='manage_teaching'),
    path('admin/manage_scores/', views.manage_scores, name='manage_scores'),
    path('admin/export_scores/', views.export_scores, name='export_scores'),
    path('admin/lock_exam/', views.lock_exam, name='lock_exam'),
    path('admin/reset_password/', views.reset_password, name='reset_password'),
    path('admin/backup_database/', views.backup_database, name='backup_database'),

    path('admin/manage_courses/', views.manage_courses, name='manage_courses'),
    path('admin/manage_semesters/', views.manage_semesters, name='manage_semesters'),

# 班级管理路由
    path('admin/manage_classes/', views.manage_classes, name='manage_classes'),
    path('admin/add_class/', views.add_class, name='add_class'),
    path('admin/update_class/<int:class_id>/', views.update_class, name='update_class'),
    #path('admin/delete_class/<int:class_id>/', views.delete_class, name='delete_class'),
    #path('admin/export_classes/', views.export_classes, name='export_classes'),
   # path('admin/download_class_template/', views.download_class_template, name='download_class_template'),
]