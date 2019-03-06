# Installation instructions
To set up ELK quickly, install docker (`apt install docker.io`) and then get the docker compose file:
`sudo git clone https://github.com/deviantony/docker-elk`

Then `cd docker-elk` and then do `docker-compose up -d`

Please note that ELK is set up to listen on all interfaces so you will need a firewall to protect the host!

Then install this script and have it run every 5 mins:

`*/5 * * * *    /usr/bin/python3 /home/rcompton/bin/ddos_info_to_elastic.py  -k <key> -u <username> -m 1445 -l 0`

If you want to do map visualizations in Kibana, then under Kibana's Dev Tools console paste in this to make the 'location' field a geo_point:

`PUT /dis_info
{
    "mappings": {
        "json": {
            "properties": {
                "location": {
                    "type": "geo_point"
                }
            }
        }
    }
}`
