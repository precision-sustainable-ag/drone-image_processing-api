FROM node:22-slim

# Set proxies
ENV http_proxy=http://proxy.oit.ncsu.edu:3128
ENV https_proxy=http://proxy.oit.ncsu.edu:3128
ENV no_proxy=localhost,127.0.0.1,169.254.169.254,169.254.170.2,.ncsu.edu


# Install http-server globally to avoid npx re-downloads
RUN npm install -g http-server

# Create directory structure and copy files
WORKDIR /app
RUN mkdir -p ./backend_storage
# COPY ./backend_storage ./backend_storage

# Expose port and run server
EXPOSE 8080
CMD ["http-server", "/app/backend_storage", "--cors", "-p", "8080"]
