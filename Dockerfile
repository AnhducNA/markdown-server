FROM paddlepaddle/paddle:2.6.2

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# System dependencies:
# - poppler-utils: convert PDF -> image
# - libgl1/libglib2.0-0: OpenCV runtime
RUN apt-get update && apt-get install -y \
    poppler-utils \
    libgl1 \
    libglib2.0-0 \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

# paddlepaddle is already installed in the base image; only install extras
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app

RUN mkdir -p /app/input /app/output

CMD ["python", "/app/app/main.py"]