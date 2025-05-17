from django.shortcuts import render, redirect, HttpResponse, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from .models import (
    Student, Teacher, Admin,
    Exam, Score, Classes,
    Course, Teaching, Semester
)
from django.db import transaction
import os
import pandas as pd
from datetime import datetime
from django.conf import settings
from .models import Classes, Teacher
from django.contrib.auth.hashers import make_password, check_password

#登录视图
def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user_type = request.POST.get('user_type')

        if user_type == 'student':
            try:
                student = Student.objects.get(student_name=username, password=password, is_studying=True)
                request.session['user_type'] = 'student'
                request.session['user_id'] = student.stu_ID
                return redirect('student_dashboard')
            except Student.DoesNotExist:
                messages.error(request, '学号或密码错误，或该学生已毕业')

        elif user_type == 'teacher':
            try:
                teacher = Teacher.objects.get(teacher_name=username, password=password, is_working=True)
                request.session['user_type'] = 'teacher'
                request.session['user_id'] = teacher.tea_ID
                return redirect('teacher_dashboard')
            except Teacher.DoesNotExist:
                messages.error(request, '工号或密码错误，或该教师已离职')

        elif user_type == 'admin':
            try:
                admin = Admin.objects.get(admin_name=username, password=password)
                request.session['user_type'] = 'admin'
                request.session['user_id'] = admin.admin_ID
                return redirect('admin_dashboard')
            except Admin.DoesNotExist:
                messages.error(request, '管理员账号或密码错误')

    return render(request, 'login.html')

#注销视图
def logout_view(request):
    request.session.flush()  # 清除所有session
    return redirect('login')  # 重定向到登录页面

#学生视图
def student_dashboard(request):
    if request.session.get('user_type') != 'student':
        return redirect('login')

    student_id = request.session.get('user_id')
    student = Student.objects.get(stu_ID=student_id)

    exams = Exam.objects.all().order_by('-start_date')

    context = {
        'student': student,
        'exams': exams,
    }
    return render(request, 'student/dashboard.html', context)

#学生查询成绩
def student_scores(request):
    if request.session.get('user_type') != 'student':
        return redirect('login')

    student_id = request.session.get('user_id')
    exam_id = request.GET.get('exam_id')

    student = Student.objects.get(stu_ID=student_id)
    exam = Exam.objects.get(pk=exam_id)

    scores = Score.objects.filter(stu_ID=student, exam_ID=exam).select_related('cou_ID')

    context = {
        'student': student,
        'exam': exam,
        'scores': scores,
    }
    return render(request, 'student/scores.html', context)

#学生更改密码
def student_change_password(request):
    if request.session.get('user_type') != 'student':
        return redirect('login')

    if request.method == 'POST':
        student_id = request.session.get('user_id')
        old_password = request.POST.get('old_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')

        try:
            student = Student.objects.get(stu_ID=student_id, password=old_password)
            if new_password == confirm_password:
                student.password = new_password
                student.save()
                messages.success(request, '密码修改成功')
            else:
                messages.error(request, '两次输入的新密码不一致')
        except Student.DoesNotExist:
            messages.error(request, '原密码错误')

    return render(request, 'student/change_password.html')
#教师视图
def teacher_dashboard(request):
    if request.session.get('user_type') != 'teacher':
        return redirect('login')

    teacher_id = request.session.get('user_id')
    teacher = Teacher.objects.get(tea_ID=teacher_id)

    # 获取该教师教授的班级
    classes = Classes.objects.filter(teaching__tea_ID=teacher).distinct()
    exams = Exam.objects.all().order_by('-start_date')

    context = {
        'teacher': teacher,
        'classes': classes,
        'exams': exams,
    }
    return render(request, 'teacher/dashboard.html', context)


def class_scores(request):
    if request.session.get('user_type') != 'teacher':
        return redirect('login')

    exam_id = request.GET.get('exam_id')
    class_id = request.GET.get('class_id')

    exam = Exam.objects.get(pk=exam_id)
    class_obj = Classes.objects.get(pk=class_id)

    # 获取该班级所有学生的成绩
    students = Student.objects.filter(current_class=class_obj)
    courses = Course.objects.filter(score__exam_ID=exam, score__stu_ID__in=students).distinct()

    # 构建成绩数据
    score_data = []
    for student in students:
        student_scores = []
        for course in courses:
            try:
                score = Score.objects.get(stu_ID=student, exam_ID=exam, cou_ID=course)
                student_scores.append(score.score)
            except Score.DoesNotExist:
                student_scores.append(None)

        score_data.append({
            'student': student,
            'scores': student_scores,
        })

    context = {
        'exam': exam,
        'class_obj': class_obj,
        'courses': courses,
        'score_data': score_data,
    }
    return render(request, 'teacher/class_scores.html', context)


def student_scores_teacher(request):
    if request.session.get('user_type') != 'teacher':
        return redirect('login')

    student_id = request.GET.get('student_id')
    exam_id = request.GET.get('exam_id')

    try:
        student = Student.objects.get(stu_ID=student_id)
        exam = Exam.objects.get(pk=exam_id)
        scores = Score.objects.filter(stu_ID=student, exam_ID=exam).select_related('cou_ID')

        # 计算总分和平均分
        total_score = sum(score.score for score in scores if score.score is not None)
        average_score = total_score / len(scores) if scores else 0

        context = {
            'student': student,
            'exam': exam,
            'scores': scores,
            'total_score': total_score,
            'average_score': round(average_score, 2)
        }
        return render(request, 'teacher/student_scores.html', context)

    except Exception as e:
        messages.error(request, f'查询失败: {str(e)}')
        return redirect('teacher_dashboard')

#导出模板
def download_template(request):
    if request.session.get('user_type') != 'teacher':
        return redirect('login')

    if request.method == 'POST':
        grade = request.POST.get('grade')
        exam_id = request.POST.get('exam_id')

        exam = Exam.objects.get(pk=exam_id)
        students = Student.objects.filter(current_class__grade_num=grade, is_studying=True)

        # 创建DataFrame
        data = {
            '学号': [],
            '姓名': [],
            '班级': [],
            '成绩': []
        }

        for student in students:
            data['学号'].append(student.stu_ID)
            data['姓名'].append(student.student_name)
            data['班级'].append(student.current_class.class_name)
            data['成绩'].append('')

        df = pd.DataFrame(data)

        # 保存到临时文件
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        filename = f"成绩模板_{exam.exam_type}_{grade}年级_{timestamp}.xlsx"
        filepath = os.path.join(settings.MEDIA_ROOT, 'templates', filename)

        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        df.to_excel(filepath, index=False)

        # 返回文件下载
        response = JsonResponse({'file_url': f'/media/templates/{filename}'})
        return response

    exams = Exam.objects.all().order_by('-start_date')
    return render(request, 'teacher/download_template.html', {'exams': exams})

#导出成绩
def import_scores(request):
    if request.session.get('user_type') != 'teacher':
        return redirect('login')

    if request.method == 'POST':
        exam_id = request.POST.get('exam_id')
        course_id = request.POST.get('course_id')
        excel_file = request.FILES.get('excel_file')

        try:
            exam = Exam.objects.get(pk=exam_id)
            course = Course.objects.get(pk=course_id)

            if exam.is_lock:
                messages.error(request, '该考试已锁定，不能导入成绩')
                return redirect('import_scores')

            df = pd.read_excel(excel_file)
            success_count = 0

            with transaction.atomic():
                for _, row in df.iterrows():
                    if pd.isna(row['学号']) or pd.isna(row['成绩']):
                        continue

                    try:
                        student = Student.objects.get(stu_ID=row['学号'])
                        Score.objects.update_or_create(
                            stu_ID=student,
                            exam_ID=exam,
                            cou_ID=course,
                            defaults={
                                'score': row['成绩'],
                                'cla_ID': student.current_class
                            }
                        )
                        success_count += 1
                    except Student.DoesNotExist:
                        continue

            messages.success(request, f'成功导入{success_count}条成绩记录')

            # 删除临时文件
            if hasattr(excel_file, 'temporary_file_path'):
                if os.path.exists(excel_file.temporary_file_path()):
                    os.remove(excel_file.temporary_file_path())

        except Exception as e:
            messages.error(request, f'导入失败: {str(e)}')

    exams = Exam.objects.all().order_by('-start_date')
    courses = Course.objects.all()
    return render(request, 'teacher/import_scores.html', {
        'exams': exams,
        'courses': courses
    })

#教师修改密码
def teacher_change_password(request):
    if request.session.get('user_type') != 'teacher':
        return redirect('login')

    if request.method == 'POST':
        teacher_id = request.session.get('user_id')
        old_password = request.POST.get('old_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')

        try:
            teacher = Teacher.objects.get(tea_ID=teacher_id, password=old_password)
            if new_password == confirm_password:
                teacher.password = new_password
                teacher.save()
                messages.success(request, '密码修改成功')
            else:
                messages.error(request, '两次输入的新密码不一致')
        except Teacher.DoesNotExist:
            messages.error(request, '原密码错误')

    return render(request, 'teacher/change_password.html')
#管理员视图


#学生管理
def manage_students(request):
    if request.session.get('user_type') != 'admin':
        return redirect('login')

    students = Student.objects.all()

    if request.method == 'POST' and 'excel_file' in request.FILES:
        try:
            excel_file = request.FILES['excel_file']
            df = pd.read_excel(excel_file)

            with transaction.atomic():
                for index, row in df.iterrows():
                    Student.objects.update_or_create(
                        stu_ID=row['学号'],
                        defaults={
                            'student_name': row['姓名'],
                            'gender': str(row['性别']),
                            'enrollment_date': row['入学年月'],
                            'is_studying': row['是否在读'],
                            'password': '123456'  # 默认密码
                        }
                    )

            messages.success(request, '学生信息导入成功')
        except Exception as e:
            messages.error(request, f'导入失败: {str(e)}')

    return render(request, 'admin/manage_students.html', {'students': students})

#教师管理
def manage_teachers(request):
    if request.session.get('user_type') != 'admin':
        return redirect('login')

    teachers = Teacher.objects.all()

    if request.method == 'POST' and 'excel_file' in request.FILES:
        try:
            excel_file = request.FILES['excel_file']
            df = pd.read_excel(excel_file)

            with transaction.atomic():
                for index, row in df.iterrows():
                    Teacher.objects.update_or_create(
                        tea_ID=row['工号'],
                        defaults={
                            'teacher_name': row['姓名'],
                            'gender': str(row['性别']),
                            'education': row['学历'],
                            'major': row['专业'],
                            'join_date': row['入校时间'],
                            'is_working': row['是否在校'],
                            'password': '123456'  # 默认密码
                        }
                    )

            messages.success(request, '教师信息导入成功')
        except Exception as e:
            messages.error(request, f'导入失败: {str(e)}')

    return render(request, 'admin/manage_teachers.html', {'teachers': teachers})

#任课管理
def manage_teaching(request):
    if request.session.get('user_type') != 'admin':
        return redirect('login')

    teachings = Teaching.objects.all()

    if request.method == 'POST' and 'excel_file' in request.FILES:
        try:
            excel_file = request.FILES['excel_file']
            df = pd.read_excel(excel_file)

            with transaction.atomic():
                for index, row in df.iterrows():
                    teacher = Teacher.objects.get(tea_ID=row['教师工号'])
                    class_obj = Classes.objects.get(class_name=row['班级'])
                    course = Course.objects.get(course_name=row['课程'])

                    Teaching.objects.update_or_create(
                        tea_ID=teacher,
                        cla_ID=class_obj,
                        cou_ID=course
                    )

            messages.success(request, '教师任课表导入成功')
        except Exception as e:
            messages.error(request, f'导入失败: {str(e)}')

    return render(request, 'admin/manage_teaching.html', {'teachings': teachings})

#成绩管理
def manage_scores(request):
    if request.session.get('user_type') != 'admin':
        return redirect('login')

    exams = Exam.objects.all().order_by('-start_date')

    if request.method == 'POST':
        exam_id = request.POST.get('exam_id')
        grade = request.POST.get('grade')
        excel_file = request.FILES.get('excel_file')

        try:
            exam = Exam.objects.get(pk=exam_id)

            if exam.is_lock:
                messages.error(request, '该考试已锁定，不能导入成绩')
                return redirect('manage_scores')

            # 读取Excel文件
            df = pd.read_excel(excel_file)

            with transaction.atomic():
                for index, row in df.iterrows():
                    student_id = row['学号']
                    student = Student.objects.get(stu_ID=student_id)
                    class_obj = student.current_class

                    # 遍历所有可能的课程列
                    for column in df.columns:
                        if column not in ['学号', '姓名', '班级']:
                            try:
                                course = Course.objects.get(course_name=column)
                                score_value = row[column]

                                if pd.notna(score_value):
                                    Score.objects.update_or_create(
                                        stu_ID=student,
                                        exam_ID=exam,
                                        cou_ID=course,
                                        defaults={
                                            'score': score_value,
                                            'cla_ID': class_obj
                                        }
                                    )
                            except Course.DoesNotExist:
                                continue

            messages.success(request, '成绩导入成功')

            # 删除上传的文件
            if os.path.exists(excel_file.temporary_file_path()):
                os.remove(excel_file.temporary_file_path())

        except Exception as e:
            messages.error(request, f'导入失败: {str(e)}')

    return render(request, 'admin/manage_scores.html', {'exams': exams})

#导出成绩
def export_scores(request):
    if request.session.get('user_type') != 'admin':
        return redirect('login')

    if request.method == 'POST':
        exam_id = request.POST.get('exam_id')
        grade = request.POST.get('grade')

        exam = Exam.objects.get(pk=exam_id)
        students = Student.objects.filter(current_class__grade_num=grade, is_studying=True)
        courses = Course.objects.filter(score__exam_ID=exam, score__stu_ID__in=students).distinct()

        # 创建DataFrame
        data = {
            '学号': [],
            '姓名': [],
            '班级': []
        }

        # 添加课程列
        for course in courses:
            data[course.course_name] = []

        # 填充数据
        for student in students:
            data['学号'].append(student.stu_ID)
            data['姓名'].append(student.student_name)
            data['班级'].append(student.current_class.class_name)

            for course in courses:
                try:
                    score = Score.objects.get(stu_ID=student, exam_ID=exam, cou_ID=course)
                    data[course.course_name].append(score.score)
                except Score.DoesNotExist:
                    data[course.course_name].append(None)

        df = pd.DataFrame(data)

        # 保存到临时文件
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        filename = f"成绩导出_{exam.exam_type}_{grade}年级_{timestamp}.xlsx"
        filepath = os.path.join(settings.MEDIA_ROOT, 'exports', filename)

        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        df.to_excel(filepath, index=False)

        # 返回文件下载
        response = JsonResponse({'file_url': f'/media/exports/{filename}'})
        return response

    exams = Exam.objects.all().order_by('-start_date')
    return render(request, 'admin/export_scores.html', {'exams': exams})

#成绩锁定
def lock_exam(request):
    if request.session.get('user_type') != 'admin':
        return redirect('login')

    if request.method == 'POST':
        exam_id = request.POST.get('exam_id')
        action = request.POST.get('action')

        exam = Exam.objects.get(pk=exam_id)

        if action == 'lock':
            exam.is_lock = True
            exam.save()
            messages.success(request, '考试已锁定')
        elif action == 'unlock':
            exam.is_lock = False
            exam.save()
            messages.success(request, '考试已解锁')

    exams = Exam.objects.all().order_by('-start_date')
    return render(request, 'admin/lock_exam.html', {'exams': exams})

#密码重置
def reset_password(request):
    if request.session.get('user_type') != 'admin':
        return redirect('login')

    if request.method == 'POST':
        user_type = request.POST.get('user_type')
        user_id = request.POST.get('user_id')

        try:
            if user_type == 'student':
                student = Student.objects.get(stu_ID=user_id)
                student.password = '123456'
                student.save()
                messages.success(request, f'学生 {student.student_name} 密码已重置为123456')
            elif user_type == 'teacher':
                teacher = Teacher.objects.get(tea_ID=user_id)
                teacher.password = '123456'
                teacher.save()
                messages.success(request, f'教师 {teacher.teacher_name} 密码已重置为123456')
        except Exception as e:
            messages.error(request, f'重置失败: {str(e)}')

    return render(request, 'admin/reset_password.html')


def backup_database(request):
    if request.session.get('user_type') != 'admin':
        return redirect('login')

    if request.method == 'POST':
        # 这里应该实现数据库备份逻辑
        # 实际项目中应该使用数据库备份工具或Django的dumpdata命令
        messages.success(request, '数据库备份功能将在实际部署时实现')

    return render(request, 'admin/backup_database.html')


def admin_dashboard(request):
    if request.session.get('user_type') != 'admin':
        return redirect('login')

    stats = {
        'student_count': Student.objects.filter(is_studying=True).count(),
        'teacher_count': Teacher.objects.filter(is_working=True).count(),
        'class_count': Classes.objects.count(),
        'exam_count': Exam.objects.count()
    }
    return render(request, 'admin/dashboard.html', stats)

#班级管理
def manage_classes(request):
    if request.session.get('user_type') != 'admin':
        return redirect('login')

    if request.method == 'POST' and 'excel_file' in request.FILES:
        try:
            df = pd.read_excel(request.FILES['excel_file'])
            with transaction.atomic():
                for _, row in df.iterrows():
                    semester = Semester.objects.get(sem_name=row['学期'])
                    headteacher = Teacher.objects.get(tea_ID=row['班主任工号'])

                    Classes.objects.update_or_create(
                        grade_num=row['年级'],
                        clas_num=row['班级'],
                        sem_ID=semester,
                        defaults={
                            'class_name': row['班级名称'],
                            'headteacher': headteacher
                        }
                    )
            messages.success(request, '班级信息导入成功')
        except Exception as e:
            messages.error(request, f'导入失败: {str(e)}')

    classes = Classes.objects.all()
    semesters = Semester.objects.all()
    teachers = Teacher.objects.filter(is_working=True)
    return render(request, 'admin/manage_classes.html', {
        'classes': classes,
        'semesters': semesters,
        'teachers': teachers
    })

#课程管理
def manage_courses(request):
    if request.session.get('user_type') != 'admin':
        return redirect('login')

    if request.method == 'POST':
        course_name = request.POST.get('course_name')
        if course_name:
            Course.objects.create(course_name=course_name)
            messages.success(request, '课程添加成功')

    courses = Course.objects.all()
    return render(request, 'admin/manage_courses.html', {'courses': courses})

#学期管理
def manage_semesters(request):
    if request.session.get('user_type') != 'admin':
        return redirect('login')

    if request.method == 'POST':
        sem_name = request.POST.get('sem_name')
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')

        if sem_name and start_date and end_date:
            Semester.objects.create(
                sem_name=sem_name,
                start_date=start_date,
                end_date=end_date
            )
            messages.success(request, '学期添加成功')

    semesters = Semester.objects.all()
    return render(request, 'admin/manage_semesters.html', {'semesters': semesters})



#增加班级
def add_class(request):
    if request.session.get('user_type') != 'admin':
        return redirect('login')

    if request.method == 'POST':
        try:
            semester = Semester.objects.get(sem_ID=request.POST['sem_ID'])
            teacher = Teacher.objects.get(tea_ID=request.POST['headteacher'])

            Classes.objects.create(
                grade_num=request.POST['grade_num'],
                clas_num=request.POST['clas_num'],
                class_name=request.POST['class_name'],
                sem_ID=semester,
                headteacher=teacher
            )
            messages.success(request, '班级添加成功')
        except Exception as e:
            messages.error(request, f'添加失败: {str(e)}')

    return redirect('manage_classes')

#导出班级
# def export_classes(request):
#     if request.session.get('user_type') != 'admin':
#         return redirect('login')
#
#     classes = Classes.objects.select_related('sem_ID', 'headteacher').all()
#
#     data = {
#         '年级': [c.get_grade_num_display() for c in classes],
#         '班级': [c.clas_num for c in classes],
#         '班级名称': [c.class_name for c in classes],
#         '学期': [c.sem_ID.sem_name for c in classes],
#         '班主任': [c.headteacher.teacher_name for c in classes],
#         '学期ID': [c.sem_ID.sem_ID for c in classes],
#         '班主任工号': [c.headteacher.tea_ID for c in classes]
#     }
#
#     df = pd.DataFrame(data)
#     response = HttpResponse(content_type='application/ms-excel')
#     response['Content-Disposition'] = 'attachment; filename="班级列表.xlsx"'
#     df.to_excel(response, index=False)
#     return response





def update_class(request, class_id):
    class_obj = get_object_or_404(Classes, id=class_id)

    if request.method == 'POST':
        # 手动从 POST 数据中获取字段并更新
        class_obj.name = request.POST.get('name')
        class_obj.grade = request.POST.get('grade')
        teacher_id = request.POST.get('teacher')
        if teacher_id:
            class_obj.teacher = Teacher.objects.get(id=teacher_id)
        class_obj.save()
        return redirect('manage_classes')  # 更新后跳转

    # 获取所有教师（用于下拉菜单）
    teachers = Teacher.objects.all()
    return render(request, 'jwc_app/update_class.html', {
        'class_obj': class_obj,
        'teachers': teachers,  # 传递给模板供选择
    })


def manage_semester(request, sem_id):
    pass