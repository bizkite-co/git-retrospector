# Use Amazon Linux 2 as the base image, matching the Lambda runtime environment
FROM amazonlinux:2

# Install Git, Curl for HTTPS support, CA certificates, and necessary utilities
RUN yum update -y && \
    yum install -y git curl ca-certificates zip findutils && \
    yum clean all && \
    update-ca-trust # Update the CA certificate store

# Create the directory structure for the Lambda layer
# Ensure lib64 exists as some dependencies might go there
RUN mkdir -p /opt/bin /opt/lib /opt/lib64 /opt/libexec/git-core /opt/share/git-core /opt/etc/pki/tls/certs

# Copy the Git executable, core components, and curl
RUN cp /usr/bin/git /opt/bin/
RUN cp /usr/bin/curl /opt/bin/ # Copy curl binary
RUN cp -a /usr/libexec/git-core/* /opt/libexec/git-core/
RUN cp -r /usr/share/git-core/* /opt/share/git-core/

# Copy CA certificates bundle
RUN cp /etc/pki/tls/certs/ca-bundle.crt /opt/etc/pki/tls/certs/ca-bundle.crt

# Identify and copy shared library dependencies for git, git-core executables, and curl
# Use -L to copy the target of symlinks. Add paths for lib64.
# Ensure git-remote-https exists and check its dependencies too.
RUN echo "Identifying and copying dependencies..." && \
    GIT_CORE_PATH=/usr/libexec/git-core && \
    ALL_BINARIES="/usr/bin/git /usr/bin/curl" && \
    if [ -f "$GIT_CORE_PATH/git-remote-https" ]; then ALL_BINARIES="$ALL_BINARIES $GIT_CORE_PATH/git-remote-https"; fi && \
    # Add other git-core executables that might be needed
    ALL_BINARIES="$ALL_BINARIES $(find $GIT_CORE_PATH -type f -executable)" && \
    echo "Checking binaries: $ALL_BINARIES" && \
    ldd $ALL_BINARIES | grep '=> /' | awk '{print $3}' | sort | uniq | xargs -I {} sh -c 'cp -vL {} /opt/lib/ || cp -vL {} /opt/lib64/ || echo "Failed to copy {}"'

# Ensure correct permissions
RUN chmod +x /opt/bin/git /opt/bin/curl
RUN find /opt/libexec/git-core -type f -exec chmod +x {} \;

# Set environment variables for Git to find certificates (may not be strictly necessary if curl finds them)
# ENV GIT_SSL_CAINFO=/opt/etc/pki/tls/certs/ca-bundle.crt

# Create the zip file containing the layer contents
# Exclude unnecessary files if any were copied
RUN cd /opt && \
    zip -r9 --symlinks /tmp/git-layer.zip .

# Set the default command to keep the container running (optional, mainly for debugging)
CMD ["/bin/bash"]
