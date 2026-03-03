FROM nginx:alpine

# Copiar la configuración de nginx
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copiar las pantallas de Stitch a la carpeta pública de nginx
COPY public/ /usr/share/nginx/html/

# Puerto en el que Cloud Run espera el tráfico
EXPOSE 8080

CMD ["nginx", "-g", "daemon off;"]
