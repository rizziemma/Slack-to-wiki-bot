# Slack to WikiJS bot WIP

Bot to export slack threads to WikiJS pages

References :
- https://github.com/HackSoftware/EuroPython-2021-Training/blob/master/main.py
- https://github.com/slackapi/python-slack-events-api


## Deploy

```
docker build -t $IMAGE -f Dockerfile 
    --build-arg WIKI_TOKEN=$WIKI_TOKEN 
    --build-arg SLACK_BOT_TOKEN=$SLACK_BOT_TOKEN 
    --build-arg SLACK_SIGNING_SECRET=$SLACK_SIGNING_SECRET 
    . 
docker push $IMAGE
```

``` 
docker run -d --name=ouistibot --restart=always -p $PORT $IMAGE
```

# WikiJS config
needs an assests folder dedicated to slack exports : `parent_folder_id`

## Slack config 
Create app, slack bot token, configure command /wikify

## Usage

`/wikify <Page name>`