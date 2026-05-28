FROM python:3.12-slim

ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies, R, and build tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    r-base \
    build-essential \
    libcurl4-openssl-dev \
    libssl-dev \
    libxml2-dev \
    libpcre2-dev \
    liblzma-dev \
    libbz2-dev \
    zlib1g-dev \
    libblas-dev \
    liblapack-dev \
    gfortran \
    libreadline-dev \
    jags \
    locales \
    && echo "en_US.UTF-8 UTF-8" > /etc/locale.gen \
    && locale-gen \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Set environment variables for R and JAGS
ENV PATH="/usr/lib/R/bin:${PATH}"
ENV R_HOME=/usr/lib/R
ENV RPY2_R_HOME=/usr/lib/R
ENV R_LIBS_USER=/usr/local/lib/R/site-library
ENV R_ENVIRON_USER=/usr/lib/R/etc/Renviron

# Install R packages that depend on JAGS
RUN Rscript -e "install.packages(c('rjags', 'R2jags', 'stringr'), repos='https://cloud.r-project.org')"

# Install snpar from GitHub
RUN Rscript -e "install.packages('remotes', repos='https://cloud.r-project.org')" \
    && Rscript -e "remotes::install_github('debinqiu/snpar')"

# Set the working directory inside the container
WORKDIR /app

# Copy the requirements.txt file into the container
COPY requirements.txt /app/requirements.txt

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy all the application files into the container
COPY . /app

# Add the /app folder to PYTHONPATH so that the `surimi` module is found
ENV PYTHONPATH=/app

# Expose server port
EXPOSE 5021

# OpenTelemetry config
ENV OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317
ENV OTEL_SERVICE_NAME=cmsy

# Run the server -u option is used to ensure that output (logs) is flushed immediately
CMD ["python", "-u", "server/app.py"]
