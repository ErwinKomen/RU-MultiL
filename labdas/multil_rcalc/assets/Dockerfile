FROM public.ecr.aws/lambda/provided

ENV R_VERSION=4.0.3
# ENV R_VERSION=4.2.1

RUN yum -y install wget

RUN yum -y install https://dl.fedoraproject.org/pub/epel/epel-release-latest-7.noarch.rpm \
  && wget https://cdn.rstudio.com/r/centos-7/pkgs/R-${R_VERSION}-1-1.x86_64.rpm \
  && yum -y install R-${R_VERSION}-1-1.x86_64.rpm \
  && rm R-${R_VERSION}-1-1.x86_64.rpm

ENV PATH="${PATH}:/opt/R/${R_VERSION}/bin/"

# System requirements for R packages
RUN yum -y install openssl-devel

# Required for tidyverse (note: syntax like CentOS)
RUN yum -y install libxml2-devel

RUN Rscript -e "install.packages(c('httr', 'jsonlite', 'logger', 'logging'), repos = 'https://cloud.r-project.org/')"
RUN Rscript -e "install.packages(c('readxl', 'metafor', 'purrr'), repos = 'https://cloud.r-project.org/')"

# For some reason this needs to be separate and the last one: tidyverse 
RUN Rscript -e "install.packages(c('tidyverse'), repos = 'https://cloud.r-project.org/')"

RUN Rscript -e "install.packages(c('clubSandwich'), repos = 'https://cloud.r-project.org/')"

COPY runtime.R functions.R bootstrap.R ${LAMBDA_TASK_ROOT}/
RUN chmod 755 -R ${LAMBDA_TASK_ROOT}/


RUN printf '#!/bin/sh\ncd $LAMBDA_TASK_ROOT\nRscript bootstrap.R' > /var/runtime/bootstrap \
  && chmod +x /var/runtime/bootstrap


# ========== INITIAL SETTINGS ========
# CMD [ "functions.myRcode" ]

# ========== ACTUAL CALCULATIONS =====
CMD [ "functions.multilingEntry"]

