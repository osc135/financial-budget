#!/bin/sh
set -e

# Only run envsubst if default.conf is writable (Docker Compose)
# In K8s, ConfigMap mounts are read-only and already have correct values
if [ -w /etc/nginx/conf.d/default.conf ]; then
  envsubst '\$BACKEND_HOST' < /etc/nginx/conf.d/default.conf > /tmp/nginx.conf
  mv /tmp/nginx.conf /etc/nginx/conf.d/default.conf
fi

nginx -g 'daemon off;'
