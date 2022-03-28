import logging

from neo4j import GraphDatabase
from neo4j.exceptions import ServiceUnavailable


class App:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()

    def clean_database(self):
        with self.driver.session() as session:
            session.write_transaction(self._clean_database)

    @staticmethod
    def _clean_database(tx):
        try:
            return tx.run('MATCH (n) DETACH DELETE n')
        except ServiceUnavailable as exception:
            logging.error('Creating the db raised an error: \n {exception}'.format(exception=exception))
            raise

    def create_node(self, node):
        with self.driver.session() as session:
            session.write_transaction(self._create_node, node)

    @staticmethod
    def _create_node(tx, node):
        query = 'MERGE (node: `' + node.label + '` { name: $name }) RETURN node'

        result = tx.run(query, name=node.name)
        try:
            return [{'node': record['node']['name']} for record in result]
        except ServiceUnavailable as exception:
            logging.error('{query} raised an error: \n {exception}'.format(
                query=query, exception=exception))
            raise

    def create_relation(self, node1, node2, relation):
        with self.driver.session() as session:
            session.write_transaction(self._create_relation, node1, node2, relation)

    @staticmethod
    def _create_relation(tx, n1, n2, relation):
        query = 'MATCH (n1 {name: $n1_name}) ' + \
                'MATCH (n2 {name: $n2_name}) ' + \
                {
                    'subscribes': 'MERGE (n1)-[r:SUBSCRIBES] -> (n2) ',
                    'produces': 'MERGE (n1)-[r:PRODUCES] -> (n2) '
                }.get(relation, 'Invalid node label') + \
                'RETURN n1, n2'

        result = tx.run(query, n1_name=n1.name, n2_name=n2.name)
        try:
            return [{'node1': record['n1']['name'], 'node2': record['n2']['name']} for record in result]
        except ServiceUnavailable as exception:
            logging.error('{query} raised an error: \n {exception}'.format(
                query=query, exception=exception))
            raise

    def create_abstract_relation(self, node1, node2, relation):
        with self.driver.session() as session:
            session.write_transaction(self._create_abstract_relation, node1, node2, relation)

    @staticmethod
    def _create_abstract_relation(tx, node1, node2, relation):
        relation_type = ':' + relation
        query = 'MATCH (n1: `' + node1.label + '` {name: \'' + node1.name + '\'}) ' + \
                'MATCH (n2: `' + node2.label + '` {name: \'' + node2.name + '\'}) ' + \
                'MERGE (n1)-[' + relation_type + ']->(n2) ' + \
                'RETURN n1, n2'

        result = tx.run(query)
        try:
            return [{'node1': record['n1']['name'], 'node2': record['n2']['name']} for record in result]
        except ServiceUnavailable as exception:
            logging.error('{query} raised an error: \n {exception}'.format(
                query=query, exception=exception))
            raise


class Node:
    def __init__(self, name=None, label=None):
        self.name = name
        self.label = label
