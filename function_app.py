import azure.functions as func
import requests
import os
import logging

app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)

@app.route(route="health")
def HealthCheck(req: func.HttpRequest) -> func.HttpResponse:
    """Health check endpoint for monitoring"""
    try:
        # Check if we can discover backends
        backends = []
        backend_num = 1
        while True:
            backend_url = os.getenv(f"BACKEND_{backend_num}_URL")
            if backend_url is None:
                break
            backend_active = os.getenv(f"BACKEND_{backend_num}_ACTIVE", "true").lower() == "true"
            backends.append({
                "url": backend_url,
                "active": backend_active
            })
            backend_num += 1
        
        active_backends = [b for b in backends if b["active"] and b["url"]]
        
        health_info = {
            "status": "healthy",
            "timestamp": req.headers.get("Date", "unknown"),
            "total_backends": len(backends),
            "active_backends": len(active_backends),
            "backend_urls": [b["url"] for b in active_backends]
        }
        
        return func.HttpResponse(
            body=str(health_info),
            status_code=200,
            headers={"Content-Type": "application/json"}
        )
    except Exception as e:
        return func.HttpResponse(
            body=f"Health check failed: {str(e)}",
            status_code=500
        )

@app.route(route="webhook")
def AppStoreWebhookProxy(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Processing Apple App Store notification')
    
    # Dynamically discover all BACKEND_*_URL environment variables
    backends = []
    backend_num = 1
    while True:
        backend_url = os.getenv(f"BACKEND_{backend_num}_URL")
        if backend_url is None:
            break
        
        backend_active = os.getenv(f"BACKEND_{backend_num}_ACTIVE", "true").lower() == "true"
        backends.append({
            "url": backend_url,
            "active": backend_active
        })
        backend_num += 1
    
    active_backends = [b for b in backends if b["active"] and b["url"]]
    
    if not active_backends:
        logging.warning("No active backends configured")
        return func.HttpResponse("No active backends configured", status_code=500)
    
    failures = []

    for backend in active_backends:
        try:
            response = requests.post(
                backend["url"],
                data=req.get_body(),
                headers={
                    "Content-Type": "application/json",
                    "X-Apple-Signature": req.headers.get("X-Apple-Signature", ""),
                    "X-Apple-Notification-Type": req.headers.get("X-Apple-Notification-Type", "")
                },
                timeout=30
            )
            response.raise_for_status()
            logging.info(f"Successfully forwarded to {backend['url']} (status: {response.status_code})")
        except requests.exceptions.Timeout:
            failures.append(f"{backend['url']} (timeout)")
            logging.error(f"Timeout forwarding to {backend['url']}")
        except requests.exceptions.ConnectionError:
            failures.append(f"{backend['url']} (connection error)")
            logging.error(f"Connection error forwarding to {backend['url']}")
        except requests.exceptions.HTTPError as e:
            failures.append(f"{backend['url']} (HTTP {e.response.status_code})")
            logging.error(f"HTTP error forwarding to {backend['url']}: {e.response.status_code}")
        except Exception as e:
            failures.append(f"{backend['url']} (error: {str(e)})")
            logging.error(f"Failed to forward to {backend['url']}: {str(e)}")

    if not failures:
        logging.info(f"Successfully delivered to all {len(active_backends)} active backends")
        return func.HttpResponse("OK", status_code=200)
    else:
        logging.error(f"Failed to deliver to {len(failures)} out of {len(active_backends)} backends")
        return func.HttpResponse(
            f"Failed to deliver to {len(failures)} out of {len(active_backends)} backends: {', '.join(failures)}", 
            status_code=500
        )