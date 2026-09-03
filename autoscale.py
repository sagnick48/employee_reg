import time
import subprocess
import docker

SERVICE_NAME = "api"
MAX_CONTAINERS = 6
UP_THRESHOLD = 20.0
MEM_UP_THRESHOLD = 8
CHECK_INTERVAL = 10
client = docker.from_env()
def get_running_count():
    containers = client.containers.list(filters={"status": "running"})
    return sum(1 for c in containers if f"-{SERVICE_NAME}-" in c.name)
def get_max_cpu_usage():
    max_cpu = 0.0
    containers = client.containers.list(filters={"status": "running"})
    app_containers = [c for c in containers if f"-{SERVICE_NAME}-" in c.name]
    if not app_containers:
        return 0.0, False
    for container in app_containers:
        stats = container.stats(stream=False)
        cpu_delta = stats['cpu_stats']['cpu_usage']['total_usage'] - stats['precpu_stats']['cpu_usage']['total_usage']
        system_delta = stats['cpu_stats']['system_cpu_usage'] - stats['precpu_stats']['system_cpu_usage']
        
        if system_delta > 0.0 and cpu_delta > 0.0:
            cpu_percent = (cpu_delta / system_delta) * stats['cpu_stats']['online_cpus'] * 100.0
        else:
            cpu_percent = 0.0
        if cpu_percent > max_cpu:
            max_cpu = cpu_percent
    return max_cpu
def get_max_mem_usage():
    max_mem=0
    containers = client.containers.list(filters={"status":"running"})
    app_containers = [c for c in containers if f"-{SERVICE_NAME}-" in c.name]
    if not app_containers:
        return 0.0, False
    for container in app_containers:
        stats = container.stats(stream=False)
        mem_stats = stats.get("memory_stats", {})
        usage = mem_stats.get("usage", 0)
        details = mem_stats.get("stats", {})
        cache = details.get("inactive_file", details.get("total_inactive_file", details.get("cache", 0)))
        active_memory = (usage - cache)/(1024*1024)
        limit = (mem_stats.get("limit", 1))/(1024*1024)
        mem_usage = (active_memory / limit) * 100
        if max_mem<mem_usage:
            max_mem=mem_usage
    return max_mem
def scale_service(count):
    print(f"Scaling {SERVICE_NAME} to {count} containers...")
    subprocess.run(["docker", "compose", "up", "-d", "--scale", f"{SERVICE_NAME}={count}"])
    subprocess.run(["docker","exec","reverse_proxy_for_empapp","nginx","-s","reload"])
print("Starting Python Autoscaler. Press Ctrl+C to stop.")

while True:
    current_count = get_running_count()
    max_cpu = get_max_cpu_usage()
    max_mem_usage=get_max_mem_usage()
    print(f"[Monitor] Active Containers: {current_count} | Highest CPU: {max_cpu:.1f}% | Highest RAM: {max_mem_usage:.1f}%")
    if max_cpu > UP_THRESHOLD and current_count < MAX_CONTAINERS:
        new_count = current_count + 1
        print(f"High load detected ({max_cpu:.1f}%).")
        scale_service(new_count)
        time.sleep(10)  
    if max_mem_usage>MEM_UP_THRESHOLD and current_count < MAX_CONTAINERS:
        new_count = current_count + 1
        scale_service(new_count)
        time.sleep(10)
    time.sleep(CHECK_INTERVAL)
