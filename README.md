# HAProxy Redis Sentinel

Python pub/sub based Sentinel master change notifier that updates HAProxy using it's [Runtime API](https://www.haproxy.com/documentation/haproxy-runtime-api/)

Just create a simple HAProxy config and it will handle everything for you

```conf
global
  stats socket /var/run/haproxy/haproxy.sock user haproxy group haproxy mode 660 level admin
  stats timeout 2m

frontend redis_master
    bind *:6379
    default_backend redis_master

backend redis_master
```

Is enough

To run this project install `poetry` (and run `poetry install`) or use `direnv` that handles automatic installation of requirements and the project itself

## Usage

`poetry run haproxy-redis-sentinel` is our command entrypoint

### Sentinel Info
- `--sentinel-host` `-h` `TEXT`  
  Sentinel Hostname  
  [env var: `SENTINEL_HOST`]  
  [default: `127.0.0.1`]

- `--sentinel-port` `-p` `INTEGER`  
  Sentinel Port  
  [env var: `SENTINEL_PORT`]  
  [default: `26379`]

- `--sentinel-password` `-p` `TEXT`  
  Sentinel Password  
  [env var: `SENTINEL_PASSWORD`]  
  [default: `None`]

- `--master-name` `-m` `TEXT`  
  Sentinel Master name  
  [env var: `MASTER_NAME`]  
  [default: `mymaster`]

### HAProxy Info
- `--haproxy-socket` `TEXT`  
  HAProxy admin socket address  
  [env var: `HAPROXY_SOCKET`]  
  [default: `/var/run/haproxy/haproxy.sock`]

- `--haproxy-backend` `TEXT`  
  HAProxy Backend name to control (Set it to an empty backend)  
  [env var: `HAPROXY_BACKEND`]  
  [default: `redis_master`]

- `--haproxy-server-name` `TEXT`  
  HAProxy Server name to control, It will be added and controlled through the given backend  
  [env var: `HAPROXY_SERVER_NAME`]  
  [default: `current_master`]

## In Containers

compose.yaml file is present is project root

Set/Change env vars and run it or add this project as a service to your existing setup

> You need HAProxy in a seperated Container/Server

## Why?

HAProxy is a great TCP Proxy and LoadBalancer with high performance

But It's not able be live in master changes, Using Runtime API we are able to configure that programmatically

With the help of Redis Pub/Sub we are able to understand master changes live that propagate changes to HAProxy By disconnecting all of the connections and changing server address accordingly

## TODO

* [ ] Add error handling for HAProxy commands
