CREATE OR REPLACE PROCEDURE {{database}}.{{schema}}.{{name}} (
{%- for arg_name, arg_data_type in args.items() %}
"{{arg_name.upper()}}" {{arg_data_type.upper()}}{%if not loop.last %},{% endif %}
{%- endfor -%}
)
{% if copy_grants %}COPY GRANTS{% endif %}
RETURNS {{returns}}
LANGUAGE JAVASCRIPT
{% if comment %}COMMENT = '{{comment}}'{% endif %}
EXECUTE AS {{execute_as}}
AS '{{procedure_definition}}' 