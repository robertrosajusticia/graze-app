#!/usr/bin/python

import sys
from os import path
_path = path.abspath(path.join(path.dirname(path.abspath(__file__)), '..\..\engine'))
print _path
sys.path.append(_path)
from graze import Manager

#import subprocess
#import threading
import uuid
import os
import sys
from flask import render_template, url_for, abort, jsonify, request
from app import app

background_scripts = {}

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
  id = str(uuid.uuid4())
  site = str(request.args.get('site', None))  
  service = str(request.args.get('service', None))  
  background_scripts[id] = False  
  manager.launch_thread(id, site, service)
  return render_template('processing.html', 
                          id=id, 
                          service=service,
                          title='Processing')

@app.route('/is_done')
def is_done():
	id = request.args.get('id', None)
	if id not in background_scripts:
		abort(404)
	return jsonify (done=background_scripts[id])


@app.route('/finished')
def finished():
	return render_template("execution_finished.html",
                          title='Execution Finished')	

   
@app.route('/live_execs')
def live_execs():
  execs = manager.live_threads()
  return render_template("live_execs.html",
                          execs=execs)  