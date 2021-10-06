import telebot, pymysql, random, qrcode, re, cv2
from constants import host, user, password, db_name, port, teachers, classes, id_admin, \
    filepath_user_photo, filepath_user_ticket, filepath_user_qr_code, status_list, apiKey
from PIL import Image, ImageDraw, ImageFont

bot = telebot.TeleBot(f'{apiKey}')

dict, generate_question, questions = {}, {}, {}

connection = pymysql.connect(
    host = host,
    port = port,
    user = user,
    password = password,
    database=db_name,
    cursorclass=pymysql.cursors.DictCursor
)

def check_face(tID):
    # 0 - не найдено лиц
    # 1 - найдено одно лицо
    # 2 - найдено больше 1 лица
    face_cascade_db = cv2.CascadeClassifier(cv2.data.haarcascades+"haarcascade_frontalface_default.xml")
    img = cv2.imread(filepath_user_photo + str(tID) + ".jpg")
    img_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    faces = face_cascade_db.detectMultiScale(img_gray, 1.1, 19)
    if len(faces) == 0:
        return 0
    elif len(faces) == 1:
        return 1
    elif len(faces) > 1:
        return 2


def check_reg(id):
    with connection.cursor() as cursor:
        cursor.execute("select firstname from regBlank where tID = \"" + str(id) + "\";")
        current = cursor.fetchall()
        if current == "()":
            return True
        else:
            return False

def check_grade(current):
    if current in classes:
        return True
    return False

def generate_uID(current):
    return str(current) + str(random.randint(1000, 10001))

def get_classes(lst):
    lst = ""
    for i in range(len(lst)):
        lst = lst + (lst[i] + " ")
    return lst

def isRegistered(id):
    with connection.cursor() as cursor:
        cursor.execute("select firstname from regBlank where tID = \"" + str(id) + "\";")
        lst = cursor.fetchall()
        if len(lst) > 0:
            return True
        else:
            return False

def notRegistered(tID):
    bot.send_message(tID, "Ты уже зарегистрирован(а). Проверить текущий статус можно командой /status")

def check_black(tID):
    with connection.cursor() as cursor:
        cursor.execute("select * from blackBlank where tID = " + str(tID) + ";")
        lst = cursor.fetchall()
    if len(lst) > 0:
        return True
    else:
        return False


def replace_letter(current):
    current = current.replace("ё", "е")
    current = current.replace("Ё", "Е")
    return current

@bot.message_handler(commands=['admin'])
def admin_start(message):
    tID = message.chat.id
    if tID == id_admin:
        bot.send_message(tID, "Панель администрирования\nКоманды:\n/members КЛАСС - листы регистрации\n/setstatus ID СТАТУС - изменить статус участников\n/questions - входящие вопросы\n/answer ID ТЕКСТ - отправить ответ на вопрос\n/blacklist - чёрный список\n/stat - статистика")

@bot.message_handler(commands=['questions'])
def admin_questions(message):
    global questions
    tID = message.chat.id
    if tID == id_admin:
        with connection.cursor() as cursor:
            cursor.execute("select firstname, lastname, tID, text from FAQBlank")
            messages = cursor.fetchall()
            if len(messages) > 0:
                for num in range (len(messages)):
                    firstname = messages[num]['firstname']
                    lastname = messages[num]['lastname']
                    id = messages[num]['tID']
                    text = messages[num]['text']
                    bot.send_message(tID, "Вопрос №" + str(id) + ", Имя: " + firstname + " " + lastname + "\nВопрос: " + text)
                    questions[num] = id
            else:
                bot.send_message(tID, "Новых вопросов нет")

@bot.message_handler(commands=['start'])
def answer_start(message):
    tID = message.chat.id
    if tID != id_admin and not check_black (tID):
        if not isRegistered(tID):
            bot.send_message(tID, "Привет! Я помогу тебе попасть на осенний бал")
            bot.send_message(tID, "Для этого мне понадобится немного информации о тебе и пара минут свободного времени.\nНапиши /reg для начала регистрации")
            bot.send_message(tID, "Если что-то непонятно, напиши /help")
        else:
            notRegistered(tID)

@bot.message_handler(commands=['help'])
def answer_help(message):
    tID = message.chat.id
    if tID != id_admin:
        bot.send_message(tID, "Данный бот поможет тебе попасть на осенний бал")
        bot.send_message(tID, "Команды для управления:\n/start - начало общения\n/reg - начало регистрации\n/status - проверка текущего статуса заявки\n/delete - удалить заявку\n/contact - написать сообщение в поддержку\n/help - помощь")

@bot.message_handler(commands=['status'])
def answer_reg(message):
    tID = message.chat.id
    if tID != id_admin and not check_black (tID):
        if not isRegistered(tID):
            bot.send_message(tID, "Ты ещё не зарегистрирован(а) на бал. Сделай это, чтобы отслеживать свой статус, напиши /start")
        else:
            with connection.cursor() as cursor:
                cursor.execute("select firstname, lastname, grade, accept, uID from regBlank where tID = \"" + str(tID) + "\";")
                status = cursor.fetchall()
                bot.send_message(tID, status[0]['firstname'] + ", твой текущий статус заявки: " + status[0]['accept'])
                if status[0]['accept'] == "приглашён":
                    bot.send_message(tID, "Ура, ты сможешь принять участие в осеннем балу! Ниже твой пригласительный билет. Покажи его при входе в школу, чтобы тебя пропустили внутрь")
                    ticket = Image.open("input_ticket.png")
                    idraw = ImageDraw.Draw(ticket)
                    if len(status[0]['firstname']) > 10 or len(status[0]['lastname']) > 10:
                        font_size = 95
                    else:
                        font_size = 120
                    font = ImageFont.truetype("bent.ttf", size=font_size)
                    idraw.text((2000, 490), status[0]['firstname'], font=font)
                    idraw.text((2000, 610), status[0]['lastname'], font=font)
                    idraw.text((2000, 800), status[0]['grade'], font=font)
                    img = qrcode.make(str(status[0]['uID']))
                    img.save(filepath_user_qr_code + 'qrcode' + str(tID) + '.png')
                    watermark = Image.open(filepath_user_qr_code + 'qrcode' + str(tID) + '.png')
                    ticket.paste(watermark, (2000, 1000), watermark)
                    ticket.save(filepath_user_ticket + 'ticket' + str(tID) + '.png')
                    bot.send_document(tID, open(filepath_user_ticket + 'ticket' + str(tID) + '.png', 'rb'))
                elif status[0]['accept'] == "отклонена":
                    bot.send_message(tID, "К сожалению, ты не сможешь попасть на осенний бал. Если ты считаешь, что произошла ошибка, то напиши нам /contact")

@bot.message_handler(commands=['stat'])
def send_grade(message):
    if message.chat.id == id_admin:
        with connection.cursor() as cursor:
            cursor.execute("SELECT * from regBlank;")
            all = cursor.fetchall()
            count_all = str(len(all))
            cursor.execute(("select tID from regBlank where accept = \"приглашён\""))
            succes = cursor.fetchall()
            count_succes = str(len(succes))
            cursor.execute(("select tID from regBlank where accept = \"отклонена\""))
            unsucces = cursor.fetchall()
            count_unsucces = str(len(unsucces))
            count_waiting = str(int(count_all) - int(count_unsucces) - int(count_succes))
            bot.send_message(message.chat.id, "Всго зарегистрировано: " + count_all + "\nОдобрено: "+ count_succes +
                             "/" + count_all + "\nОтклонено: " + count_unsucces + "/" + count_all + "\nВ ожидании: " + count_waiting)

@bot.message_handler(commands=['reg'])
def answer_reg(message):
    tID = message.chat.id
    if tID != id_admin and not check_black (tID):
        if not isRegistered(tID):
            msg = bot.send_message(tID,"Как тебя зовут? Напиши в таком формате: \"Иван Иванов\"")
            bot.register_next_step_handler(msg, pick_name)
        else:
            notRegistered(tID)


def pick_name(message):
    flag = False
    tID = message.chat.id
    try:
        input_text = message.text.split()
        input_text[0], input_text[1] = replace_letter(input_text[0]), replace_letter(input_text[1])
        with connection.cursor() as cursor:
            cursor.execute("select firstname, lastname from regBlank where lastname = \"" + input_text[1] + "\";")
            check_data = cursor.fetchall()
            cursor.execute("select firstname, lastname, grade from grades where lastname = \"" + input_text[1] + "\";")
            maybe = cursor.fetchall()
            if len(check_data) == 0:
                if len(input_text) == 2:
                    for i in range(len(maybe)):
                        if maybe[i]['firstname'] == input_text[0] and maybe[i]['lastname'] == input_text[1]:
                            firstname, lastname, grade, teacher = maybe[i][
                                                 'firstname'], maybe[i][
                                                 'lastname'], maybe[i][
                                                 'grade'], teachers[maybe[i]['grade']]
                            bot.send_message(tID,
                                             "Я нашёл тебя в списке учащихся. Вот информация о тебе:\nИмя: " + firstname + " " + lastname + "\nКласс: " + grade + "\nКлассный руководитель: " + teacher)
                            bot.send_message(tID,
                                             "Мне нужна твоя фотография, где хорошо видно твоё лицо (пример ниже), отправь её сюда")
                            msg = bot.send_photo(tID, open('preview_photo.png', 'rb'))
                            dict["'" + str(tID) + "'"] = []
                            dict["'" + str(tID) + "'"].append(firstname)
                            dict["'" + str(tID) + "'"].append(lastname)
                            dict["'" + str(tID) + "'"].append(grade)
                            dict["'" + str(tID) + "'"].append(str(tID))
                            dict["'" + str(tID) + "'"].append(str(tID) + str(random.randint(1000,10001)))

                            flag = True
                            bot.register_next_step_handler(msg, recieve_photo)
                    if not flag:
                        dict["'" + str(tID) + "'"] = []
                        dict["'" + str(tID) + "'"].append(input_text[0].capitalize())
                        dict["'" + str(tID) + "'"].append(input_text[1].capitalize())
                        msg = bot.send_message(tID, "Приятно познакомиться, " + dict["'" + str(tID) + "'"][0] + ".\nВ каком классе ты учишься? \nДоступные классы: \n" + get_classes(classes))
                        bot.register_next_step_handler(msg, pick_grade)
                else:
                    bot.reply_to(message, "Неправильный формат ввода данных, попробуй ещё раз, используя команду /reg")
            else:
                name, surname = check_data[0]['firstname'], check_data[0]['lastname']
                if replace_letter(name.capitalize()) == replace_letter(input_text[0].capitalize()) and replace_letter(surname.capitalize()) == replace_letter(input_text[1].capitalize()):
                    bot.send_message(tID, "Человек с таким именем и фамилией уже зарегистрирован. Если ты считаешь, что произошла ошибка, напиши нам /contact")
    except Exception as e:
        msg = bot.send_message(tID, "Упс, что-то пошло не так, попробуй заново ввести имя и фамилию")
        bot.register_next_step_handler(msg, pick_name)

def pick_grade(message):
    tID = message.chat.id
    try:
        input_text = message.text.split()
        input_text[0] = input_text[0].upper()
        if len(input_text) == 1:
            if check_grade(input_text[0]):
                dict["'" + str(tID) + "'"].append(input_text[0])
                dict["'" + str(tID) + "'"].append(str(tID))
                dict["'" + str(tID) + "'"].append(str(tID) + str(random.randint(1000,10001)))
                bot.reply_to(message, "Класс выбран")
                bot.send_message(tID,
                                 "Мне нужна твоя фотография, где хорошо видно твоё лицо (пример ниже), отправь её сюда")
                msg = bot.send_photo(tID, open('preview_photo.png', 'rb'))
                bot.register_next_step_handler(msg, recieve_photo)
            else:
                bot.send_message(tID, "Такого класса не существует, попробуй ещё раз, используя команду /reg")
        else:
            bot.reply_to(message, "Неправильный формат ввода данных, попробуй ещё раз, используя команду /reg")
    except Exception:
        msg = bot.send_message(tID, "Упс, что-то пошло не так, попробуй заново ввести класс")
        bot.register_next_step_handler(msg, pick_grade)

def recieve_photo(message):
    tID = message.chat.id
    try:
        file_info = bot.get_file(message.photo[len(message.photo) - 1].file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        src = filepath_user_photo + str(tID) + '.jpg'
        with open(src, 'wb') as new_file:
            new_file.write(downloaded_file)
        dict["'" + str(tID) + "'"].append(src)
        isFaceOnPhoto = check_face(tID)
        if isFaceOnPhoto == 1:
            bot.reply_to(message, "Отлично, вижу тебя на фотографии)")
            bot.send_message(tID, "Давай посмотрим, какую информацию о тебе я узнал\nИмя: " + dict["'" + str(tID) + "'"][0] + " " +
                             dict["'" + str(tID) + "'"][1] +
                             "\nКласс: " + dict["'" + str(tID) + "'"][2] + "\nКлассный руководитель: " + teachers[
                                 dict["'" + str(tID) + "'"][2]] +
                             '\nЕсли хочешь что-то исправить, напиши /reg')
            bot.send_message(tID, "Если все данные введены верно, напиши /send")
        elif isFaceOnPhoto == 2:
            msg = bot.send_message(tID, "Моё компьютерное зрение видит, что на твоей фотографии больше одного человека\nПопробуй найти другую фотографию и пришли её сюда")
            bot.register_next_step_handler(msg, recieve_photo)
        elif isFaceOnPhoto == 0:
            msg = bot.send_message(tID, "У меня довольно хорошее зрение, но я не смог увидеть на этой фотографии лицо\nПопробуй найти другую фотографию и пришли её сюда")
            bot.register_next_step_handler(msg, recieve_photo)
    except Exception as e:
        msg = bot.send_message(tID, "Упс, что-то пошло не так, попробуй отправить фотографию снова")
        bot.register_next_step_handler(msg, recieve_photo)


@bot.message_handler(commands=['send'])
def answer_send(message):
    tID = message.chat.id
    if not isRegistered(tID) and not check_black (tID):
        firstname = dict["'" + str(tID) + "'"][0]
        lastname = dict["'" + str(tID) + "'"][1]
        grade = dict["'" + str(tID) + "'"][2]
        teacher = teachers[grade]
        photo_src = dict["'" + str(tID) + "'"][5]
        uID = dict["'" + str(tID) + "'"][4]
        with connection.cursor() as cursor:
            cursor.execute(
                "insert into regBlank (firstname, lastname, grade, teacher, tID, uID, accept, photo) VALUES (\"" + firstname + "\", \"" + lastname + "\", \"" + grade + "\", \"" + teacher + "\", \"" + str(
                    tID) + "\", \"" + str(uID) + "\", \"" + "в обработке" + "\", \"" + photo_src + "\");")
            connection.commit()
        bot.send_message(tID,
                         firstname + ", заявка создана и отправлена на обработку, теперь ты можешь отслеживать её статус с помощью команды /status")
    else:
        if not isRegistered(tID):
            notRegistered(tID)


@bot.message_handler(commands=['delete'])
def answer_send(message):
    tID = message.chat.id
    if isRegistered(tID) and not check_black(tID):
        with connection.cursor() as cursor:
            cursor.execute("delete from regBlank where tID = \"" + str(tID) + "\";")
            connection.commit()
        bot.send_message(tID,
                         "Твоя заявка на участие в осеннем балу удалена, если ты хочешь создать её заново, напиши /reg")
    else:
        if isRegistered(tID):
            bot.send_message(tID, "Ты ещё не зарегистрирован(а) и не можешь удалить заявку, которой не существует, напиши /start для начала регистрации")

@bot.message_handler(commands=['contact'])
def answer_reg(message):
    tID = message.chat.id
    if tID != id_admin:
        try:
            with connection.cursor() as cursor:
                cursor.execute("select text from FAQBlank where tID = \"" + str(tID) + "\";")
                question = cursor.fetchall()
            if len(question) > 0:
                bot.send_message(tID, "Ты уже задавал(а) вопрос, вот его текст:\n" + question[0]['text'])
            else:
                msg = bot.send_message(tID,"Введи имя и фамилию в формате: \"Иван Иванов\"")
                bot.register_next_step_handler(msg, input_name_faq)
        except Exception as e:
            print(e)
            bot.reply_to(message, "Упс, что-то то пошло не так, попробуй снова, используя /contact")

def input_name_faq(message):
    global generate_question
    tID = message.chat.id
    input_text = message.text.split()
    if len(input_text) == 2:
        generate_question["'" + str(tID) + "'"] = []
        generate_question["'" + str(tID) + "'"].append(input_text[0])
        generate_question["'" + str(tID) + "'"].append(input_text[1])
        msg = bot.send_message(tID, input_text[0] + ", введи свой вопрос")
        bot.register_next_step_handler(msg, input_text_faq)
    else:
        bot.reply_to(message, "Неправильный формат ввода данных, попробуй ещё раз, используя команду /contact")

def input_text_faq(message):
    global generate_question
    tID = message.chat.id
    generate_question["'" + str(tID) + "'"].append(message.text)
    with connection.cursor() as cursor:
        cursor.execute("insert into FAQBlank (firstname, lastname, text, tID) VALUES (\"" + generate_question["'" + str(tID) + "'"][0] + "\", \"" + generate_question["'" + str(tID) + "'"][1] + "\", \"" + generate_question["'" + str(tID) + "'"][2] + "\", \"" + str(tID) + "\");" )
        connection.commit()
    bot.send_message(tID, generate_question["'" + str(tID) + "'"][0] + ", твой вопрос отправлен. В скором времени мы ответим на него")
    bot.send_message(id_admin, "Поступил новый вопрос, введите /questions для просмотра")



@bot.message_handler(content_types=['text'])
def admin_command(message):
    tID = message.chat.id
    if tID == id_admin:
        if re.match('/setstatus', message.text):
            input_text = message.text.split()
            if len(input_text) == 3:
                if input_text[2] in status_list:
                    try:
                        with connection.cursor() as cursor:
                            cursor.execute("update regBlank set accept = \"" + input_text[2] + "\" where tID = \"" + input_text[1] + "\";")
                            connection.commit()
                            bot.send_message(input_text[1],
                                             "Твой статус регистрации изменился. Напиши /status для получения более подробной информации")
                        bot.send_message(tID, "Статус участника изменён")
                    except Exception:
                        bot.send_message(id_admin, "Неверно введён tID")
                else:
                    bot.reply_to(message, "такого статуса не существует, попробуйте ещё раз")
            else:
                bot.reply_to(message, "неправильный форма ввода, попробуйте ещё раз")
        elif re.match('/members', message.text):
            input_text = message.text.split()
            if len(input_text) == 2:
                with connection.cursor() as cursor:
                    cursor.execute(
                        "select firstname, lastname, tID, accept from regBlank where grade = '" + input_text[1] + "';")
                    data = cursor.fetchall()
                    if len(data) > 0:
                        arr = []
                        for row in data:
                            try:
                                arr.append(row['firstname'] + " " + row['lastname'] + " | " + str(row[
                                                     'tID']) + " | " + row['accept'])
                            except TypeError:
                                arr.append(row['firstname'] + " " + row['lastname'] + " | " + str(row[
                                                     'tID']) + " | " + 'в обработке')
                            print(arr)
                        bot.reply_to(message, arr)
                    else:
                        bot.reply_to(message, "такого класса не существует, либо в нём никто не зарегистрирован, попробуйте ещё раз")
            else:
                bot.reply_to(message, "неправильный форма ввода, попробуйте ещё раз")
        elif re.match('/answer', message.text):
            input_text = message.text.split()
            if len(input_text) >= 3:
                text = ""
                for i in range(2, len(input_text)):
                    text = text + " " + input_text[i]
                bot.send_message(int(input_text[1]), "Тебе пришёл ответ на вопрос:\n" + text)
                bot.send_message(tID, "Сообщение отправлено")
                with connection.cursor() as cursor:
                    cursor.execute("delete from FAQBlank where tID = \"" + input_text[1] + "\";")
                    connection.commit()
            else:
                bot.reply_to(message, "Неправильный форма ввода, попробуйте ещё раз")
        elif re.match('/block', message.text):
            input_text = message.text.split()
            if len(input_text) == 3:
                if input_text[2] == 'add':
                    with connection.cursor() as cursor:
                        if not check_black(tID):
                            cursor.execute("insert blackBlank (tID) VALUES (" + input_text[1] + ");")
                            connection.commit()
                            print("OK")
                            bot.reply_to(message, "Пользователь добавлен в чёрный список")
                        else:
                            bot.reply_to(message, "Данный пользователь уже находится в чёрном списке")
                elif input_text[2] == 'del':
                    with connection.cursor() as cursor:
                        if check_black(tID):
                            cursor.execute("delete from blackBlank where tID = " + input_text[1] + ";")
                            connection.commit()
                            bot.reply_to(message, "Пользователь удалён из чёрного списка")
                        else:
                            bot.reply_to(message, "Пользователя с таким tID нет в чёрном списке")


            else:
                bot.reply_to(message, "Неправильный форма ввода, попробуйте ещё раз")

bot.polling()