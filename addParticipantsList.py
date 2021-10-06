from openpyxl import Workbook
import openpyxl
import pymysql
from constants import host, user, password, db_name, port, teachers, classes, id_admin, \
    filepath_user_photo, filepath_user_ticket, filepath_user_qr_code, status_list
connection = pymysql.connect(
    host = host,
    port = port,
    user = user,
    password = password,
    database=db_name,
    cursorclass=pymysql.cursors.DictCursor
)    
arr = [[]*313]
wb = openpyxl.reader.excel.load_workbook(filename="книга1.xlsx")
wb.active = 0
sheet = wb.active
for i in range (1,314):
    grade = sheet['A'+str(i)].value
    grade = grade.replace("-","")
    name = sheet['B'+str(i)].value.split()
    firstname = name[1]
    lastname = name[0]
    arr.append([firstname, lastname, grade])
    with connection.cursor() as cursor:
                cursor.execute(
                    "insert into grades (firstname, lastname, grade) VALUES (\"" + firstname + "\", \"" + lastname + "\", \"" + grade + "\");")
                connection.commit()


    