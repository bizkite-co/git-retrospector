PAYLOAD='{"repo_owner":"bizkite-co","repo_name":"urllog","repo_url":"https://github.com/bizkite-co/urllog.git","iterations":1}'

aws lambda invoke \
    --function-name RetrospectorInfraStack-InitiationLambdaD92993FC-19qCXWAawQNL \
    --cli-binary-format raw-in-base64-out \
    --payload "$PAYLOAD" \
    response.json
