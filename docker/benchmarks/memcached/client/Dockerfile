FROM cloudsuite3/data-caching:client

WORKDIR /usr/src/memcached/memcached_client
COPY ./client_entrypoint.sh ./client_entrypoint.sh

ENTRYPOINT ["./client_entrypoint.sh"]
