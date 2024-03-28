docker build . -t nilkad/hw4
docker run -d --name hw4 -v c:\temp\my_volume:/app/storage -p 3000:3000 nilkad/hw4