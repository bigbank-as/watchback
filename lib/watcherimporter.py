from elasticsearch.exceptions import NotFoundError
from elasticsearch.exceptions import RequestError
import json
import os
from deepdiff import DeepDiff


class WatcherImporter:
    WATCH_FILE_NAME = 'watch.json'

    def __init__(self, elastic, watcher_dir, logger):
        self.logger = logger
        self.watcher_dir = watcher_dir
        self.elastic = elastic

    @staticmethod
    def read_json_file(file_path):
        with open(file_path) as f:
            file_content = json.load(f)
            f.close()
        return file_content

    def read_watcher_definition(self, watcher_file):
        if not os.path.isfile(watcher_file):
            self.logger.error('Could not find watcher %s, skipping', watcher_file)
            return False

        try:
            return self.read_json_file(watcher_file)
        except ValueError:
            self.logger.error('Invalid JSON in %s, skipping', watcher_file)
            return False

    def update_elastic(self, watcher_id, watcher_definition):

        try:
            result = self.elastic.xpack.watcher.put_watch(id=watcher_id, body=watcher_definition)
        except RequestError as e:
            self.logger.exception('Unable to update Elasticsearch watcher %s: %s', watcher_id, str(e))
            return

        if result.get('created'):
            self.logger.info('Created a new watcher %s', watcher_id)
        else:
            self.logger.info('Updated watcher %s, it is now version #%d', watcher_id, result.get('_version', 1))

    def watcher_needs_updating(self, watcher_id, watcher_definition):

        """
        Determines, if a given watcher_id definition from a local file is out-of-sync with remote Elasticsearch

        :param watcher_id:
        :param watcher_definition:
        :return: True if local-remote watcher definitions are not in sync and remote needs updating
        """
        if not watcher_definition:
            return False

        try:
            watcher_response = self.elastic.xpack.watcher.get_watch(id=watcher_id)
        except NotFoundError:
            self.logger.info('Watcher %s does not exist on the remote Elasticsearch, will create it', watcher_id)
            return True

        remote_watcher = watcher_response.get('watch', {})
        diff = DeepDiff(watcher_definition, remote_watcher, ignore_order=True)

        if not diff:
            self.logger.info('Watcher %s definition is up-to-date with remote Elasticsearch, will not update it',
                             watcher_id)
            return False

        self.logger.info('Watcher %s is not up-to-date with remote Elasticsearch, it will be updated', watcher_id)
        self.logger.info('Diff between local and remote for watcher %s is as follows:', watcher_id)
        self.logger.info(diff)

        return True

    def run(self, dry_run=False):

        for watcher_id in os.listdir(self.watcher_dir):
            watcher_path = os.path.join(self.watcher_dir, watcher_id, self.WATCH_FILE_NAME)

            watcher_definition = self.read_watcher_definition(watcher_path)

            if not self.watcher_needs_updating(watcher_id, watcher_definition):
                self.logger.info('Skipping updating of watcher %s - no changes between local and remote')
                continue

            if dry_run:
                self.logger.info('Skipping Elasticsearch update (dry_run=True) for watcher %s', watcher_id)
            else:
                self.update_elastic(watcher_id, watcher_definition)
