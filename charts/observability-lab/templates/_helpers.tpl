{{- define "observability.name" -}}
{{- printf "%s-%s" .Release.Name .component | lower | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{- define "observability.labels" -}}
app.kubernetes.io/name: {{ .Chart.Name }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
app.kubernetes.io/component: {{ .component }}
{{- end -}}

{{- define "observability.selectorLabels" -}}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/component: {{ .component }}
{{- end -}}
