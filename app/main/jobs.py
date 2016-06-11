__author__ = 'jie'

import time, sys, datetime, os, shutil, zipfile
from flask_rq import job

from .. import app, db
from ..models import Job

from postorder import xls_to_orders

batch_order_queue = app.config['BATCH_ORDER_QUEUE']

@job(batch_order_queue)
def batch_order(job_id, input_file, workdir):
    with app.app_context():
        job = Job.query.filter(Job.uuid == job_id).first()
        outfile = os.path.join(workdir, job_id + '.zip')
        outdir = os.path.join(workdir, 'output')
        tmpdir = os.path.join(workdir, 'tmpdir')
        curdir = os.getcwd()

        if not os.path.exists(outdir):
            os.makedirs(outdir)
        if not os.path.exists(tmpdir):
            os.makedirs(tmpdir)

        try:
            if not job:
                raise Exception, "Failed to find job: %d" % job_id

            job.status = Job.Status.PROCESSING
            db.session.commit()

            def percent_callback(percent):
                percent = int(percent)
                if percent > job.percentage:
                    job.percentage = percent
                    db.session.commit()

            xls_to_orders(input_file, outdir, tmpdir, percent_callback)

            outfile = os.path.abspath(outfile)
            os.chdir(outdir)
            zf = zipfile.ZipFile(outfile, "w", compression=zipfile.ZIP_DEFLATED)
            for root, dirs, files in os.walk("."):
                if root <> ".":
                    zf.write(root)
                for filename in files:
                    filepath = os.path.join(root, filename)
                    zf.write(filepath)
            zf.close()

            job.completion_time = datetime.datetime.utcnow()
            job.status = Job.Status.COMPLETED
            db.session.commit()
        except Exception, inst:
            import traceback
            traceback.print_exc(sys.stderr)
            job.message = "Format error: %s" % inst.message.encode('utf8')
            job.status = Job.Status.FAILED
            db.session.commit()
        finally:
            os.chdir(curdir)
            if os.path.exists(tmpdir):
                shutil.rmtree(tmpdir)
            if os.path.exists(outdir):
                shutil.rmtree(outdir)
