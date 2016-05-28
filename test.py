#!/usr /bin/env python
# -*- coding: utf-8 -*-
# Created by qiu on 16-5-24
#

import time
import unittest
from config import TestingConfig
from flask import Flask, request, session

from app import app, db, redis_store

class MessageBoardTestClass(unittest.TestCase):

    def setUp(self):
        app.config.from_object(TestingConfig)
        self.app = app.test_client()

    def tearDown(self):
        session.clear()

    def test_exception_user_login(self):
        @app.route("/set", methods = ["POST"])
        def set():
            name = request.form["name"]
            session["logged_in"] = name

            # user = User.query.fliter_by(username = name)
            redis_store.set(name, time.time())
            return "I'am %s" % (name)

        @app.route("/get")
        def get():
            name = session.get("logged_in", None)
            redis_time = redis_store.get(name)
            return time.time() - redis_time

        @app.route("/delete", methodds = ["POST"])
        def delete():
            del session["logged_in"]
            return "The test deleted"

        for i in range(10):
            self.assertEqual(self.app.post('/set', data = {"name": "qiu"}).data, "I'am qiu")
            time.sleep(10)
            self.assertTrue(5.0< self.app.get("/get") < 10.0)

        self.app.post("/delete")

    def test_exception_ip_login(self):
        pass
