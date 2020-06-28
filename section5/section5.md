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
    
    