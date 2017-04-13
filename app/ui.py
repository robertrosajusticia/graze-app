#!/usr/bin/python

import sys
import uuid
from bson.objectid import ObjectId
from os import path
_path = path.abspath(path.join(path.dirname(path.abspath(__file__)), '..\..\\core'))
sys.path.append(_path)
from graze import (
  Graze, 
  MongoDB,   
  Time
)

from datetime import datetime

import os
import sys
import json
from flask import render_template, url_for, abort, jsonify, request, redirect
from app import app


graze = Graze()
db = MongoDB()
time = Time()

interval_types = [["hour","Hour"],["daily","Day"],["weekly","Week"]]
interval_values = [(str(x), str(x)) for x in range(1, 10+1)]

def generate_session_id(prefix='session'): 
  return '{}{}'.format(prefix, str(uuid.uuid4()).replace('-', ''))

def oid(id_=None):
    if id_ is None:
        return ObjectId()
    if isinstance(id_, ObjectId):
        return id_
    if isinstance(id_, basestring):
        return ObjectId(id_)
    raise MongoError("Could not create ObjectId using: {}".format(id_))


@app.route('/')
@app.route('/index')
def index():	
    items = db.get_statuses()
    return render_template("index.html",
                           title='Home - Status',
                           items=items)

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
                          text="Execution of {} has been stopped".format(id),
                          function="live_execs"
                          )

# Schedule functions

@app.route('/schedule_list')
def show_schedules():
  services = db.get_schedules({})
  return render_template("schedule_list.html",
                          title="Schedule manager",
                          items=services,
                          mil_to_date=time.mil_to_date,
                          mil_to_time=time.mil_to_time
                          )

@app.route('/schedule_edit')
def edit_schedule():  
  id = str(request.args.get('id', None))
  item = db.get_schedule(id)
  item['id'] = item['config_id']
  item['services_list'] = db.get_configs({})
  interval = time.mil_to_time_coded(item['interval'])  
  item['interval_types'] = interval_types
  item['interval_type'] = interval[1]
  item['interval_values'] = interval_values
  item['interval_value'] = interval[0]
  return render_template("schedule_edit.html",
                          title="Edit schedule",
                          item=item,
                          function="schedule_update",
                          btn_txt="Update schedule",
                          mil_to_date=time.mil_to_date
                          )

@app.route('/schedule_new')
def schedule_service():   
  item = {}  
  item['services_list'] = db.get_configs({})
  item['interval_types'] = interval_types
  item['interval_values'] = interval_values
  return render_template("schedule_edit.html",
                          title="Create new schedule",
                          item=item, #Template expects it when edit
                          function="schedule_save",
                          btn_txt="Create new schedule",
                          mil_to_date=time.mil_to_date #Template expects it when edit
                          )

@app.route('/schedule_save')
def save_shedule():       
  name = str(request.args.get('name', None))
  service_for = str(request.args.get('service_for', None))

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

  date_from = time.date_to_mil(datetime.strptime(request.args.get('date_from', None), '%d-%m-%Y %H:%M'))
  config_id = str(request.args.get('config_id', None))

  document = {
              "name": name,
              "for": service_for,
              "interval": interval,
              "next_execution": date_from,                    
              "last_execution": "",
              "config_id": config_id
             }
  db.add_schedule(document)
  return render_template("message.html",
                          title="Create new schedule",
                          text="Schedule scheduled successfully",
                          function="schedule_list"
                          )

@app.route('/schedule_update')
def update_shedule():  
  id = str(request.args.get('id', None))
  name = str(request.args.get('name', None))
  service_for = str(request.args.get('service_for', None))
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

  date_from = time.date_to_mil(datetime.strptime(request.args.get('date_from', None), '%d-%m-%Y %H:%M'))
  config_id = str(request.args.get('config_id', None))

  document = { '$set': { 
              "name": name,
              "for": service_for,
              "interval": interval,
              "next_execution": date_from,                    
              "config_id": config_id
             }}
  db.update_schedule(id, document)
  return render_template("message.html",
                          title="Update schedule",
                          text="Schedule updated successfully",
                          function="schedule_list"
                          )

@app.route('/schedule_delete')
def delete_shedule():  
  id = str(request.args.get('id', None))
  db.delete_schedule(id)   
  items = db.get_schedules({})
  return render_template("schedule_list.html",
                            title="Schedule manager",
                            items=items,
                            mil_to_date=time.mil_to_date,
                            mil_to_time=time.mil_to_time
                            )

# Template functions

@app.route('/template_list')
def show_templates():
  templates = db.get_templates({})
  return render_template("template_list.html",
                          title="Template manager",
                          items=templates
                          )

@app.route('/template_new')
def new_template():  
  item = {}  
  return render_template("template_edit.html",
                          title="Create new template",
                          item=item, #Template expects it when edit
                          btn_txt="Create new template",
                          function="template_save"
                        )

@app.route('/template_edit')
def edit_template(): 
  id = str(request.args.get('id', None))
  item = db.get_template(id)
  item['template'] = str(json.dumps(item['template'], indent=4))
  return render_template("template_edit.html",
                          title="Edit template",
                          item=item,
                          btn_txt="Update template",
                          function="template_update"
                        )

@app.route('/template_save')
def save_template():  
  name = str(request.args.get('name', None))
  servicefor = str(request.args.get('service_for', None))
  template = request.args.get('template', None)
  template = json.loads(template)
  document = {
              "name": name,
              "for": servicefor,
              "template": template
             }
  db.add_template(document)
  return render_template("message.html",
                          title="Create new template",
                          text="Template created successfully",
                          function="template_list"
                          )

@app.route('/template_update')
def update_template():  
  id = str(request.args.get('id', None))
  name = str(request.args.get('name', None))
  servicefor = str(request.args.get('service_for', None))
  template = request.args.get('template', None).decode('utf-8')
  template = json.loads(template)
  document = { '$set': { 
              "name": name,
              "for": servicefor,
              "template": template
             }}
  db.update_template(id, document)
  return render_template("message.html",
                          title="Update template",
                          text="Template updated successfully",
                          function="template_list"
                          )

@app.route('/template_delete')
def delete_template():   
  id = str(request.args.get('id', None))
  db.delete_template(id)   
  templates = db.get_templates({})
  return render_template("template_list.html",
                          title="Template manager",
                          items=templates
                          )


# Config functions

@app.route('/config_list')
def show_configs():
  configs = db.get_configs({})
  return render_template("config_list.html",
                          title="Config files manager",
                          items=configs
                          )

@app.route('/config_new')
def new_config():  
  item = {}  
  item['config'] = {}
  item['crawler_templates'] = db.get_templates({"for": "crawler"})
  item['scraper_templates'] = db.get_templates({"for": "scraper"})
  return render_template("config_edit.html",
                          title="Create new config file",
                          item=item, #config expects it when edit
                          btn_txt="Create new config file",
                          function="config_save"
                        )

@app.route('/config_edit')
def edit_config(): 
  id = str(request.args.get('id', None))
  item = db.get_config(id)
  item['crawler_templates'] = db.get_templates({"for": "crawler"})
  item['scraper_templates'] = db.get_templates({"for": "scraper"})  
  return render_template("config_edit.html",
                          title="Edit config file",
                          item=item,
                          btn_txt="Update config file",
                          function="config_update"
                        )

@app.route('/config_save')
def save_config(): 
  name = str(request.args.get('name', None))
  site = str(request.args.get('site', None))
  start_url = str(request.args.get('start_url', None))
  crawler_template_key = request.args.get('crawler_template_key', None)
  scraper_template_key = request.args.get('scraper_template_key', None)
  user_id = "Demo"
  session_id = generate_session_id()
  document = {
              "name": name,              
              "config": {
                "site": site,
                "start_url": start_url,
                "user_id": user_id,
                "session_id": session_id,
                "crawler_template_key": oid(crawler_template_key),
                "scraper_template_key": oid(scraper_template_key)
              }
             }  

  db.add_config(document) 
  return render_template("message.html",
                          title="Create new config file",
                          text="Config file created successfully",
                          function="config_list"
                          )

@app.route('/config_update')
def update_config():  
  id = str(request.args.get('id', None))
  name = str(request.args.get('name', None))
  site = str(request.args.get('site', None))
  start_url = str(request.args.get('start_url', None))
  crawler_template_key = request.args.get('crawler_template_key', None)
  scraper_template_key = request.args.get('scraper_template_key', None)
  item = db.get_config(id)['config']
  document = { '$set': { 
              "name": name,              
              "config": {
                "site": site,
                "start_url": start_url,
                "user_id": item['user_id'],
                "session_id": item['session_id'],
                "crawler_template_key": oid(crawler_template_key),
                "scraper_template_key": oid(scraper_template_key)
              }
             }}
  db.update_config(id, document)
  return render_template("message.html",
                          title="Update config file",
                          text="Config file updated successfully",
                          function="config_list"
                          )

@app.route('/config_delete')
def delete_config():   
  id = str(request.args.get('id', None))
  db.delete_config(id)   
  configs = db.get_configs({})
  return render_template("config_list.html",
                          title="Config files manager",
                          items=configs
                          )