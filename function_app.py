import azure.functions as func
import requests
import os
import logging

app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)

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
                timeout=5
            )
            response.raise_for_status()
        except Exception as e:
            failures.append(backend["url"])
            logging.error(f"Failed to forward to {backend['url']}: {str(e)}")

    if not failures:
        return func.HttpResponse("OK", status_code=200)
    else:
        return func.HttpResponse(
            f"Failed to deliver to: {', '.join(failures)}", 
            status_code=500
        )