
from django.db import models
from django.contrib.auth.models import AbstractUser


class Semester(models.Model):
    sem_name = models.CharField(max_length=100, verbose_name='学期名')
    start_date = models.DateField(verbose_name='开始日期')
    end_date = models.DateField(verbose_name='结束日期')

    class Meta:
        verbose_name = '学期表'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.sem_name


class Course(models.Model):
    course_name = models.CharField(max_length=50, verbose_name='课程名')

    class Meta:
        verbose_name = '课程表'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.course_name


class Teacher(models.Model):
    GENDER_CHOICES = (
        ('1', '男'),
        ('2', '女'),
    )

    tea_ID = models.CharField(max_length=10, primary_key=True, verbose_name='教师工号')
    teacher_name = models.CharField(max_length=50, verbose_name='教师姓名')
    password = models.CharField(max_length=100, verbose_name='密码')
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, verbose_name='性别')
    education = models.CharField(max_length=50, blank=True, null=True, verbose_name='学历')
    major = models.CharField(max_length=50, blank=True, null=True, verbose_name='专业')
    join_date = models.DateField(blank=True, null=True, verbose_name='入校时间')
    is_working = models.BooleanField(default=True, verbose_name='是否在职')

    class Meta:
        verbose_name = '教师表'
        verbose_name_plural = verbose_name

    def __str__(self):
        return f"{self.teacher_name} ({self.tea_ID})"


class Classes(models.Model):
    GRADE_CHOICES = (
        (7, '七年级'),
        (8, '八年级'),
        (9, '九年级'),
    )

    grade_num = models.SmallIntegerField(choices=GRADE_CHOICES, verbose_name='年级')
    clas_num = models.SmallIntegerField(verbose_name='班级')
    class_name = models.CharField(max_length=50, verbose_name='班级名')
    sem_ID = models.ForeignKey(Semester, on_delete=models.CASCADE, verbose_name='学期')
    headteacher = models.ForeignKey(Teacher, on_delete=models.CASCADE, verbose_name='班主任ID')

    class Meta:
        verbose_name = '班级表'
        verbose_name_plural = verbose_name
        unique_together = ('grade_num', 'clas_num', 'sem_ID')

    def __str__(self):
        return self.class_name


class Teaching(models.Model):
    tea_ID = models.ForeignKey(Teacher, on_delete=models.CASCADE, verbose_name='教师工号')
    cla_ID = models.ForeignKey(Classes, on_delete=models.CASCADE, verbose_name='班级')
    cou_ID = models.ForeignKey(Course, on_delete=models.CASCADE, verbose_name='课程')

    class Meta:
        verbose_name = '教师任课表'
        verbose_name_plural = verbose_name
        unique_together = ('tea_ID', 'cla_ID', 'cou_ID')

    def __str__(self):
        return f"{self.tea_ID} - {self.cla_ID} - {self.cou_ID}"


class Student(models.Model):
    GENDER_CHOICES = (
        ('1', '男'),
        ('2', '女'),
    )

    stu_ID = models.CharField(max_length=10, primary_key=True, verbose_name='学生学号')
    student_name = models.CharField(max_length=50, verbose_name='学生姓名')
    password = models.CharField(max_length=100, verbose_name='密码')
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, verbose_name='性别')
    enrollment_date = models.DateField(blank=True, null=True, verbose_name='入学年月')
    is_studying = models.BooleanField(default=True, verbose_name='是否在校')
    current_class = models.ForeignKey(Classes, on_delete=models.SET_NULL, null=True, verbose_name='当前班级')

    class Meta:
        verbose_name = '学生表'
        verbose_name_plural = verbose_name

    def __str__(self):
        return f"{self.student_name} ({self.stu_ID})"


class Exam(models.Model):
    sem_ID = models.ForeignKey(Semester, on_delete=models.CASCADE, verbose_name='学期')
    exam_type = models.CharField(max_length=100, verbose_name='考试类别名')
    start_date = models.DateField(verbose_name='考试开始日期')
    end_date = models.DateField(verbose_name='考试结束日期')
    is_lock = models.BooleanField(default=False, verbose_name='是否锁定')

    class Meta:
        verbose_name = '考试类别表'
        verbose_name_plural = verbose_name
        ordering = ['-start_date']

    def __str__(self):
        return f"{self.sem_ID} - {self.exam_type}"


class Score(models.Model):
    stu_ID = models.ForeignKey(Student, on_delete=models.CASCADE, verbose_name='学生学号')
    cla_ID = models.ForeignKey(Classes, on_delete=models.CASCADE, verbose_name='班级', null=True, blank=True)
    exam_ID = models.ForeignKey(Exam, on_delete=models.CASCADE, verbose_name='考试类别')
    cou_ID = models.ForeignKey(Course, on_delete=models.CASCADE, verbose_name='课程')
    score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, verbose_name='成绩')

    class Meta:
        verbose_name = '学生成绩表'
        verbose_name_plural = verbose_name
        unique_together = ('stu_ID', 'exam_ID', 'cou_ID')

    def __str__(self):
        return f"{self.stu_ID} - {self.exam_ID} - {self.cou_ID}: {self.score}"


class Admin(models.Model):
    admin_ID = models.CharField(max_length=10, primary_key=True, verbose_name='管理员ID')
    admin_name = models.CharField(max_length=50, verbose_name='管理员姓名')
    password = models.CharField(max_length=100, verbose_name='密码')

    class Meta:
        verbose_name = '管理员表'
        verbose_name_plural = verbose_name

    def __str__(self):
        return f"{self.admin_name} ({self.admin_ID})"
