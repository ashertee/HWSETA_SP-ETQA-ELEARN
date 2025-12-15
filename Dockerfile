FROM odoo:18.0

USER root
RUN pip3 install --break-system-packages --no-cache-dir pandas
RUN pip3 install --break-system-packages --no-cache-dir zxcvbn
RUN pip3 install --break-system-packages --no-cache-dir odooly
RUN pip3 install --break-system-packages --no-cache-dir ptpython
RUN pip3 install --break-system-packages --no-cache-dir email_validator
RUN pip3 install --break-system-packages --no-cache-dir xlwt
RUN pip3 install --break-system-packages --no-cache-dir num2words

RUN apt-get update && apt-get install -y \
    gcc \
    git \
    libxml2-dev \
    libxslt1-dev \
    libldap2-dev \
    libsasl2-dev \
#    libpq-dev \
    libjpeg-dev \
    zlib1g-dev \
    libffi-dev \
    libssl-dev \
    libjpeg8-dev \
    liblcms2-dev \
    libblas-dev \
    libatlas-base-dev \
    node-less \
    npm \
    curl \
    && rm -rf /var/lib/apt/lists/*

RUN whoami
USER odoo
RUN pip3 install --break-system-packages --no-cache-dir pandas
RUN pip3 install --break-system-packages --no-cache-dir zxcvbn
RUN pip3 install --break-system-packages --no-cache-dir ptpython
RUN pip3 install --break-system-packages --no-cache-dir email_validator
RUN pip3 install --break-system-packages --no-cache-dir odooly
RUN pip3 install --break-system-packages --no-cache-dir xlwt
RUN pip3 install --break-system-packages --no-cache-dir num2words