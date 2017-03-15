#!/usr/bin/python

import sys
from os import path
_path = path.abspath(path.join(path.dirname(path.abspath(__file__)), '..\..\\V3.0'))
print _path
sys.path.append(_path)
from graze import (
  Graze, 
  MongoDB, 
  Time
)

from datetime import datetime

import os
import sys
from flask import render_template, url_for, abort, jsonify, request, redirect
from app import app

graze = Graze()
db = MongoDB()
time = Time()

interval_types = [["hour","Hour"],["daily","Day"],["weekly","Week"]]
interval_values = [(str(x), str(x)) for x in range(1, 10+1)]

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

@app.route('/edit_schedule')
def edit_crawlers_scheduler():
  id = str(request.args.get('id', None))
  crawler = db.get_crawler_scheduler(id)
  crawler['status'] = db.get_status_list()
  interval = time.mil_to_time_coded(crawler['interval'])  
  crawler['interval_types'] = interval_types
  crawler['interval_type'] = interval[1]
  crawler['interval_values'] = interval_values
  crawler['interval_value'] = interval[0]
  return render_template("schedule_crawler.html",
                          title="Edit crawler schedule",
                          crawler=crawler,      
                          function="update_schedule",
                          btn_txt="Update schedule",
                          mil_to_date=time.mil_to_date
                          )

@app.route('/schedule_crawler')
def schedule_crawler():  
  crawler = {}  
  crawler['status'] = db.get_status_list()
  crawler['interval_types'] = interval_types
  crawler['interval_values'] = interval_values
  return render_template("schedule_crawler.html",
                          title="Create new crawler schedule",
                          crawler=crawler, #Template expects it when edit
                          function="save_schedule",
                          btn_txt="Create new schedule",
                          mil_to_date=time.mil_to_date #Template expects it when edit
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

  document = {
              "name": name,
              "interval": interval,
              "next_execution": date_from,                    
              "last_execution": "",
              "crawler_id": crawler_id
             }
  db.add_crawler_scheduler(document)
  return render_template("message.html",
                          title="Create new crawler schedule",
                          text="Schedule scheduled successfully"
                          )

@app.route('/update_schedule')
def update_shedule():  
  id = str(request.args.get('id', None))
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

  document = {
              "name": name,
              "interval": interval,
              "next_execution": date_from,                    
              "last_execution": "",
              "crawler_id": crawler_id
             }

  db.update_crawler_scheduler(id, document)
  return render_template("message.html",
                          title="Update crawler schedule",
                          text="Schedule updated successfully"
                          )

@app.route('/delete_schedule')
def delete_shedule():  
  id = str(request.args.get('id', None))
  db.delete_crawler_scheduler(id)   
  crawlers = db.get_crawler_scheduler_list()
  return render_template("crawler.html",
                            title="Crawler manager",
                            crawlers=crawlers,
                            mil_to_date=time.mil_to_date,
                            mil_to_time=time.mil_to_time
                            )
