import subprocess
import time

from celery import Celery
from pottery import Redlock
import redis

from osism.tasks import Config

app = Celery('reconciler')
app.config_from_object(Config)


@app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    sender.add_periodic_task(600.0, run.s(), expires=10)
    # sender.add_periodic_task(600.0, sync_inventory_with_netbox.s(), expires=10)


@app.task(bind=True, name="osism.tasks.reconciler.run")
def run(self):
    r = redis.Redis(host="redis", port="6379")
    lock = Redlock(key="lock_osism_tasks_reconciler_run",
                   masters={r},
                   auto_release_time=60*1000)

    if lock.acquire(blocking=False):

        # NOTE: Synthetic pause to wait for synchronization
        time.sleep(10)

        p = subprocess.Popen("/run.sh", shell=True)
        p.wait()

    r.close()


@app.task(bind=True, name="osism.tasks.reconciler.sync_inventory_with_netbox")
def sync_inventory_with_netbox(self):
    r = redis.Redis(host="redis", port="6379")
    lock = Redlock(key="lock_osism_tasks_reconciler_sync_inventory_with_netbox",
                   masters={r},
                   auto_release_time=60*1000)

    if lock.acquire(blocking=False):

        # NOTE: Synthetic pause to wait for synchronization
        time.sleep(10)

        p = subprocess.Popen("/sync-inventory-with-netbox.sh", shell=True)
        p.wait()

    r.close()
