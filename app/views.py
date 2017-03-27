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

@app.route('/schedule_list_crawler')
@app.route('/schedule_list_scraper')
def show_services():
  route = request.url_rule.rule
  service = route[route.rfind("_")+1:]
  if service == "crawler":  
    services = db.get_crawler_schedules({})
  else:
    services = db.get_scraper_schedules({})
  return render_template("schedule_list.html",
                          title="{} manager".format(service.title()),
                          items=services,
                          service=service,
                          mil_to_date=time.mil_to_date,
                          mil_to_time=time.mil_to_time
                          )

@app.route('/schedule_edit_crawler')
@app.route('/schedule_edit_scraper')
def edit_service_schedule():
  route = request.url_rule.rule
  service = route[route.rfind("_")+1:]     
  id = str(request.args.get('id', None))
  if service == "crawler":
    item = db.get_crawler_schedule(id)
    item['id'] = item['crawler_id']
  else:
    item = db.get_scraper_schedule(id)
    item['id'] = item['scraper_id']
  item['services_list'] = db.get_statuses()
  interval = time.mil_to_time_coded(item['interval'])  
  item['interval_types'] = interval_types
  item['interval_type'] = interval[1]
  item['interval_values'] = interval_values
  item['interval_value'] = interval[0]
  return render_template("schedule_edit.html",
                          title="Edit {} schedule".format(service),
                          item=item,     
                          service=service, 
                          function="schedule_update_{}".format(service),
                          btn_txt="Update schedule",
                          mil_to_date=time.mil_to_date
                          )

@app.route('/schedule_new_crawler')
@app.route('/schedule_new_scraper')
def schedule_service():  
  route = request.url_rule.rule
  service = route[route.rfind("_")+1:]    
  item = {}  
  item['services_list'] = db.get_services(service)
  item['interval_types'] = interval_types
  item['interval_values'] = interval_values
  return render_template("schedule_edit.html",
                          title="Create new {} schedule".format(service),
                          item=item, #Template expects it when edit
                          service=service,
                          function="schedule_save_{}".format(service),
                          btn_txt="Create new schedule",
                          mil_to_date=time.mil_to_date #Template expects it when edit
                          )

@app.route('/schedule_save_crawler')
@app.route('/schedule_save_scraper')
def save_shedule():  
  route = request.url_rule.rule
  service = route[route.rfind("_")+1:]   
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
  service_id = str(request.args.get('service_id', None))

  document = {
              "name": name,
              "interval": interval,
              "next_execution": date_from,                    
              "last_execution": "",
              "{}_id".format(service): service_id
             }
  if service == "crawler":
    db.add_crawler_schedule(document)
  else:
    db.add_scraper_schedule(document)
  return render_template("message.html",
                          title="Create new {} schedule".format(service),
                          text="Schedule scheduled successfully"
                          )

@app.route('/schedule_update_crawler')
@app.route('/schedule_update_scraper')
def update_shedule():  
  route = request.url_rule.rule
  service = route[route.rfind("_")+1:]    
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
  service_id = str(request.args.get('service_id', None))

  document = { '$set': { 
              "name": name,
              "interval": interval,
              "next_execution": date_from,                    
              "{}_id".format(service): service_id
             }}

  if service == "crawler":
    db.update_crawler_schedule(id, document)
  else:
    db.update_scraper_schedule(id, document)
  return render_template("message.html",
                          title="Update {} schedule".format(service),
                          text="Schedule updated successfully"
                          )

@app.route('/schedule_delete_crawler')
@app.route('/schedule_delete_scraper')
def delete_shedule():  
  route = request.url_rule.rule
  service = route[route.rfind("_")+1:]      
  id = str(request.args.get('id', None))
  if service == "crawler":
    db.delete_crawler_schedule(id)   
    items = db.get_crawler_schedule_list()
  else:
    db.delete_scraper_schedule(id)   
    items = db.get_scraper_schedule_list()  
  return render_template("schedule_list.html",
                            title="{} manager".format(service),
                            items=items,
                            mil_to_date=time.mil_to_date,
                            mil_to_time=time.mil_to_time
                            )
