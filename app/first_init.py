from config import *
from app import app, db, logger as log
from app.models import Users, Devices, Job, Extensions, Setup
from app.utils.system import SYS_get_hostname
from app.utils.db_mgmt import database_allowed
from app.utils.tasks import (
    read_CPU,
    read_RAM,
    read_NET,
    retention_files,
    maitenance_server,
)

from flask_apscheduler import APScheduler
from sqlalchemy import text
import subprocess
import logging
import csv
import os


def database_init():
    log.info("Initialisation database")
    with app.app_context():
        pg_add_extension()
        db.create_all()
        db.session.commit()

        # log.info("Load stamp migration in database")
        # stamp_migration()

        create_admin_job()

        create_admin_user()

        create_server_device()

        pg_add_hypertable()

        add_mimetype_extention()

        setup_maintenance()

        check_data_folder()

        set_maintenance()

        end_intallation()
        # log.info("Upgrade database if need")
        # upgrade_migration()


def create_admin_user():
    if Users.query.filter_by(username="admin").first() is None:
        log.info("Create admin user")
        set_admin = Users(
            name="SABU",
            firstname="Admin",
            email="admin@sabu.fr",
            username="admin",
            role="Admin",
            job_id=1,
        )
        set_admin.set_password("P4$$w0rdF0r54Bu5t4t10N")
        db.session.add(set_admin)
        db.session.commit()
    return None


def create_admin_job():
    if Job.query.filter_by(name="Administrator").first() is None:
        log.info("Create Administrator job")
        set_job_admin = Job(name="Administrator")
        db.session.add(set_job_admin)
        db.session.commit()
    return None


def create_server_device():
    if Devices.query.filter_by(token="server").first() is None:
        log.info("Create server device")
        set_device_server = Devices(
            hostname=SYS_get_hostname(),
            description="This is the master server",
            token="server",
            state=1,
        )
        db.session.add(set_device_server)
        db.session.commit()
    return None


def pg_add_extension():
    if "postgresql" == database_allowed()[:10]:
        with db.engine.connect() as con:
            con.execute(text("CREATE EXTENSION IF NOT EXISTS pgcrypto;"))
            con.execute(text("CREATE EXTENSION IF NOT EXISTS timescaledb;"))
            con.commit()


def pg_add_hypertable():
    with db.engine.connect() as con:
        # For log metrics
        con.execute(
            text(
                "SELECT create_hypertable('metrics', by_range('timestamp_ht', INTERVAL '24 hours'),migrate_data => true, if_not_exists => true);"
            )
        )
        con.execute(
            text(
                "SELECT add_retention_policy('metrics', INTERVAL '7 days',if_not_exists => true);"
            )
        )

        # For scan log
        con.execute(
            text(
                "SELECT create_hypertable('usblog', by_range('date_ht', INTERVAL '24 hours'),migrate_data => true, if_not_exists => true);"
            )
        )
        con.execute(
            text(
                "SELECT add_retention_policy('usblog', INTERVAL '8 days',if_not_exists => true);"
            )
        )
        con.commit()


def add_mimetype_extention():
    if Extensions.query.count() == 0:
        with open("mime.csv", "r") as csvfile:
            reader = csv.reader(csvfile, delimiter=",")
            for ext_mime in reader:
                extension_row = Extensions(extension=ext_mime[0], mimetype=ext_mime[1])
                db.session.add(extension_row)
                db.session.commit()
    return


def setup_maintenance():
    if Setup.query.filter_by(action="ret").first() is None:
        ret = Setup(action="ret", value="30")
        db.session.add(ret)
        db.session.commit()
    if Setup.query.filter_by(action="appc").first() is None:
        appc = Setup(action="appc", value="ED")
        db.session.add(appc)
        db.session.commit()
    if Setup.query.filter_by(action="appt").first() is None:
        appt = Setup(action="appt", value="02:00")
        db.session.add(appt)
        db.session.commit()


def check_data_folder():
    quarantine_path = f"{DATA_PATH}/quarantine"
    data_path = f"{DATA_PATH}/data"
    scan_path = f"{DATA_PATH}/scan"
    if not os.path.exists(quarantine_path):
        log.info("Creating to quarantine path")
        os.makedirs(quarantine_path)
    if not os.path.exists(data_path):
        log.info("Creating to data path")
        os.makedirs(data_path)
    if not os.path.exists(scan_path):
        log.info("Creating to scan path")
        os.makedirs(scan_path)
    return ""


def set_maintenance():
    # APSchelduler
    logging.getLogger("apscheduler").setLevel(logging.ERROR)

    scheduler = APScheduler()
    scheduler.api_enabled = False
    scheduler.init_app(app)
    scheduler.add_job(trigger="interval", id="readCPU", func=read_CPU, seconds=60)
    scheduler.add_job(trigger="interval", id="readRAM", func=read_RAM, seconds=60)
    scheduler.add_job(trigger="interval", id="readNET", func=read_NET, seconds=60)
    scheduler.add_job(
        trigger="cron",
        id="retentionFiles",
        func=retention_files,
        day="*",
        month="*",
        hour=1,
        minute=0,
    )
    # Maintenance server job
    with app.app_context():
        query_maintenace_circle = Setup.query.filter_by(action="appc").first()
        query_maintenace_time = Setup.query.filter_by(action="appt").first()
        if query_maintenace_time is not None and query_maintenace_circle is not None:
            hour = query_maintenace_time.value.split(":")[0]
            minute = query_maintenace_time.value.split(":")[1]
            if query_maintenace_circle.value == "ED":
                scheduler.add_job(
                    trigger="cron",
                    id="maitenanceServerED",
                    func=maitenance_server,
                    day="*",
                    hour=int(hour),
                    minute=int(minute),
                )
            if query_maintenace_circle.value == "EW":
                scheduler.add_job(
                    trigger="cron",
                    id="maitenanceServerEW",
                    func=maitenance_server,
                    day_of_week="1",
                    hour=int(hour),
                    minute=int(minute),
                )
            if query_maintenace_circle.value == "EM":
                scheduler.add_job(
                    trigger="cron",
                    id="maitenanceServerEM",
                    func=maitenance_server,
                    day="1",
                    month="*",
                    hour=int(hour),
                    minute=int(minute),
                )

    scheduler.start()


def end_intallation():
    if Setup.query.filter_by(action="setup").first() is None:
        set_setup = Setup(action="setup", value="1")
        db.session.add(set_setup)
        db.session.commit()
        subprocess.Popen(["sudo", "/usr/bin/systemctl", "restart", "sabu.service"])
