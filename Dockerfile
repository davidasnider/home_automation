# Build Image
FROM python:3.10 AS compile-image

RUN useradd -m -u 1000 home_automation
USER home_automation
COPY requirements.txt .
RUN pip install --user -r requirements.txt

# Runtime Image
FROM python:3.10-slim AS final-image
RUN useradd -m -u 1000 home_automation
USER home_automation
COPY --from=compile-image /home/home_automation/.local /home/home_automation/.local

# Keeps Python from generating .pyc files in the container
ENV PYTHONDONTWRITEBYTECODE 1

# Turns off buffering for easier container logging
ENV PYTHONUNBUFFERED 1

# Add .local/bin to the path
ENV PATH /home/home_automation/.local/bin:$PATH

WORKDIR /app
ADD home_automation /app/home_automation
ADD sprinkler_multiplier.py /app/sprinkler_multiplier.py
ADD update_magic_mirror_temp.py /app/update_magic_mirror_temp.py

CMD ["python3", "/app/sprinkler_multiplier.py"]
