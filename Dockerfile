FROM paddlepaddle/paddle:2.6.2

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV LANG=C.UTF-8
ENV LC_ALL=C.UTF-8

WORKDIR /app

# System dependencies:
# - poppler-utils: convert PDF -> image
# - libgl1/libglib2.0-0: OpenCV runtime
# - fonts-dejavu-core/fonts-noto-cjk: UTF-8 fonts for multi-language rendering
RUN apt-get update && apt-get install -y \
    poppler-utils \
    libgl1 \
    libglib2.0-0 \
    libgomp1 \
    fonts-dejavu-core \
    fonts-noto-cjk \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

# Install PyTorch CPU and VietOCR dependencies
RUN pip install --no-cache-dir torch torchvision --index-url https://download.pytorch.org/whl/cpu
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app

RUN mkdir -p /app/input /app/output

EXPOSE 6868

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "6868"]