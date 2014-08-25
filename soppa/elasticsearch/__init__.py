import os

from soppa.contrib import *

class ElasticSearch(Soppa):
    url='https://download.elasticsearch.org/elasticsearch/elasticsearch/elasticsearch-1.1.1.tar.gz'
    servername='elasticsearch.dev'
    needs = ['soppa.supervisor',
            'soppa.nginx',
            'soppa.package',]

    def setup():
        self.package.file_as_release(self.url)
        self.action('up', 'elasticsearch_supervisor.conf', '{supervisor.conf_dir}', handler=['supervisor.restart'])
        self.action('up', 'elasticsearch_nginx.conf', '{nginx.dir}conf/sites-enabled/', handler=['nginx.restart'])

    def health():
        # http://www.elasticsearch.org/guide/en/elasticsearch/reference/current/_cluster_health.html
        f=1
        #/_cat/health?v
