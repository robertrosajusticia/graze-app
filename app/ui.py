#!/usr/bin/python

import uuid
import os
import sys
import json
import glob

# Graze
from graze import Graze
from graze.modules import Time
from graze.services import MongoDB
from graze._common import get_log_dir
from graze.exceptions import MongoError
from graze.schemas import(
    config_schema,
    crawler_template_schema,
    scraper_template_schema
)

# Flask
from flask import (
    Flask,
    render_template,
    url_for,
    abort,
    jsonify,
    request,
    redirect,
    flash
)

from datetime import datetime
from bson.objectid import ObjectId


app = Flask(__name__)

# Set session secret key
app.secret_key = 'some_secret'


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


def render_template_validation(template, servicefor):
    if servicefor == "crawler":
        template_schema = crawler_template_schema
    else:
        template_schema = scraper_template_schema



    return template_schema.validated(template), template_schema.errors


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
        title="Active processes"
    )

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
        item=item,  # Template expects it when edit
        function="schedule_save",
        btn_txt="Create new schedule",
        mil_to_date=time.mil_to_date  # Template expects it when edit
    )

@app.route('/schedule_save')
def save_shedule():
    name = str(request.args.get('name', None))
    service_for = str(request.args.get('service_for', None))

    interval_type = str(request.args.get('interval_type', None))
    interval_value = str(request.args.get('interval_value', None))

    if interval_type == "weekly":
        interval = time.time_to_mil(int(interval_value)*24*7)
    elif interval_type == "daily":
        interval = time.time_to_mil(int(interval_value)*24)
    elif interval_type == "hour":
        interval = time.time_to_mil(int(interval_value))
    else:
        # A week by default
        interval = 7*24*60*60*1000

    date_from = time.date_to_mil(datetime.strptime(request.args.get('date_from', None), '%d-%m-%Y %H:%M'))
    config_id = str(request.args.get('config_id', None))

    db.add_schedule({
        "name": name,
        "for": service_for,
        "interval": interval,
        "next_execution": date_from,
        "last_execution": "",
        "config_id": config_id
    })

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

    if interval_type == "weekly":
        interval = time.time_to_mil(int(interval_value)*24*7)
    elif interval_type == "daily":
        interval = time.time_to_mil(int(interval_value)*24)
    elif interval_type == "hour":
        interval = time.time_to_mil(int(interval_value))
    else:
        interval = 7*24*60*60*1000

    date_from = time.date_to_mil(datetime.strptime(request.args.get('date_from', None), '%d-%m-%Y %H:%M'))
    config_id = str(request.args.get('config_id', None))

    db.update_schedule(id, {'$set': {
        "name": name,
        "for": service_for,
        "interval": interval,
        "next_execution": date_from,
        "config_id": config_id
    }})

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

    normalised_template, errors = render_template_validation(template, servicefor)
    if normalised_template:
        db.add_template({
            "name": name,
            "for": servicefor,
            "template": normalised_template
        })

        return render_template("message.html",
                            title="Create new template",
                            text="Template created successfully",
                            function="template_list")
    else:
        item = {}
        item['name'] = name
        item['for'] = servicefor
        item['template'] = str(json.dumps(template, indent=4))

        flash("The template you uploaded is invalid, please check the errors and try again: ")
        for error in errors:
            for text in errors[error][0]: # It's contained in an object whose 1st item is the content
                flash("  - Error found in '" + str(error) + "': " + text + ": " + str(errors[error][0][text][0]))

        return render_template("template_edit.html",
                            item= item,
                            btn_txt="Create new template",
                            function="template_save")

@app.route('/template_update')
def update_template():
    id = str(request.args.get('id', None))
    name = str(request.args.get('name', None))
    servicefor = str(request.args.get('service_for', None))
    template = request.args.get('template', None).decode('utf-8')
    template = json.loads(template)

    normalised_template, errors = render_template_validation(template, servicefor)
    if normalised_template:
        db.update_template(id, {
            '$set': {
                "name": name,
                "for": servicefor,
                "template": normalised_template
            }
        })

        return render_template("message.html",
            title="Update template",
            text="Template updated successfully",
            function="template_list"
        )

    else:
        item = {}
        item["_id"] = id
        item['name'] = name
        item['for'] = servicefor
        item['template'] = str(json.dumps(template, indent=4))

        flash("The template you uploaded is invalid, please check the errors and try again: ")
        for error in errors:
            for text in errors[error][0]: # It's contained in an object whose 1st item is the content
                flash("  - Error found in '" + str(error) + "': " + text + ": " + str(errors[error][0][text][0]))

        return render_template("template_edit.html",
                            item= item,
                            btn_txt="Update template",
                            function="template_update")


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

    db.add_config({
        "name": name,
        "config": {
            "site": site,
            "start_url": start_url,
            "user_id": user_id,
            "session_id": session_id,
            "crawler_template_key": oid(crawler_template_key),
            "scraper_template_key": oid(scraper_template_key)
        }
    })

    # TODO AS: Validate config here using graze.schemas.config

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

    db.update_config(id, {
        '$set': {
            "name": name,
            "config": {
                "site": site,
                "start_url": start_url,
                "user_id": item['user_id'],
                "session_id": item['session_id'],
                "crawler_template_key": oid(crawler_template_key),
                "scraper_template_key": oid(scraper_template_key)
            }
    }})

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









### ---- ###
### LOGS ###
### ---- ###

LOG_DIR = get_log_dir()

def get_logpaths(filter=""):
    return [log for log in glob.glob(os.path.join(LOG_DIR, '*.log'))
        if filter in log]

@app.route('/logs')
def logs():
    logs = []
    config_documents = db.get_configs({})

    for log in get_logpaths():
        config_document = get_config_from_log(config_documents, log)
        if config_document:
            logs.append({
                'name': config_document.get('name'),
                'site': config_document['config']['site'],
                'path': os.path.basename(log),
                'last_modified': getFileLastMofifiedTimestamp(log),
            })

    return render_template("logs.html",
        title="Logs",
        items=logs
    )

@app.route('/log')
def log():
    logname = str(request.args.get('name'))
    _logpath = str(request.args.get('path'))
    logpath = os.path.join(LOG_DIR, _logpath)

    if os.path.exists(logpath):
        log = request.args.copy()
        with open(logpath, "r") as fileobj:
            log['content'] = fileobj.read()
            return render_template("log.html",
                title="{} Log".format(logname),
                log=log)

    return render_template("message.html",
        title="Error {}".format(logname),
        text="No log exists with a name of {}.".format(logname),
        function="log_list")


@app.route('/delete_log')
def delete_log():
    pass


def getFileLastMofifiedTimestamp(filepath):
    return int(os.path.getmtime(filepath)) * 1000





def get_config_from_log(config_documents, logname):
    for x in config_documents:
        if x.get('_id', '').__str__() in logname:
            return x

def helper__print_attrs(obj):
    # prints obj.x, obj.y etc
    print "\n\n\n****"
    for x in dir(obj):
        print x
    print "****\n\n\n"
    raise

def helper__print_keys(obj):
    # prints obj['x'], obj['y'] etc
    print "\n\n\n****"
    for x in obj.keys():
        print x
    print "****\n\n\n"
    raise
