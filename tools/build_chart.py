from pathlib import Path
root=Path(__file__).resolve().parents[1]
chart=root/'charts/observability-lab'
components={
'nginx':('nginx:1.27-alpine',80,'/health',True),
'nginxExporter':('nginx/nginx-prometheus-exporter:1.4.2',9113,'/metrics',True),
'blackboxExporter':('prom/blackbox-exporter:v0.25.0',9115,'/metrics',True),
'prometheus':('prom/prometheus:v2.55.1',9090,'/-/healthy',True),
'alertmanager':('prom/alertmanager:v0.27.0',9093,'/-/healthy',False),
'grafana':('grafana/grafana:11.3.0',3000,'/api/health',False),
'loki':('grafana/loki:3.2.0',3100,'/ready',False),
'promtail':('grafana/promtail:3.2.0',9080,'/ready',False),
'tempo':('grafana/tempo:2.6.0',3200,'/ready',False),
'otelCollector':('otel/opentelemetry-collector:0.113.0',8888,'/metrics',False),
'nodeExporter':('prom/node-exporter:v1.8.2',9100,'/metrics',False),
'kubeStateMetrics':('registry.k8s.io/kube-state-metrics/kube-state-metrics:v2.14.0',8080,'/metrics',False),
'cadvisor':('gcr.io/cadvisor/cadvisor:v0.49.1',8080,'/metrics',False),
'postgresExporter':('prometheuscommunity/postgres-exporter:v0.16.0',9187,'/metrics',False),
'redisExporter':('oliver006/redis_exporter:v1.66.0',9121,'/metrics',False),
'processExporter':('ncabatoff/process-exporter:0.8.4',9256,'/metrics',False),
'pushgateway':('prom/pushgateway:v1.10.0',9091,'/metrics',False),
'statsdExporter':('prom/statsd-exporter:v0.27.1',9102,'/metrics',False),
}
values='''global:
  imagePullPolicy: IfNotPresent
  podSecurityContext:
    runAsNonRoot: false
  annotations: {}
  labels: {}

components:
'''
for name,(image,port,path,enabled) in components.items():
    values+=f'''  {name}:
    enabled: {str(enabled).lower()}
    image: {image}
    replicas: 1
    port: {port}
    probePath: {path}
    args: []
    env: []
    config: ""
    configKey: config.yml
    configMountPath: /etc/observability/config.yml
    serviceType: ClusterIP
    resources:
      requests:
        cpu: 25m
        memory: 64Mi
      limits:
        cpu: 500m
        memory: 512Mi
    podAnnotations: {{}}
    podLabels: {{}}
    nodeSelector: {{}}
    tolerations: []
    affinity: {{}}
    podDisruptionBudget:
      enabled: false
      minAvailable: 1
    networkPolicy:
      enabled: false
'''
values+='''
# Core component arguments and configuration.
'''
values+='''
'''
(chart/'values.yaml').write_text(values)
for name,(image,port,path,enabled) in components.items():
    context=f'{{{{- $ctx := dict "Release" .Release "Chart" .Chart "component" "{name}" -}}}}'
    template=f'''{{{{- if .Values.components.{name}.enabled }}}}
{context}
{{{{- $component := .Values.components.{name} -}}}}
apiVersion: v1
kind: ServiceAccount
metadata:
  name: {{{{ include "observability.name" $ctx }}}}
  labels:
    {{{{- include "observability.labels" $ctx | nindent 4 }}}}
automountServiceAccountToken: false
---
apiVersion: v1
kind: ConfigMap
metadata:
  name: {{{{ include "observability.name" $ctx }}}}-config
  labels:
    {{{{- include "observability.labels" $ctx | nindent 4 }}}}
data:
  {{{{ $component.configKey }}}}: |
{{{{ $component.config | indent 4 }}}}
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{{{ include "observability.name" $ctx }}}}
  labels:
    {{{{- include "observability.labels" $ctx | nindent 4 }}}}
spec:
  replicas: {{{{ $component.replicas }}}}
  revisionHistoryLimit: 3
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
  selector:
    matchLabels:
      {{{{- include "observability.selectorLabels" $ctx | nindent 6 }}}}
  template:
    metadata:
      labels:
        {{{{- include "observability.selectorLabels" $ctx | nindent 8 }}}}
        {{{{- with $component.podLabels }}}}
        {{{{- toYaml . | nindent 8 }}}}
        {{{{- end }}}}
      annotations:
        checksum/config: {{{{ $component.config | sha256sum }}}}
        {{{{- with $component.podAnnotations }}}}
        {{{{- toYaml . | nindent 8 }}}}
        {{{{- end }}}}
    spec:
      serviceAccountName: {{{{ include "observability.name" $ctx }}}}
      automountServiceAccountToken: false
      terminationGracePeriodSeconds: 30
      imagePullSecrets: []
      nodeSelector:
        {{{{- toYaml $component.nodeSelector | nindent 8 }}}}
      tolerations:
        {{{{- toYaml $component.tolerations | nindent 8 }}}}
      affinity:
        {{{{- toYaml $component.affinity | nindent 8 }}}}
      containers:
        - name: {name}
          image: {{{{ $component.image | quote }}}}
          imagePullPolicy: {{{{ $.Values.global.imagePullPolicy }}}}
          {{{{- with $component.args }}}}
          args:
            {{{{- toYaml . | nindent 12 }}}}
          {{{{- end }}}}
          {{{{- with $component.env }}}}
          env:
            {{{{- toYaml . | nindent 12 }}}}
          {{{{- end }}}}
          ports:
            - name: http
              containerPort: {{{{ $component.port }}}}
              protocol: TCP
          readinessProbe:
            httpGet:
              path: {{{{ $component.probePath }}}}
              port: http
            periodSeconds: 10
            timeoutSeconds: 3
            failureThreshold: 3
          livenessProbe:
            httpGet:
              path: {{{{ $component.probePath }}}}
              port: http
            periodSeconds: 20
            timeoutSeconds: 3
            failureThreshold: 5
          startupProbe:
            httpGet:
              path: {{{{ $component.probePath }}}}
              port: http
            periodSeconds: 5
            failureThreshold: 12
          resources:
            {{{{- toYaml $component.resources | nindent 12 }}}}
          volumeMounts:
            - name: config
              mountPath: {{{{ $component.configMountPath }}}}
              subPath: {{{{ $component.configKey }}}}
              readOnly: true
      volumes:
        - name: config
          configMap:
            name: {{{{ include "observability.name" $ctx }}}}-config
---
apiVersion: v1
kind: Service
metadata:
  name: {{{{ include "observability.name" $ctx }}}}
  labels:
    {{{{- include "observability.labels" $ctx | nindent 4 }}}}
spec:
  type: {{{{ $component.serviceType }}}}
  selector:
    {{{{- include "observability.selectorLabels" $ctx | nindent 4 }}}}
  ports:
    - name: http
      port: {{{{ $component.port }}}}
      targetPort: http
      protocol: TCP
{{{{- if $component.podDisruptionBudget.enabled }}}}
---
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata:
  name: {{{{ include "observability.name" $ctx }}}}
  labels:
    {{{{- include "observability.labels" $ctx | nindent 4 }}}}
spec:
  minAvailable: {{{{ $component.podDisruptionBudget.minAvailable }}}}
  selector:
    matchLabels:
      {{{{- include "observability.selectorLabels" $ctx | nindent 6 }}}}
{{{{- end }}}}
{{{{- if $component.networkPolicy.enabled }}}}
---
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: {{{{ include "observability.name" $ctx }}}}
  labels:
    {{{{- include "observability.labels" $ctx | nindent 4 }}}}
spec:
  podSelector:
    matchLabels:
      {{{{- include "observability.selectorLabels" $ctx | nindent 6 }}}}
  policyTypes:
    - Ingress
    - Egress
  ingress:
    - from:
        - podSelector: {{}}
      ports:
        - protocol: TCP
          port: {{{{ $component.port }}}}
  egress:
    - to:
        - podSelector: {{}}
{{{{- end }}}}
{{{{- end }}}}
'''
    (chart/'templates'/f'{name}.yaml').write_text(template)
# Small override files for different cluster sizes.
for env,replicas,cpu,memory in [('development',1,'25m','64Mi'),('staging',2,'50m','128Mi'),('production',3,'100m','256Mi')]:
    text=f'''global:
  imagePullPolicy: IfNotPresent
components:
'''
    for name in components:
        text+=f'''  {name}:
    replicas: {replicas if name in ('nginx','prometheus') else 1}
    resources:
      requests:
        cpu: {cpu}
        memory: {memory}
      limits:
        cpu: 1000m
        memory: 1Gi
    podDisruptionBudget:
      enabled: {str(replicas>1 and name in ('nginx','prometheus')).lower()}
      minAvailable: 1
'''
    (chart/f'values-{env}.yaml').write_text(text)
print('Generated',len(components),'component templates')
