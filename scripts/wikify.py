import requests
import urllib.request 
import json
import os

graphql_url = os.getenv("WIKI_GRAPHQL")
rest_url = os.getenv("WIKI_REST")
wiki_token = os.getenv("WIKI_TOKEN")
slack_token= os.getenv("SLACK_BOT_TOKEN")
wiki_url = os.getenv("WIKI_URL")

#SLACK FOLDER ID = 2

def list_folders(parent_folder_id="2"):
    headers = {'Authorization': f'Bearer {wiki_token}'}
    query = '''
    query {
      assets {
        folders (parentFolderId: '''+parent_folder_id+'''){
        id
        name
        }
      }
    }
    '''
    r = requests.post(graphql_url, json={'query': query}, headers=headers)
    return json.loads(r.text)["data"]["assets"]["folders"]
     
def create_folder(folder_name, parent_folder_id="2"):
    print(f"creating folder {folder_name}")
    headers = {'Authorization': f'Bearer {wiki_token}'}
    query = '''
    mutation {
      assets {
        createFolder(parentFolderId: '''+parent_folder_id+''', slug: "'''+folder_name+'''") {
          responseResult {
            succeeded
          }
        }
      }
    }
    '''
    r = requests.post(graphql_url, json={'query': query}, headers=headers)
    if json.loads(r.text)["data"]["assets"]["createFolder"]["responseResult"]["succeeded"] == "false":
        raise Exception(f"Failed to create folder {folder_name} in parent {parent_folder_id}")
    return 

def get_folder_id(folder_name, parent_folder_id="2"):
    folders = list_folders(parent_folder_id)
    for f in folders : 
        if f["name"] == folder_name:
            return str(f["id"])
    
    #if not found, create folder
    create_folder(folder_name, parent_folder_id)

    folders = list_folders(parent_folder_id)
    for f in folders : 
        if f["name"] == folder_name:
            return str(f["id"])
    
    raise Exception("Something went wrong fetching folder id")



def upload_asset(source_path, dest_path, filename, mimetype, parent_folder_id="2"):
    #download from source
    print(f"downloading asset {filename}")
    os.system('wget {} -O {} -d --header="Authorization: Bearer {}"'.format(source_path, filename, slack_token))
    folder_id = get_folder_id(dest_path, parent_folder_id)

    with open(filename, 'rb') as f :
        headers = {'Authorization': f'Bearer {wiki_token}'}

        files = (
            ('mediaUpload', (None, '{"folderId":'+folder_id+'}')),
            ('mediaUpload', (filename, f, mimetype))
        )
        print("uploading to wiki")
        r = requests.post(rest_url, headers=headers, files=files)
        
        if r.text != "ok":
            raise Exception("Something went wrong uploading file : "+ r.text)
            
    os.remove(filename)
    return dest_path+"/"+filename


def replies_to_md(replies, page_name, thread_id, slack_client):
    md = []
    md.append(f"# {page_name} \n ## export thread {thread_id}")

    users = {}
    for m in replies:
        user = m["user"]
        if user not in users :
            # retreive user name 
            print(f"Fetching username for {user}")
            users[user] = slack_client.users_info(user=user).data["user"]["real_name"]
        sender = users[user]
        text = m["text"]
        
        md.append(f"**{sender}** : \n {text} \n")

        # attachments
        if 'files' in m :
            for f in m["files"]:
                print(f"handling attachment {f}")
                filename = f['name']
                path = "/slack/" + upload_asset(f['url_private_download'], thread_id, filename, f["mimetype"], parent_folder_id="2")
                if f["filetype"] in ['png', 'gif', 'jpg'] :
                    md.append(f"![{filename}]({path}) \n") #include image in md
                else :
                    md.append(f"[{filename}]({path}) \n")
                
    separator = "\n --- \n"
    result = separator.join(md)
    return result


def upload_to_wiki(md, page_name, timestamp, page_path):
    query = '''
    mutation Page {
      pages {
        create(
          content: "'''+md+'''"
          description: "Slack Export : '''+timestamp+'''"
          editor: "markdown"
          isPublished: true
          isPrivate: false
          locale: "en"
          path: "'''+page_path+'''"
          tags: ["test"]
          title: "'''+page_name+'''"
        ) {
          responseResult {
            succeeded
            errorCode
            slug
            message
          }
          page {
            id
            path
            title
          }
        }
      }
    }
    '''
    r = requests.post(graphql_url, json={'query': query})
    response = json.loads(r.text)["data"]["pages"]["create"]
    if response["responseResult"]["succeeded"] == "false":
      raise Exception(f"Failed to upload markdown to wiki, error : {response['responseResult']['message']}")
    print(f"Page created {response['page']")
    
    return wiki_url+"/"+response["page"]["path"]

