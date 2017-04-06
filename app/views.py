#!/usr/bin/python

import sys
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
                          text="Execution of {} has been stopped".format(id),
                          function="live_execs"
                          )

# Schedule functions

@app.route('/schedule_list_crawler')
@app.route('/schedule_list_scraper')
def show_services():
  route = request.url_rule.rule
  service = route[route.rfind("_")+1:]
  services = db.get_schedules({"for": service})
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
  item = db.get_schedule(id)
  item['id'] = item['config_id']
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
  item['services_list'] = db.get_statuses()
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

  date_from = time.date_to_mil(datetime.strptime(request.args.get('date_from', None), '%d-%m-%Y %H:%M'))
  config_id = str(request.args.get('config_id', None))

  document = {
              "name": name,
              "for": service,
              "interval": interval,
              "next_execution": date_from,                    
              "last_execution": "",
              "config_id": config_id
             }
  db.add_schedule(document)
  return render_template("message.html",
                          title="Create new {} schedule".format(service),
                          text="Schedule scheduled successfully",
                          function="schedule_list_{}".format(service)
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

  date_from = time.date_to_mil(datetime.strptime(request.args.get('date_from', None), '%d-%m-%Y %H:%M'))
  config_id = str(request.args.get('config_id', None))

  document = { '$set': { 
              "name": name,
              "for": service,
              "interval": interval,
              "next_execution": date_from,                    
              "config_id": config_id
             }}
  db.update_schedule(id, document)
  return render_template("message.html",
                          title="Update {} schedule".format(service),
                          text="Schedule updated successfully",
                          function="schedule_list_{}".format(service)
                          )

@app.route('/schedule_delete_crawler')
@app.route('/schedule_delete_scraper')
def delete_shedule():  
  route = request.url_rule.rule
  service = route[route.rfind("_")+1:]      
  id = str(request.args.get('id', None))
  db.delete_schedule(id)   
  items = db.get_schedules({"for": service})
  return render_template("schedule_list.html",
                            title="{} manager".format(service),
                            items=items,
                            service=service,
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
  template = str(request.args.get('template', None))
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
  template = request.args.get('template', None)
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
  return render_template("config_edit.html",
                          title="Edit config file",
                          item=item,
                          btn_txt="Update config file",
                          function="config_update"
                        )

@app.route('/config_save')
def save_config():  
  name = str(request.args.get('name', None))
  servicefor = str(request.args.get('service_for', None))
  config = str(request.args.get('config', None))

  document = {
              "name": name,
              "for": servicefor,
              "config": config
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
  servicefor = str(request.args.get('service_for', None))
  config = str(request.args.get('config', None))
  document = { '$set': { 
              "name": name,
              "for": servicefor,
              "config": config
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
