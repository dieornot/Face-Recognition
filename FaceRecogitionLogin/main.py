import hashlib
import os
import random
import string
import time

import face_recognition
import base64

from flask import Flask, request, jsonify

import pymysql

app = Flask(__name__)

# 连接数据库
connection = pymysql.connect(host="127.0.0.1", port=3306, user="root", passwd="123456", db="face_login")
cursor = connection.cursor()


# 验证用户名功能路由
@app.route('/verifyUsername', methods=["POST"])
def usernameVerify():
    # 获取前端表单输入的用户名
    username = request.form.get("username")

    # 根据用户名查询数据库内的数据
    sql = "select * from user where username = %s "

    count = cursor.execute(sql, [username])
    if count == 0:
        return "<script>alert('没有找到该用户！！请重新输入！！');window.location.href='/static/faceVerifyUsername.html'</script>"

    return "<script>window.location.href='/static/faceRecognition.html?username=%s'</script>" % username


# 人脸识别功能路由
@app.route('/faceLogin', methods=["POST"])
def faceLogin():
    # 获取前端表单输入的用户名
    username = request.form.get("-")

    # 获取前端表单传入人脸识别图片的base64编码
    faceImg = request.form.get("faceImg")

    # 根据用户名找到数据库中的用户数据，用来进行人脸识别
    cursor.execute("select * from user where username = %s ", [username])
    user = cursor.fetchone()
    user_id = user[0]
    user_username = user[1]
    user_password = user[2]
    user_salt = user[3]
    user_face_img = user[4]

    # 定义前端传来图片的保存路径和文件名
    faceImg_Name = "\\" + username + time.strftime("%Y %m %d %H %M %S", time.localtime()) + ".png"
    faceImg_PATH = os.path.join("LoginFaceImg" + faceImg_Name)

    # 打开该文件，向文件写入base64编码
    with open(faceImg_PATH, "wb") as i:
        i.write(base64.b64decode(faceImg[22:]))

    # 使用face_recognition库加载刚才保存的文件
    face_recognition_Img = face_recognition.load_image_file(faceImg_PATH)
    # 加载人脸识别基准图片
    face_recognition_baseImg = face_recognition.load_image_file("FaceImg\\%s" % user_face_img)

    # 将两个文件转换为编码
    code_img = face_recognition.face_encodings(face_recognition_Img)
    code_baseImg = face_recognition.face_encodings(face_recognition_baseImg)

    # 检测用户上传照片中是否存在人脸特征，如不存在则返回页面重新人脸识别，返回信息1表示未找到人脸,返回信息2表示未通过检测
    if not face_recognition.face_locations(face_recognition_Img):
        return "1", 500

    is_pass = face_recognition.compare_faces([code_baseImg[0]], code_img[0], 0.49)

    if is_pass[0]:

        selectuser_id = user[0]
        selectuser_name = user[1]
        import datetime
        selectlogin_time = datetime.datetime.now()
        type1 = 'facelogin'
        print(selectuser_id, selectuser_name, selectlogin_time)
        sql2 = "insert into login_message values (null, %d, '%s', '%s', '%s') " % (
            selectuser_id, selectuser_name, selectlogin_time, type1)
        cursor.execute(sql2)
        connection.commit()
        return "", 200
    else:
        return "2", 500


# 密码登录功能路由
@app.route('/passwordLogin', methods=["POST"])
def passwordLogin():
    # 获取前端表单输入的用户名
    username = request.form.get("username")

    # 获取前端表单输入的密码
    password = request.form.get("password")

    # 根据用户名查询数据库内的数据
    sql = "select * from user where username = %s "

    # 执行sql语句
    count = cursor.execute(sql, [username])

    # 如果没有对应的用户，返回界面重新登录
    if count == 0:
        return "<script>alert('没有找到该用户！！请重新输入！！');window.location.href='/static/passwordLogin.html'</script>"

    # 移动游标到下一行数据
    user = cursor.fetchone()

    # 获得到的用户密码和盐值
    selectedPassword = user[2]
    selectedSalt = user[3]
    if not hashlib.sha256((password + selectedSalt).encode("utf8")).hexdigest() == selectedPassword:
        return "<script>alert('密码输入错误！！');window.location.href='/static/passwordLogin.html'</script>"
    else:
        selectuser_id = user[0]
        selectuser_name = user[1]
        import datetime
        selectlogin_time = datetime.datetime.now()
        type2 = 'passlogin'
        print(selectuser_id, selectuser_name, selectlogin_time)
        sql1 = "insert into login_message values (null, %d, '%s', '%s', '%s') " % (
            selectuser_id, selectuser_name, selectlogin_time, type2)
        cursor.execute(sql1)
        connection.commit()
        return "<script>alert('登录成功！！');window.location.href='/static/success.html'</script>"


# 注册功能路由
@app.route('/register', methods=["POST"])
def register():
    # 获取前端发送的注册用户的用户名
    username = request.form.get("username")

    sql5 = "SELECT * FROM `user` WHERE username = '%s' " % username
    if (cursor.execute(sql5) == 1):
        return "<script>" \
               "alert('用户名已存在');" \
               "window.location.href='/static/register.html';" \
               "</script>"
    # 获取前端发送的注册用户的密码
    else:
        password = request.form.get("password")

        # 获取前端表单发送来的文件数据
        face_img = request.files['face_img']

        # 获取图片的扩展名
        img_extent = os.path.splitext(face_img.filename)[1]

        # 拼接文件新的文件名（以用户名为名字）
        face_img_name = username + img_extent

        # 修改文件的文件名为用户名.扩展名
        face_img.filename = face_img_name
        if bool(username) & bool(password):

            # 生成哈希盐值
            salt = "".join(random.sample(string.ascii_letters + string.digits, 16))
            hashPassword = hashlib.sha256((password + salt).encode("utf8")).hexdigest()
            # 将用户信息保存到数据库
            sql = "insert into user value (null, '" + username + "', '" + str(
                hashPassword) + "', '" + salt + "', '" + face_img_name + "')"
            cursor.execute(sql)
        else:
            return "<script>alert('参数获取错误，请重新输入参数')</script>"

        # 设定图片存储位置
        UPLOAD_PATH = 'FaceImg'

        # 根据当前的项目位置获取文件绝对路径

        file_path = os.path.join(UPLOAD_PATH, face_img.filename)

        # 保存文件
        face_img.save(file_path)

        # 检测图像中的人脸，如果没有的话就删除文件
        if not face_recognition.face_locations(face_recognition.load_image_file(file_path)):
            os.remove(file_path)
            connection.rollback()
            return "<script>alert('图片没有检测到人像，请重新上传');window.location.href='/static/register.html';</script>"

        # 提交数据库事务
        connection.commit()

        if (cursor.execute(sql5) == 1):
            return "<script>" \
                   "alert('注册成功');" \
                   "window.location.href='/static/index.html';" \
                   "</script>"
        else:
            return "<script>" \
                   "alert('注册失败');" \
                   "window.location.href='/static/register.html';" \
                   "</script>"


@app.route("/listUser", methods=["GET"])
def listUser():
    sql = "select * from user "
    cursor.execute(sql)
    users = cursor.fetchall()

    from flask import jsonify
    return jsonify(users)


# 用来删除用户
@app.route("/deleteUser", methods=["GET"])
def deleteUser():
    user_id = request.args.get("id")
    # user_name = request.args.get("username")
    print(user_id)
    # print(user_name)
    slq11 = "SELECT face_img FROM `user` WHERE id = '%s'" %user_id
    imgname=cursor.execute(slq11)
    print(imgname)
    sql = "delete from user where id = %s"
    cursor.execute(sql, [user_id])
    connection.commit()

    return "<script>alert('删除成功');window.location.href='/static/manageUser.html'</script> "


# 用来修改用户
@app.route('/updateUser', methods=["POST"])
def updateUser():
    user_id = int(request.form.get("id"))
    print(user_id)
    # 获取前端发送的注册用户的用户名
    user_name = request.form.get("username")
    # 获取前端发送的注册用户的密码
    password = request.form.get("password")
    if bool(user_name) & bool(password):
        # 生成哈希盐值
        salt = "".join(random.sample(string.ascii_letters + string.digits, 16))
        hashPassword = hashlib.sha256((password + salt).encode("utf8")).hexdigest()
        # 将用户信息保存到数据库
        sql = "update user set username='%s',password='%s'，salt=’%s'' where id= %d " % (user_name, hashPassword,salt,user_id)
        cursor.execute(sql)
        return "<script>alert('修改成功');window.location.href='/static/manageUser.html'</script> "


@app.route("/selectUserById", methods=["GET"])
def selectUserById():
    user_id = int(request.args.get("id"))
    sql = "select * from user where id = %d " % user_id
    cursor.execute(sql)
    user = cursor.fetchone()

    return jsonify(user)


if __name__ == '__main__':
    app.run()
