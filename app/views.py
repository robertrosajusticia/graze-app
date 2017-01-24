#!/usr/bin/python

import sys
from os import path
_path = path.abspath(path.join(path.dirname(path.abspath(__file__)), '..\..\engine'))
print _path
sys.path.append(_path)
from graze import Manager

import os
import sys
from flask import render_template, url_for, abort, jsonify, request, redirect
from app import app

manager = Manager()

@app.route('/')
@app.route('/index')
def index():	
    dirs = [d for d in os.listdir('..\engine\sites') if os.path.isdir(os.path.join('..\engine\sites', d))]
    return render_template("index.html",
                           title='Home',
                           dirs=dirs)

@app.route('/execute')
def execute():
  site = str(request.args.get('site', None))  
  service = str(request.args.get('service', None))  
  manager.launch_thread(site, service)
  return redirect("/live_execs")  

@app.route('/live_execs')
def live_execs():
  execs = manager.live_threads()
  return render_template("live_execs.html",
                          execs=execs,
                          title="Active processes")  

@app.route('/stop_exec')
def stop_exec():
  id = str(request.args.get('exec', None))
  stopped = manager.stop_thread(id)
  return render_template("message.html",
                          title="Execution stopped",
                          text="Execution of {} has been stopped".format(id))