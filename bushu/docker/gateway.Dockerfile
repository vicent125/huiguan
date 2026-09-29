FROM nginx:1.27-alpine
COPY bushu/nginx/render.conf /etc/nginx/conf.d/default.conf
COPY bushu/nginx/proxy_params /etc/nginx/proxy_params
COPY zhineng_shuifei/web /usr/share/nginx/html
COPY nongyeguanlipingtai /usr/share/nginx/html/nongye
EXPOSE 10000
