import concurrent.futures
import time
import requests

#Config
TARGET_URL = "http://localhost:8888" 
WORKERS = 50000    
DURATION = 30  


def send_request(request_id):
    start_time = time.time()
    try:
        response = requests.get(TARGET_URL, timeout=5)
        duration = time.time() - start_time
        return response.status_code, duration
    except requests.exceptions.RequestException as e:
        return "ERROR", time.time() - start_time


def blast_traffic(num_workers, duration):
    print(f"\n[TEST START] Simulating {num_workers} concurrent users for {duration}s...")
    timeout_expiry = time.time() + duration
    success_count = 0
    error_count = 0
    latencies = []

    with concurrent.futures.ThreadPoolExecutor(max_workers=num_workers) as executor:
        req_id = 0
        while time.time() < timeout_expiry:
            futures = [executor.submit(send_request, req_id + i) for i in range(num_workers)]
            req_id += num_workers
            for future in concurrent.futures.as_completed(futures):
                status, latency = future.result()
                latencies.append(latency)
                if status == 200:
                    success_count += 1
                else:
                    error_count += 1
            time.sleep(0.1)
    avg_latency = sum(latencies) / len(latencies) if latencies else 0
    print(f"[TEST STATS] Success: {success_count} | Errors: {error_count}")
    print(f"[TEST STATS] Avg Latency: {avg_latency:.4f}s")


if __name__ == "__main__":
    print(f"Target API under test: {TARGET_URL}")
    print("Beginning auto-scaling traffic simulation...")
    blast_traffic(WORKERS, DURATION)
    print("\nTraffic generation script completed.")
