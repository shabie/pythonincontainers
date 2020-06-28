# Section 5

1. Docker Swarm and Kubernetes both can run reasonably sized containerized applications. However, they have very
different philosophies. Docker comes from a developer point of view. Kubernetes from an operations viewpoint.

2. Generally speaking a multi-container application can be said follow this equation:

    Containerized application = Services + Networks + Volumes

3. **Docker Compose** introduction: It is a wrapper tool around docker to simplify the startup of multi-container
applications.
    
    It is a YAML file with the following basic format:
    
    ```yaml
    # Every docker-compose YAML file starts with declaration of docker-compose "language" version we are using.
    # YAML doesn't need quotes normally for strings but for those that will be misinterpreted as float, we must use them.
    version: "3.7"

    # Services section declares Containers running Application Components
    services:
    # Database Service
      db:
        ...

    # Application Logic Service
      app:
        ...

    # Proxy Service
      proxy:
        ...

    # Networks section declares Virtual Networks for Application Components
    networks:
      net1:
      net2:

    # Volumes section declares Persistent Volumes used by Application Components
    volumes:
      vol1:
      vol2
    ```
    
    * Services are Docker Containers
    * Networks are Docker Networks
    * Volumes are Docker Volumes

    There are some other options like Config and Secrets that are used only with Docker Swarm and are ignored
    if called with Docker Compose.
    
4. Let's look at a concrete example of Docker Compose:

    ```yaml
    version: "3.7"

    # Network to used for Application Components Service Discovery and communication
    networks:
      polls_net:

    # Persistent Volume to hold Database data files
    volumes:
      polls_vol:

    # Services representing Application Components
    services:
    # Postgres Database Engine
      db:
        image: postgres:11.3
        networks:
          - polls_net
        volumes:
          - polls_vol:/var/lib/postgresql/data
        environment:
          - POSTGRES_USER=pollsuser
          - POSTGRES_PASSWORD=pollspass
          - POSTGRES_DB=pollsdb

    # Django Polls Application Server
      app1:
        image: pythonincontainers/django-polls:nginx
        networks:
          - polls_net
        environment:
          - DATABASE_URL=postgres://pollsuser:pollspass@db/pollsdb
        depends_on:
          - db

    # Proxy Server
      proxy:
        image: pythonincontainers/mynginx:latest
        networks:
          - polls_net
        ports:
          - "8000:8000"
        depends_on:
          - app1
    ```
   
    The one thing to understand is the meaning of `depends_on`. It simply means that this container is to be started
    after the container mentioned in `depends_on`. It doesn't wait for the container to be properly up and running as
    this is outside the capabilities of docker-compose.
    
    Here's how the file can be used:
    
    `docker-compose up -d` where `-d` flag means that launch all containers in background. The file is first checked
    for correctness. Then it identifies what objects to create and in which order:
    
    ![docker compose terminal output](staticfiles/docker-compose.svg)
     
    The started containers/networks/volumes all have the prefix `compose-intro_` and a suffix `_1` (suffix is only for 
    the containers) to allow running several parallel applications (i.e. multi-container apps) from the same 
    docker-compose file.
    
    The database has not been initialized so when we try to access the app, we receive an error (status code 500):
    
    ```shell
    shabie:~$ curl -IL localhost:8000
    HTTP/1.1 302 Found
    Server: nginx/1.17.0
    Date: Sun, 28 Jun 2020 08:59:19 GMT
    Content-Type: text/html; charset=utf-8
    Content-Length: 0
    Connection: keep-alive
    Location: /polls/
    X-Frame-Options: SAMEORIGIN

    HTTP/1.1 500 Internal Server Error
    Server: nginx/1.17.0
    Date: Sun, 28 Jun 2020 08:59:19 GMT
    Content-Type: text/html; charset=utf-8
    Content-Length: 144842
    Connection: keep-alive
    X-Frame-Options: SAMEORIGIN
    Vary: Cookie
    ```
   
    Q. **Can we write the initialization commands in docker compose**?
    
    No. Because docker compose file is declarative in nature. It is not imperative i.e. it doesn't allow sequential
    listing and execution of commands. This will be covered later.
    
    So for now we can initialize them manually using these commands:
    
        * `docker-compose exec app1 python manage.py migrate`
        * `docker-compose exec app1 python manage.py createsuperuser`
        * `docker-compose exec app1 python manage.py loaddata initial_data.json`
       
    Interestingly, the container even though from the outside called `compose-intro_app1_1`, gets its name translated
    into the short-name `app1` so the commands above work well. Even from inside the containers, the other components
    are referred to using the short-name only. So for example from `app1` we can ping `db` directly using `db` and not
    using `compose-intro_db_1`.
    
    The whole application can also be brought down **gracefully** using the docker-compose if we are in the same folder
    used to bring them up (i.e. folder containing the docker-compose.yml file). Graceful shutdown is important specially
    for database engines.
    
    Output for command **`docker-compose down`** looks like this:
    
    ```shell
    shabie:~$ docker-compose down
    Stopping compose-intro_proxy_1 ... done
    Stopping compose-intro_app1_1  ... done
    Stopping compose-intro_db_1    ... done
    Removing compose-intro_proxy_1 ... done
    Removing compose-intro_app1_1  ... done
    Removing compose-intro_db_1    ... done
    Removing network compose-intro_polls_net
    ```
    
    Very logically the persistent volume `compose-intro_polls_vol` has NOT been removed. If we start the application
    again using `docker-compose up -d` the volume will not be recreated but rather the current one will be re-used.
    
    If we really do want it to remove the volumes as well, we can add the `-v` option which stands for the `--volumes`
    flag.
    
5. Docker Compose file is normally named `docker-compose.yaml` or `docker-compose.yml`. Both extensions work.

    We can always use the `-f` flag (just like for Docker build) to pass any non-default docker compose filenames.
    
6. Docker Compose file structure (focus on volumes and versions):

    1. Uses YAML syntax
    
    2. Can contain up-to 4 key-value mappings with the keys being as follows:
        1. `version: ...`
        2. `services: ...`
        3. `networks: ...`
        4. `volumes: ...`
    
    3. Version value must be a string (!!str is YAML type casting): `version: "3.7"` or `version: !!str 3.7`. If there
    are multiple entries, only the last one is taken into account.
    
    4. A config file can be validated with this cmd: `docker-compose -f last_one_survives.yml config`
    
    5. Docker compose creates volumes before the services. It checks if any declared volumes have already been created.
    If they are, they are simply mounted. If not, they are created. Declaration of volume looks like this:
        
    ```yaml
    volumes:
      my_vol:
    ```

    The declaration above is equivalent to: `docker volume create my_vol`. The default driver (can be seen with 
    `docker info`) is used. However, you may want to create volumes elsewhere i.e. other than your own host machine
    specially (which is the factory default at least) for the production environments. Then the plugins can be used. 
    
    Here's one example of using the netapp plugin driver:

    ```yaml
    volumes:
      my_vol:
        driver: netapp
    ```
    
    List of supported plugs can be found **[here](https://docs.docker.com/engine/extend/legacy_plugins/)**
    
    Volumes that are already created and should only be used are available in 2 ways:
    
        1. We already have the volume with the same name that will be created like `compose-file_my_vol`. I mean for
        this we would have in the compose file only written `my_vol` and the name conversion happens automatically.
        
        2. We use the `external` flag. Consider the example below:
        
        ```yaml
        version: "3.7"
        volumes:
          int:
          ext:
            external:
              name: my_vol
        ```
        
        In the example above, two volumes are declared. One called `int` will be created with the name `compose-file_int`
        and the other one will be accessible by the name `ext` uses however an already defined volume called `my_vol`.
        
        **Doing a `docker-compose down -v` will not remove the external one since, well, it is external.**
           
    6. One volume can be shared by several services (containers) declared in Docker Compose file, if they explicitly
    mount it. Here's an example of one volume being mounted twice:
    
    ```yaml
    version: "3.7"

    volumes:
      shared_vol:

    services:
      proxy1:
        image: nginx:1.17.0
        volumes:
          - shared_vol:/static

      proxy2:
        image: nginx:1.17.0
        volumes:
          - shared_vol:/static
    ```
    
    There is locking or sync mechanism between the containers using the shared volume which means the application must
    implement the coordinated data access (I guess it makes sense to just read files like static from such shared
    volumes).
    
    To execute a command on the service containers above (say to see contents of static folder) we can do the following:
    
    **`docker-compose -f shared_volume.yml exec proxy2 l -al /static`**
    
7. Docker Compose file structure (Networks):

    
    