FROM ubuntu:24.04
ARG DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates curl unzip libgtk-3-0t64 libxtst6 libxi6 libxrender1 xvfb xauth dbus-x11 fonts-dejavu-core && rm -rf /var/lib/apt/lists/*
ARG CAPELLA_URL=https://download.eclipse.org/capella/core/products/releases/7.0.1/capella-7.0.1.202503211540-linux-gtk-aarch64.tar.gz
ARG DOCGEN_URL=https://download.eclipse.org/capella/addons/xhtmldocgen/dropins/releases/7.0.0/CapellaXHTMLDocGen-dropins-7.0.0.202407171012.zip
RUN mkdir -p /opt/capella && curl -fL --retry 3 "$CAPELLA_URL" | tar -xz -C /opt/capella --strip-components=1
RUN curl -fL --retry 3 "$DOCGEN_URL" -o /tmp/docgen.zip && unzip -q /tmp/docgen.zip -d /opt/capella/dropins && rm /tmp/docgen.zip
ENV PATH="/opt/capella:${PATH}"
COPY export.sh /usr/local/bin/export-capella
ENTRYPOINT ["/usr/local/bin/export-capella"]
