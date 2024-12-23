# haproxy-redis-sentinel

<p align="center" width="100%">
    <img width="33%" src="https://raw.githubusercontent.com/ParminCloud/haproxy-redis-sentinel/master/docs/icon.png">
</p>

![Version: 0.0.20](https://img.shields.io/badge/Version-0.0.20-informational?style=flat-square) ![Type: application](https://img.shields.io/badge/Type-application-informational?style=flat-square) ![AppVersion: 0.0.10](https://img.shields.io/badge/AppVersion-0.0.10-informational?style=flat-square)

A Helm chart for HAProxy with Redis Sentinel

**Homepage:** <https://github.com/ParminCloud/haproxy-redis-sentinel>

## Compatibility

This chart can be used alongside every chart that provides access to Redis Sentinel service, For example [DandyDeveloper's redis-ha](https://github.com/DandyDeveloper/charts/tree/master/charts/redis-ha) chart

## Maintainers

| Name | Email | Url |
| ---- | ------ | --- |
| ParminCloud | <info@parmin.cloud> | <https://github.com/ParminCloud> |
| Muhammed Hussein Karimi | <info@karimi.dev> | <https://github.com/mhkarimi1383> |

## Source Code

* <https://github.com/ParminCloud/haproxy-redis-sentinel>

## Values

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| fullnameOverride | string | `""` | overrides name of the components entirely |
| haproxy.image | object | `{"pullPolicy":"IfNotPresent","repository":"docker.io/library/haproxy","tag":"bookworm"}` | HAProxy Image |
| haproxy.service.port | int | `6379` | Redis Master connection service port |
| haproxy.service.statsPort | int | `8404` | HAProxy stats port (if enabled) |
| haproxy.service.type | string | `"ClusterIP"` | Service Type |
| haproxy.stats.enabled | bool | `true` | Enables HAProxy Stats |
| haproxy.stats.metrics.enabled | bool | `true` | Enables stats metrics for HAProxy |
| haproxy.stats.metrics.serviceMonitor.enabled | bool | `false` | Enables Prometheus operator serviceMonitor to point to stats metrics |
| haproxy.stats.refresh | int | `10` | Stats refresh interval |
| haproxyRedisSentinel.image.pullPolicy | string | `"IfNotPresent"` | haproxy-redis-sentinel image pullPolicy (set to Always if you want to use branched tags) |
| haproxyRedisSentinel.image.repository | string | `"ghcr.io/parmincloud/haproxy-redis-sentinel"` | haproxy-redis-sentinel image repository |
| haproxyRedisSentinel.image.tag | string | `""` | haproxy-redis-sentinel image tag (defaults to appVersion of chart) |
| haproxyRedisSentinel.sentinel | object | `{"host":"","masterName":"mymaster","password":"","port":""}` | Redis Sentinel information |
| nameOverride | string | `""` | overrides name of the chart |
| replicaCount | int | `1` | number of replicas for deployment |

----------------------------------------------
Autogenerated from chart metadata using [helm-docs v1.13.1](https://github.com/norwoodj/helm-docs/releases/v1.13.1)
