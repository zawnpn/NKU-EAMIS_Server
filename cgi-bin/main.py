#!/usr/bin/python3
# -*- coding: utf-8 -*-
# @Time    : 2017-08-20 12:17
# @Author  : Wanpeng Zhang
# @Site    : http://www.oncemath.com
# @File    : main.py
# @Project : nkueamis-web

import cgi
import json
from nkueamis import *

# import sys
# import io
# sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')


def start_response(resp="text/html"):
    return 'Content-type: ' + resp + '\n\n'


def test_server():
    print('success')


def return_detail(username, password):
    sess = log_in(username, password)
    return get_std_detail(sess)


def return_grade(username, password, category):
    sess = log_in(username, password)
    response = sess.get(GRADE_URL)
    grade = get_specified_grade(response, category)
    return make_grade_markdown(grade, category)


def return_course(username, password, semester):
    sess = log_in(username, password)
    sess.get(STD_DETAIL_URL + '?projectId=1')
    semester_id = determine_semester_id(sess, semester)
    course_info = get_course_table(sess, semester_id)
    return struct_course_table(course_info, semester)


def return_exam(username, password, semester):
    sess = log_in(username, password)
    sess.get(STD_DETAIL_URL + '?projectId=1')
    semester_id = determine_semester_id(sess, semester)
    exam_info = get_exam_table(sess, semester_id)
    return struct_exam_table(exam_info, semester)


if __name__ == '__main__':
    print(start_response('application/json'))
    from_data = cgi.FieldStorage()
    try:
        if from_data['test'].value == '1':
            test_server()
    except KeyError:
        pass

    try:
        username = from_data['username'].value
        password = from_data['password'].value

        if from_data['func'].value == 'detail':
            output = return_detail(username, password)
            print(json.dumps(output))

        elif from_data['func'].value == 'grade':
            output = return_grade(username, password, from_data['category'].value)
            print(output)

        elif from_data['func'].value == 'course':
            output = return_course(username, password, from_data['semester'].value)
            print(output)

        elif from_data['func'].value == 'exam':
            output = return_exam(username, password, from_data['semester'].value)
            print(output)
    except KeyError:
        print('请输入用户名及密码！')