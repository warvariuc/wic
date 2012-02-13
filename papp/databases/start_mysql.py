# author Victor Varvariuc <victor.varvariuc@gmail.com>
# tested on Ubuntu Linux 11.10

import os, sys, subprocess
import errno
import pymysql


def call(cmd):
    print('\nExecuting:', cmd)
    try:
        output = subprocess.check_output(cmd, stderr=subprocess.STDOUT, shell=True)
    except subprocess.CalledProcessError as exc:
        print('Failure.', exc.output.decode())
        raise
    else:
        print('Success.', output.decode())
        return True


this_dir = os.path.abspath(os.path.dirname(__file__))

data_dir = "%s/mysql_db_data/" % this_dir

print('Checking if mysql db data dir exists (%s)' % data_dir)
if not os.path.isdir(data_dir):
    print('Dir not found. Initilizing new db in `%s`' % data_dir)
    user = os.getlogin()
    call('mysql_install_db --datadir="%(data_dir)s" --force --user=%(user)s' % locals())
else:
    print('DB data dir exists.')
    #call('rm -rf "%s"' % data_dir)


pid_file = "%s/mysql.pid" % this_dir
print('Checking if pid file exists (%s).' % pid_file)
mysqld_is_running = False

if os.path.isfile(pid_file):
    print('Found mysqld pid file (%s).' % pid_file)
    with open(pid_file) as file:
        pid = int(file.read())
        print('Checking if mysqld (pid=%s) is running.' % pid)
        try:
            os.kill(pid, 0)
        except OSError as exc: # http://docs.python.org/py3k/library/errno.html
            if exc.errno == errno.ESRCH: # No such process
                print("Not running")
            elif exc.errno == errno.EPERM: # Operation not permitted
                mysqld_is_running = True
                print("No permission to signal this process!")
            else:
                print("Unknown error")
        else: # mysqld received the signal - it is running
            print('Mysqld is running.')
            mysqld_is_running = True

port = 3307
pymysql.connect(user='root', passwd='', host='localhost', port=port)
socket_file = "%s/mysql.socket" % this_dir

args = ['mysqld', '-h', data_dir, '--port', str(port), '--socket', socket_file, '--pid-file', pid_file]
print('Starting mysqld in background.', args)
subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
#call('mysqld --datadir="%(data_dir)s" --port=%(port)s --socket="%(socket_file)s" --pid-file="%(pid_file)s"' % locals())
