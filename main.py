import json
import subprocess
import threading
import time
import requests
import psutil

def load_config():
    with open('config.json') as f:
        return json.load(f)

def exec_rclone(command):
    while True:
        process = subprocess.Popen(["rclone"] + command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1, universal_newlines=True)
        while True:
            output = process.stdout.readline()
            if not output and process.poll() is not None:
                break
            if output:
                print(output.strip())
        print("rclone move completed. Restarting...")
        # 延迟重新启动，根据需要调整
        time.sleep(2)

def get_disk_usage():
    return psutil.disk_usage('/').percent

def control_qbittorrent(url, username, password, target_action):
    session = requests.Session()
    response = session.post(f'{url}/api/v2/auth/login', data={'username': username, 'password': password})
    if not response.ok:
        print("qBittorrent login failed")
        return

    torrents_info = session.get(f'{url}/api/v2/torrents/info').json()
    if target_action == 'pause' and all(t['state'] in ['pausedDL', 'pausedUP'] for t in torrents_info):
        print("All torrents already paused.")
        return
    elif target_action == 'resume' and all(t['state'] not in ['pausedDL', 'pausedUP'] for t in torrents_info):
        print("All torrents already active.")
        return

    if target_action == 'pause':
        session.post(f'{url}/api/v2/torrents/pause', data={'hashes': 'all'})
        print("Paused all qBittorrent tasks.")
    elif target_action == 'resume':
        session.post(f'{url}/api/v2/torrents/resume', data={'hashes': 'all'})
        print("Resumed all qBittorrent tasks.")

def monitor_disk_and_control_qbittorrent(config):
    while True:
        usage = get_disk_usage()
        print(f"Current disk usage: {usage}%")
        if usage > config["diskUsageThreshold"]["high"]:
            control_qbittorrent(config["qBittorrent"]["url"], config["qBittorrent"]["username"], config["qBittorrent"]["password"], 'pause')
        elif usage < config["diskUsageThreshold"]["low"]:
            control_qbittorrent(config["qBittorrent"]["url"], config["qBittorrent"]["username"], config["qBittorrent"]["password"], 'resume')
        time.sleep(60)  # Check every minute

def main():
    config = load_config()
    threading.Thread(target=exec_rclone, args=(config["rcloneCommand"],), daemon=True).start()
    monitor_disk_and_control_qbittorrent(config)

if __name__ == "__main__":
    main()
