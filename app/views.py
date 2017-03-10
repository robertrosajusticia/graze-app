#!/usr/bin/python

import sys
from os import path
_path = path.abspath(path.join(path.dirname(path.abspath(__file__)), '..\..\\V3.0'))
print _path
sys.path.append(_path)
from graze import Graze
from graze import DB
from graze import Time
from datetime import datetime

import os
import sys
from flask import render_template, url_for, abort, jsonify, request, redirect
from app import app

graze = Graze()
db = DB()
time = Time()

@app.route('/')
@app.route('/index')
def index():	
    dirs = [d for d in os.listdir('..\\engine\sites') if os.path.isdir(os.path.join('..\\engine\sites', d))]
    return render_template("index.html",
                           title='Home',
                           dirs=dirs)

@app.route('/execute')
def execute():
  site = str(request.args.get('site', None))  
  service = str(request.args.get('service', None))  
  graze.launch_thread(site, service)
  return redirect("/live_execs")  

@app.route('/live_execs')
def live_execs():
  execs = graze.live_threads()
  return render_template("live_execs.html",
                          execs=execs,
                          title="Active processes")  

@app.route('/stop_exec')
def stop_exec():
  id = str(request.args.get('exec', None))
  stopped = graze.stop_thread(id)
  return render_template("message.html",
                          title="Execution stopped",
                          text="Execution of {} has been stopped".format(id))

@app.route('/crawler')
def show_crawlers():
  crawlers = db.get_crawler_scheduler_list()
  return render_template("crawler.html",
                          title="Crawler manager",
                          crawlers=crawlers,
                          mil_to_date=time.mil_to_date,
                          mil_to_time=time.mil_to_time
                          )

@app.route('/schedule_crawler')
def schedule_crawler():  
  return render_template("schedule_crawler.html",
                          title="Create new crawler schedule"
                          )

@app.route('/save_schedule')
def save_shedule():  
  name = str(request.args.get('name', None))

  interval_type = str(request.args.get('interval_type', None))
  interval_value = str(request.args.get('interval_value', None))  
  # A week by default
  interval = 7*24*60*60*1000
  if interval_type == "weekly":
    interval = time.time_to_mil(int(interval_value)*24*7)
  elif interval_type == "daily":    
    interval = time.time_to_mil(int(interval_value)*24)
  elif interval_type == "hour":
    interval = time.time_to_mil(int(interval_value))  

  date_from = time.date_to_mil(datetime.strptime(request.args.get('date_from', None), '%Y-%m-%d %H:%M'))
  crawler_id = str(request.args.get('crawler_id', None))

  result = db.add_crawler_scheduler(name, interval, date_from, crawler_id)
  
  if result:
    result_text = "Schedule scheduled successfully"
  else:
    result_text = "It is not been possible to save the schedule, please try again"
  return render_template("message.html",
                          title="Create new crawler schedule",
                          text=result_text
                          )
