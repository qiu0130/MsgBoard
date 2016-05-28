# -*- coding: UTF-8 -*- 
# Created by qiu on 16-5-24
#

import time
import json
import requests
from datetime import datetime
from flask import Flask
from flask import g, request, session, redirect, url_for, abort, flash
from flask.ext.mako import render_template
from flask.ext.mako import MakoTemplates
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.bcrypt import Bcrypt
from flask.ext.redis import FlaskRedis
from redis import StrictRedis


from config import Config
from geetest import GeetestLib

captcha_id = "27bc512f6dd9a9d268d9dad909af6d6e"
private_key = "913542762c8a4550be0cc809cd390098"
MIN_PASS_TIME = 5.0
MAX_PASS_TIME = 15.0
redis_key_expire = 60 * 10


app = Flask(__name__)
app.config.from_object(Config)
mako = MakoTemplates(app)
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)


# redis编码设置
class DecodedRedis(StrictRedis):
    @classmethod
    def from_url(cls, url, db=None, **kwargs):
        kwargs['decode_responses'] = True
        return StrictRedis.from_url(url, db, **kwargs)

redis_store = FlaskRedis.from_custom_provider(DecodedRedis, app)


class User(db.Model):
    __tablename__ = "user"
    id = db.Column(db.Integer, primary_key = True, autoincrement = True)
    username = db.Column(db.String(128), unique = True)
    password_hashed = db.Column(db.String(256))

    def __init__(self, username, password):
        self.username = username
        self.password_hashed = bcrypt.generate_password_hash(password)

    def __repr__(self):
        return "<User %r>" % (self.username)

class Message(db.Model):
    __tablename__ = "message"
    id = db.Column(db.Integer, primary_key = True, autoincrement = True)
    title = db.Column(db.String(128))
    body = db.Column(db.Text)
    pub_date = db.Column(db.DateTime)

    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    user = db.relationship("User", backref=db.backref('messages', lazy='dynamic'))

    def __init__(self, title, body, user, pub_date = None):
        self.title = title
        self.body = body
        self.user = user
        if pub_date is None:
            pub_date = datetime.now()
        self.pub_date = pub_date

    def __repr__(self):
        return "<Message %r of User %r>" % (self.title, self.user.username)


@app.route("/add", methods=["GET", "POST"])
def add_message():

    cur_user = session.get("logged_in", None)
    if not cur_user:
         return redirect("/login")

    if request.method == "POST":

        title = request.form["title"]
        message = request.form["message"]
        if not title or not Message:
            return redirect("/")

        # 单一ip频繁留言
        redis_ip = redis_store.get(get_cur_ip())
        if redis_ip and MIN_PASS_TIME < time.time() - float(redis_ip) < MAX_PASS_TIME:

            redis_store.setex(cur_user, redis_key_expire, time.time())
            redis_store.setex(get_cur_ip(), redis_key_expire, time.time())

            redis_store.hmset("pre_add_msg", {"title": title, "message": message})
            redis_store.expire("pre_add_msg", redis_key_expire)

            return redirect(url_for("validate_capthca"))

        #单一用户频繁留言
        redis_user = redis_store.get(cur_user)
        if redis_user and MIN_PASS_TIME < time.time() - float(redis_user) < MAX_PASS_TIME:

            redis_store.setex(cur_user, redis_key_expire, time.time())
            redis_store.setex(get_cur_ip(), redis_key_expire, time.time())
            redis_store.hmset("pre_add_msg", {"title": title, "message": message})
            redis_store.expire("pre_add_msg", redis_key_expire)

            return redirect(url_for("validate_capthca"))

        redis_store.setex(cur_user, redis_key_expire, time.time())
        redis_store.setex(get_cur_ip(), redis_key_expire, time.time())

        user = User.query.filter_by(username = cur_user).first()
        msg = Message(title=title, body=message, user = user)
        db.session.add(msg)
        db.session.commit()

        return redirect("/")

    return render_template("add.html")


@app.route("/")
def show_messages():

    messages = Message.query.order_by(db.desc(Message.pub_date)).all()
    return render_template("home.html", messages = messages)


def get_cur_ip():
    real_ip = request.headers.get('X-Real-Ip', request.remote_addr)
    return real_ip

# def get_cur_ip_addr():
#     url = "http://int.dpool.sina.com.cn/iplookup/iplookup.php?format=json&ip=" + get_cur_ip()
#     rt = requests.get(url).json()
#
#     if isinstance(rt, dict) and rt["ret"] == 1:
#         location = rt["country"] + " . " + rt["province"] + " . " + rt["city"]
#     else:
#         location = "unknown"
#     return location


@app.route("/login", methods = ["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        user = User.query.filter_by(username = request.form["username"]).first()

        if user and bcrypt.check_password_hash(user.password_hashed,request.form["password"]):

            redis_user = redis_store.get(user.username)
            redis_ip = redis_store.get(get_cur_ip())

            # 单一ip多次登录
            if redis_ip and MIN_PASS_TIME < time.time() - float(redis_ip) < MAX_PASS_TIME:

                 redis_store.setex(user.username, redis_key_expire, time.time())
                 redis_store.setex(get_cur_ip(), redis_key_expire, time.time())
                 redis_store.setex("pre_login", redis_key_expire, user.username)

                 return redirect(url_for("validate_capthca"))

            #单一用户多次登录
            if redis_user and MIN_PASS_TIME < time.time() - float(redis_user) < MAX_PASS_TIME:

                 redis_store.setex(user.username, redis_key_expire, time.time())
                 redis_store.setex(get_cur_ip(), redis_key_expire, time.time())
                 redis_store.setex("pre_login", redis_key_expire, user.username)

                 return redirect(url_for("validate_capthca"))

            redis_store.setex(user.username, redis_key_expire, time.time())
            redis_store.setex(get_cur_ip(), redis_key_expire, time.time())

            session["logged_in"] = user.username

            return redirect("/")
        else:
            error = "用户或密码错误"

    return render_template("login.html", error = error)



@app.route("/logout")
def logout():
    session.pop("logged_in", None)
    return redirect("/")

@app.route('/getcaptcha', methods=["GET"])
def get_captcha():
    user_id = "test"
    gt = GeetestLib(captcha_id, private_key)
    status = gt.pre_process(user_id)
    session[gt.GT_STATUS_SESSION_KEY] = status
    session["user_id"] = user_id
    response_str = gt.get_response_str()
    return response_str


@app.route('/validate', methods=["GET", "POST"])
def validate_capthca():

    if request.method == "POST":
        gt = GeetestLib(captcha_id, private_key)
        challenge = request.form[gt.FN_CHALLENGE]
        validate = request.form[gt.FN_VALIDATE]
        seccode = request.form[gt.FN_SECCODE]
        status = session[gt.GT_STATUS_SESSION_KEY]
        user_id = session.get("user_id", None)

        if status:
            result = gt.success_validate(challenge, validate, seccode, user_id)
        else:
            result = gt.failback_validate(challenge, validate, seccode)

        if result:
            # 验证安全，完成登录
            _user =  redis_store.get("pre_login")
            if _user:
                session["logged_in"] = _user
            # 验证安全，完成添加留言
            _body = redis_store.hgetall("pre_add_msg")
            if _body:
                title = _body.get("title")
                message = _body.get("message")

                user = User.query.filter_by(username = session["logged_in"]).first()
                msg = Message(title=title, body=message, user = user)

                db.session.add(msg)
                db.session.commit()
            return redirect("/")
        else:
            return redirect("/login")

    return render_template("validate.html")


if __name__ == "__main__":

    app.run(host="0.0.0.0", port=80, debug=True)



