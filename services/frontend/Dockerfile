FROM node:20-slim

WORKDIR /app

# install a tiny static server
RUN npm install -g serve

# copy app files
COPY . .

EXPOSE 3000

# serve the current directory on port 3000
CMD ["serve", "-s", "-l", "3000", "."]