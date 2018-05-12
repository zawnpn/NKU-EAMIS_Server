#!/usr/bin/python3
# -*- coding: utf-8 -*-
# @Time    : 2017-07-01 11:03
# @Author  : Wanpeng Zhang
# @Site    : http://www.oncemath.com
# @File    : nkueamis.py
# @Project : NKU-EAMIS


import re
import requests
from bs4 import BeautifulSoup

HOME_URL = 'http://eamis.nankai.edu.cn'
LOGIN_URL = HOME_URL + '/eams/login.action'
STD_DETAIL_BASIC_URL = HOME_URL + '/eams/stdDetail.action'
STD_DETAIL_URL = HOME_URL + '/eams/stdDetail!innerIndex.action'
GRADE_URL = HOME_URL + '/eams/myPlanCompl!innerIndex.action'
COURSETABLE_QUERY_URL = HOME_URL + '/eams/dataQuery.action'
COURSETABLE_CLASS_URL = HOME_URL + '/eams/courseTableForStd.action'
COURSETABLE_ID_URL = HOME_URL + '/eams/courseTableForStd!innerIndex.action'
COURSETABLE_URL = HOME_URL + '/eams/courseTableForStd!courseTable.action'
EXAM_ID_URL = HOME_URL + '/eams/stdExam.action'
EXAM_URL = HOME_URL + '/eams/stdExam!examTable.action'
COURSE_CAT = ['校公共必修课', '院系公共必修课', '专业必修课', '专业选修课', '任选课']


# test the network
def test_net():
    conn = requests.get(LOGIN_URL)
    response_status = conn.status_code
    if response_status == '200':
        return False
    else:
        return True


# login to the system
def log_in(username, password):
    login_data = {
        'username': username,
        'password': password
    }
    s = requests.session()
    s.post(LOGIN_URL, data=login_data)
    return s


# find student's detail
def std_detail_pattern(content):
    pattern = re.compile(
        '姓名：</td>.*?<td>(.+?)</td>.*?院系：</td>.*?<td>(.+?)</td>.*?专业：</td>.*?<td>(.+?)</td>', re.S)
    detail = pattern.findall(content)
    return detail


# print detail of student on screen
def get_std_detail(sess):
    resp = sess.get(STD_DETAIL_URL + '?projectId=1')
    result = std_detail_pattern(resp.content.decode())
    if result:
        std_detail = result[0]
        return {'name': std_detail[0], 'school': std_detail[1], 'major': std_detail[2]}


# find the category of course
def find_course_cat(i, content):
    pattern = re.compile(COURSE_CAT[i-1])
    result = pattern.findall(content)
    return result


# convert str tuple into num tuple
def tuple_conv(strtuple):
    inttuple = []
    for i in strtuple:
        inttuple.append(int(i))
    return tuple(inttuple)


# replace some irregular words
def replace_some_word(text):
    replace_origin = ['Ⅰ', 'Ⅱ', 'Ⅲ', 'Ⅳ']
    replace_target = ['I', 'II', 'III', 'IV']
    for i in range(4):
        text = text.replace(replace_origin[i], replace_target[i])
    return text


# find the information of semester
def get_semester_info(data):
    pattern = re.compile('{id:(.+?),schoolYear:"(.+?)",name:"(.+?)"}', re.S)
    result = pattern.findall(data)
    return result


# determine the semester_id based on the <semester> arg
def determine_semester_id(sess, semester):
    semester = semester.split(':')
    semester_data = {'dataType': 'semesterCalendar'}
    resp = sess.post(COURSETABLE_QUERY_URL, data=semester_data)
    semester_info = get_semester_info(resp.content.decode())
    for i in semester_info:
        if list(i)[1:] == semester:
            semester_id = i[0]
            return semester_id
    print('Failed to find your semester, please make sure that you\'ve correctly inputed!')
    exit()


# get information of grades
def get_grade_info(i, table):
    result = []
    for info in table:
        if len(info('td')) == 8:
            result.append([replace_some_word(info('td')[2].text), info('td')[3].text, info('td')[5].text])
        if find_course_cat(i, info.text):
            result = []
        if i < 5 and find_course_cat(i+1, info.text):
            return result
    return result


# get grade information of specified courses
def get_specified_grade(resp, cat_list_str):
    result = []
    cat_list_num = [ord(i)-65 for i in cat_list_str]
    soup = BeautifulSoup(resp.content.decode(), 'html.parser')
    for i in cat_list_num:
        result.extend(get_grade_info(i+1, soup('tr')))
    return result
    # grade_dict = {}
    # for i in result:
    #     grade_dict[i[0]] = i[1:]
    # return grade_dict


def make_grade_markdown(table, category):
    md = '# %s类课程成绩\n\n课程 | 学分 | 成绩\n:---- | :----: | :----:\n' %category
    for i in table:
        if not i[2]:
            i[2] = '--'
        md += '%s | %s | %s\n' % (i[0], i[1], i[2])
    calc = grade_calc(table)
    md += '__合计__ | %d | %.4f' % (calc[1], calc[0])
    return md


# calculate the avg and sum of grade
def grade_calc(table):
    gradesum = 0
    scoresum = 0
    for i in table:

            try:
                if i[2] and i[2] != '--':
                    gradesum += float(i[1])*float(i[2].split(' ')[0])
                    scoresum += float(i[1])
            except ValueError:
                continue
    if scoresum:
        avg = gradesum/scoresum
    else:
        avg = 0
    return avg, scoresum


# get the necessary id to post data for course table
def get_std_course_id(resp):
    std_id_pattern = \
        re.compile('bg\.form\.addInput\(form,"ids","(.+?)"\);')
    std_id = std_id_pattern.findall(resp.content.decode())
    return std_id


# get information of courses
def get_course_info(resp):
    teacher_pattern = re.compile('var teachers = \[{id:.*?,name:"(.+?)",lab:.*?}\];')
    course_info_pattern = re.compile('\)","(.+?)\(\d+\)",".*?","(.+?)","\d+000"')
    course_time_pattern = re.compile('=(.+?)\*unitCount\+(.+?);')
    teacher_name = teacher_pattern.findall(resp.content.decode())
    course_info_iter = course_info_pattern.finditer(resp.content.decode())
    # test = course_info_pattern.findall(resp.content.decode())
    course_info = course_info_pattern.findall(resp.content.decode())
    course_pos = [i.start() for i in course_info_iter]
    course_info = [list(i) for i in course_info]
    course = []
    if len(course_pos)>1:
        for i in range(len(course_pos) - 1):
            course.append([tuple_conv(j) for j in course_time_pattern.findall(resp.content.decode(),
                                                                              course_pos[i], course_pos[i+1])])
        course.append([tuple_conv(j) for j in course_time_pattern.findall(resp.content.decode(), course_pos[i+1])])
    else:
        course.append([tuple_conv(j) for j in course_time_pattern.findall(resp.content.decode(),course_pos[0])])
    result = []
    for i in range(len(course_info)):
        result.append(course_info[i] + [teacher_name[i]] + course[i])
    return result


# struct course data to help make course table
def struct_course_data(sess, project_id, semester_id=None):
    project_id = str(project_id)
    sess.get(COURSETABLE_CLASS_URL + '?projectId=%s' % project_id)
    response = sess.get(COURSETABLE_ID_URL + '?projectId=%s' % project_id)
    if not semester_id:
        try:
            semester_id = re.findall('semester\.id=(.+?);', response.headers['Set-Cookie'])[0]
        except KeyError:
            print('Failed to get your courses, please check your username and password!')
            exit()
    result = get_std_course_id(response)
    if not result:
        print('Sorry, something went wrong, please close and try again!')
    else:
        course_ids = result[0]
        course_data = {
            'setting.kind': 'std',
            'semester.id': semester_id,
            'ids': course_ids
        }
        return course_data


# print the course table on screen
def get_course_table(sess, semester_id=None):
    course_data1 = struct_course_data(sess, '1', semester_id)
    courses1 = get_course_info(sess.post(COURSETABLE_URL, data=course_data1))
    sess.get(HOME_URL + '/eams/home.action')
    #course_data2 = struct_course_data(sess, '2', semester_id)
    #courses2 = get_course_info(sess.post(COURSETABLE_URL, data=course_data2))
    #courses = courses1 + courses2
    courses = courses1
    for c in courses:
        i = 4
        while(i<len(c)):
            if c[i][0] == c[3][0] and c[i][1] > c[i-1][1]:
                i += 1
            else:
                c.pop(i)
    return courses


def get_course_table_json(sess, semester_id=None):
    course_data1 = struct_course_data(sess, '1', semester_id)
    courses1 = get_course_info(sess.post(COURSETABLE_URL, data=course_data1))
    sess.get(HOME_URL + '/eams/home.action')
    #course_data2 = struct_course_data(sess, '2', semester_id)
    #courses2 = get_course_info(sess.post(COURSETABLE_URL, data=course_data2))
    courses = courses1
    for c in courses:
        i = 4
        while(i<len(c)):
            if c[i][0] == c[3][0] and c[i][1] > c[i-1][1]:
                i += 1
            else:
                c.pop(i)
    result = []
    for c in courses:
        tmp = {}
        tmp['day'] = c[3][0]+1
        tmp['begin'] = c[3][1]+1
        tmp['len'] = c[-1][1]-c[3][1]+1
        tmp['name'] = c[0] + '@' + c[1]
        result.append(tmp)
    return result


def struct_course_table(course_info, semester):
    sepa = '---'
    n = 1
    semester = semester.split(':')
    table = '# %s学年第%s学期课程表\n\n' % (semester[0], semester[1])
    table += '| - | 1 | 2 | 3 | 4 | 5 | 6 | 7 |\n'
    table += '|' + ' :------: |'*8 + '\n'
    mat = [['' for i in range(7)] for j in range(14)]
    for i in course_info:
        for j in i[3:]:
            mat[j[1]][j[0]] = i[0]
    for i in mat:
        table += '| %s |' % n
        for j in i:
            if j:
                table += ' %s |' % replace_some_word(j)
            else:
                table += ' %s |' % sepa
        table += '\n'
        n += 1
    return table


# get the exam id
def get_exam_id(sess, semester_id):
    headers = {'Cookie': 'JSESSIONID=%s; semester.id=%s' % (sess.cookies.items()[0][1], semester_id)}
    response = requests.get(EXAM_ID_URL, headers=headers)
    pattern = re.compile('\'/eams/stdExam!examTable\.action\?examBatch\.id=(.+?)\'')
    exam_id = pattern.findall(response.content.decode())
    if exam_id:
        return exam_id[0]
    else:
        print('暂无考试安排\n')
        exit()


# print the exam table on screen
def get_exam_table(sess, semester_id=None):
    if not semester_id:
        response = sess.get(EXAM_ID_URL)
        try:
            semester_id =re.findall('semester\.id=(.+?);', response.headers['Set-Cookie'])[0]
        except KeyError:
            print('Failed to get your exams, please check your username and password!')
    response = sess.get(EXAM_URL + '?examBatch.id=%s' % get_exam_id(sess, semester_id))
    text = response.content.decode()
    text = re.sub('<font color="BBC4C3">exam.*?noArrange</font>', '><', text)
    pattern = re.compile('<td>\d{4}</td><td>(.*?)</td><td>.*?</td>.*?<td>>*'
                         '(.*?)<*</td>.*?<td>>*(.*?)<*</td>.*?<td>.*?>(.*?)<.*?</td>.*?<td>正常</td>', re.S)
    exam_info = pattern.findall(text)
    return exam_info


def struct_exam_table(exam_info, semester):
    sepa = '---'
    n = 1
    semester = semester.split(':')
    table = '# %s学年第%s学期考试安排\n\n' % (semester[0], semester[1])
    table += '| -- | 课程名称 | 考试日期 | 考试时间 | 考试地点 |\n'
    table += '|' + ' :------: |' * 5 + '\n'
    for row in exam_info:
        table += '| %s |' % n
        for i in row:
            if i:
                table += ' %s |' % i
            else:
                table += ' %s |' % sepa
        table += '\n'
        n += 1
    return table

# main
def main():
    if test_net():
        username = ''
        password = ''
        sess = log_in(username, password)

        # print(get_std_detail(sess))

    else:
        print('Failed to connect the NKU-EAMIS system!\n')

if __name__ == '__main__':
    main()
