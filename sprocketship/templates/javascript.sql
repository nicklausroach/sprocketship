CREATE OR REPLACE PROCEDURE {{database}}.{{schema}}.{{name}} (

{% for arg in args %}
"{{arg['name'].upper()}}" {{arg['type'].upper()}}{%if 'default' in arg %} DEFAULT '{{ arg['default'] }}'{% endif %}{%if not loop.last %},{% endif %}
{% endfor %}

)

{% if copy_grants %}COPY GRANTS{% endif %}

RETURNS {{returns}}

LANGUAGE JAVASCRIPT

{% if comment %}COMMENT = '{{comment}}'{% endif %}

EXECUTE AS {{execute_as}}

AS

$$

{{procedure_definition}}

$$