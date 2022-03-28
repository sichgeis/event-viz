# event-viz

This project demonstrates how to visualize the event flow within a fictional system landscape.

This project also contains scripts that perform a static code analysis on the host machine and fill a graph database with the 
found events, producers, subscribers and their relationship. 
These scripts are very specific to the system landscape that event-viz was originally created for.
They are published here as a possible starting point for your own adaptions.

The event graph can be visualized and inspected with the bundled browser.
A database dump of the most recent scan is also checked into this git repository.
This should allow a quick startup of the graph-browser.
There is no need to utilize the static code analysis script if you just want to inspect the event flow.


## Run the graph-browser to inspect event-flow

1. Git checkout the project
2. Run `./start-neo4j.sh` in the `src` directory. Make sure that the docker deamon is running.
3. Connect to `http://localhost:7474/` and login with these credentials:
    * **user:** `neo4j`
    * **pass:** `test`
4. Run queries like eg:
    * `match (n) return n`
    * `match (n) -[:PurchaseReceived]->(m) return n,m`
    * `match (n {name: 'shop'}) match (m {name: 'peero-consumer'}) return n, m`
    * `match (n {name: 'offer'})-[r]->(u) where u.name <> 'offer' return n,r,u`

* A double click on the node expands and collapses child relationships.
* A cheat sheet for the query language `cypher` can be found here: [reference card](https://neo4j.com/docs/cypher-refcard/current/).

## Update graph database with dummy data for testing

#### Setup
1. Check out every project that may be connected to the event bus (eg. Kinesis).
2. `cd` into the `src` dirctory
3. Create a virtual python environment with:
   * `virtualenv venv`
   * `source venv/bin/activate`
4. Install project dependencies into you virtual environment:
   * `pip install -r requirements.txt`
   
#### Add dummy data
1. Check the script `polpulate_db_with_dummy_data.py` and change the hard coded lists and dictionaries to your liking.
2. Start the neo4j docker container as described above.
3. Run `polpulate_db_with_dummy_data.py`.
4. Inspect the data with the neo4j browser as described above.

## Current state

Currently it is possible to find events in the Java and Terraform codebase on a local machine. 
Events are found from typical method signatures of handlers.
eg:
```
    public void handle(final PurchaseReceived purchase) {
    
    protected void processEvent(SomeOtherEvent event) {
```
The found events are then output to the `events.dat` file for manual inspection. This file is check in the git repo
for fail safe checks. If you run the crawler and find less events as stated in the events.dat, something might be wrong.

In a second step the code base is searched for any method signatures which includes the found event type.
If such a method is found, then that class is assumed to be a subscriber.
The relation between this subscriber and the event is `subscribes`.

In a third scan the code base is searched for calls to the constructor of known events.
If a class calls an event constructor, then that class is assumed to be a producer.
The relation between this producer and the event is `produces`.

Events, subscribers and producers are saved to a neo4j graph database that is running in a docker container.
The graph database can be inspected with the bundled neo4j browser web application.
 

### How to run static code analysis

#### Setup
1. Check out every project that may be connected to the event bus (eg. Kinesis).
2. `cd` into the `src` dirctory
3. Create a virtual python environment with:
    * `virtualenv venv`
    * `source venv/bin/activate`
4. Install project dependencies into you virtual environment:
    * `pip install -r requirements.txt`

#### Run it
1. Adapt the search_root_directory  parameter  within `analyse_code_and_find_events.py` and then run the script. 
This should produce the `events.dat` file.
You can add events to a blacklist to exclude them from the search.
Or you can use the whitelist to explicitly add events that were not found properly.
2. Start the neo4j docker container as described above.
3. Adapt the search_root_directory and "get_project" file split number to match your file tree within `events_as_edges_proto.py` and run it.
This should first remove all nodes and relations from the database.
Then it performes the static code analysis and populates the database.
4. Inspect the data with the neo4j browser as described above.
5. If you like this data, change the host_name to the current ip of your production neo4j graph-db and rerun the `events_as_edges_proto.py` or `analyse_code_and_insert_into_db.py` to update the database
