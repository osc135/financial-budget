{{- define "financial-budget.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{- define "financial-budget.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- if contains $name .Release.Name }}
{{- .Release.Name | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}
{{- end }}

{{- define "financial-budget.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{- define "financial-budget.labels" -}}
helm.sh/chart: {{ include "financial-budget.chart" . }}
{{ include "financial-budget.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{- define "financial-budget.selectorLabels" -}}
app.kubernetes.io/name: {{ include "financial-budget.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{- define "financial-budget.postgresql.host" -}}
{{- if .Values.database.embedded.enabled }}
{{- printf "%s-postgresql" (include "financial-budget.fullname" .) }}
{{- else }}
{{- .Values.database.external.host }}
{{- end }}
{{- end }}

{{- define "financial-budget.database.url" -}}
{{- if .Values.database.embedded.enabled }}
{{- printf "postgresql://%s:%s@%s:5432/%s" .Values.postgresql.auth.username .Values.postgresql.auth.password (include "financial-budget.postgresql.host" .) .Values.postgresql.auth.database }}
{{- else }}
{{- printf "postgresql://%s:%s@%s:%s/%s" .Values.database.external.username .Values.database.external.password .Values.database.external.host (.Values.database.external.port | toString) .Values.database.external.database }}
{{- end }}
{{- end }}
