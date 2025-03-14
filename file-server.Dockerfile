FROM node:22-slim

# Install http-server globally to avoid npx re-downloads
RUN npm install -g http-server

# Create directory structure and copy files
WORKDIR /app
COPY ./backend_storage ./backend_storage

# Expose port and run server
EXPOSE 8080
CMD ["http-server", "/app/backend_storage", "--cors", "-p", "8080"]
