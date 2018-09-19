# watchback

Sync Elasticsearch Watchers from local JSON files to remote Elasticsearch.

## Motivation

[Elasticsearch X-Pack Watchers][] are great - however, they exist in the "belly"
of Elasticsearch. In order to have off-band backups, version history and code
reviews for Watch definitions, it is desirable to hold them as JSON files in
VCS.

This project is a simple tool to take a bunch of Watcher definition files
and sync them to a remote Elasticsearch instance.

## Requirements

Python 3 + PIP

## Installation

```bash
git clone https://github.com/bigbank-as/watchback.git
cd watchback
pip3 install -r requirements.txt
./watchback.py --help
```

## Usage
*For --es_pass argument use - (hypen) if you want to password asked during script execution (prevents password storing in bash/used command history).*

```
$ ./watchback.py --es-ca Corporate_Root_CA.crt \
    --es-user=bruce.wayne \
    --es-pass=IAmBatman \
    --es-host=elasticsearch.waynecorp \
    --es-port=9200 \
    --watcher-dir=/home/bruce/vigilante/watchlist

2018-08-02 14:07:38,554 - root - INFO - Starting to sync Watchers from local folder /home/bruce/vigilante/watchlist to remote Elasticsearch ['elasticsearch.waynecorp']:9200
2018-08-02 14:07:38,671 - elasticsearch - INFO - GET https://elasticsearch.waynecorp:9200/ [status:200 request:0.117s]
2018-08-02 14:07:38,681 - elasticsearch - INFO - GET https://elasticsearch.waynecorp:9200/_xpack/watcher/watch/example-watch [status:200 request:0.009s]
2018-08-02 14:07:38,682 - root - INFO - Watcher example-watch is not up-to-date with remote Elasticsearch, it will be updated
2018-08-02 14:07:38,682 - root - INFO - Diff between local and remote for watcher example-watch is as follows:
2018-08-02 14:07:38,682 - root - INFO - {'dictionary_item_added': {"root['input']['search']['request']['types']", "root['actions']['my-logging-action']['logging']['level']", "root['input']['search']['request']['search_type']"}}
2018-08-02 14:07:38,707 - elasticsearch - INFO - PUT https://elasticsearch.waynecorp:9200/_xpack/watcher/watch/example-watch [status:200 request:0.024s]
2018-08-02 14:07:38,707 - root - INFO - Updated watcher example-watch, it is now version #6
2018-08-02 14:07:38,707 - root - INFO - Finished importing Watchers
```

## Watcher Folder Structure

The Watcher folder needs to follow a set structure:

- One subfolder per Watcher
- Watcher ID is the folder name (`example-watch`)
- `watch.json` in the subfolder contains the Watch definition

```
watchers
└── example-watch
    └── watch.json
```

The sub-folder is needed for mapping the Watcher ID, as well as to facilitate
additional documentation (README) and tests, per Watch.

## Versioning

This project follows [Semantic Versioning][].
Current version of the project is pre-release (`0.x`): anything can change at any time.

## License

[Apache-2.0 license](https://tldrlegal.com/license/apache-license-2.0-(apache-2.0))

[Semantic Versioning]: https://semver.org
[Elasticsearch X-Pack Watchers]: https://www.elastic.co/guide/en/elastic-stack-overview/current/xpack-alerting.html
