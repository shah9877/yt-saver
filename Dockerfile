FROM python:3.11-slim

RUN apt-get update && apt-get install -y ffmpeg

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["python", "app.py"]
```

**5.** Neeche scroll karein → **"Commit new file"** green button click karein ✅

---

### Ab Aapki Repository mein 4 Files hongi:
```
yt-saver/
  ├── app.py
  ├── index.html
  ├── requirements.txt
  └── Dockerfile        ← nai file
