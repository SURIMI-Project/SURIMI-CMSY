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
    libfontconfig1-dev \
    libfreetype6-dev \
    libharfbuzz-dev \
    libfribidi-dev \
    libpng-dev \
    libcairo2-dev \
    libjpeg-dev \
    libtiff5-dev \
    libgif-dev \
    gfortran \
    libreadline-dev \
    wget \
    locales \
    && echo "en_US.UTF-8 UTF-8" > /etc/locale.gen \
    && locale-gen \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install JAGS 4.3.1 from source
RUN wget https://sourceforge.net/projects/mcmc-jags/files/JAGS/4.x/Source/JAGS-4.3.1.tar.gz \
    && tar -xvzf JAGS-4.3.1.tar.gz \
    && cd JAGS-4.3.1 \
    && ./configure \
    && make \
    && make install \
    && cd .. \
    && rm -rf JAGS-4.3.1 JAGS-4.3.1.tar.gz

    
RUN apt-get update && apt-get install -y --no-install-recommends \
    texlive-xetex \
    texlive-fonts-recommended \
    texlive-latex-extra \
    fonts-dejavu \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*


# Set environment variables for R and JAGS
ENV PATH="/usr/lib/R/bin:${PATH}"
ENV R_HOME=/usr/lib/R
ENV RPY2_R_HOME=/usr/lib/R
ENV R_LIBS_USER=/usr/local/lib/R/site-library
ENV R_ENVIRON_USER=/usr/lib/R/etc/Renviron
ENV LD_LIBRARY_PATH=/usr/local/lib

# Install R packages that depend on JAGS
RUN Rscript -e "install.packages(c('rjags', 'R2jags', 'stringr'), repos='https://cloud.r-project.org')"

# Install devtools and snpar from GitHub
RUN Rscript -e "install.packages('devtools', repos='https://cloud.r-project.org')" \
    && Rscript -e "devtools::install_github('debinqiu/snpar')"

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
EXPOSE 50201

# OpenTelemetry config
ENV OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317
ENV OTEL_SERVICE_NAME=cmsy

# Run the server
CMD ["python", "server/app.py"]
