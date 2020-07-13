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
    # YAML doesn't need quotes for strings but for those that will be misinterpreted as float, we must use them.
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

    1. Networks in the YAML file can be declared as follow:
    
    ```yaml
    networks:
      my_net:
    ```

    This is equivalent to: `docker network create my_net`
    
    2. Network is created using the default driver which is bridge. This network can make the containers connected to
    it reachable to the internet through the host's network interface. Moreover, the network allows DNS name resolution
    (i.e. a DNS service) based on the container name. Pretty standard docker stuff.
    
    3. It is possible to declare more than one network in a docker compose file:
    
    ```yaml
    version: "3.7"

    networks:
      net1:
      net2:

    services:
      one:
        image: alpine
        command: ["tail", "-f", "/dev/null"]
        networks:
          - net1

      two:
        image: alpine
        command: ["tail", "-f", "/dev/null"]
        networks:
          - net2
    ```
    
    As can be seen above, two service containers attached to their own networks. Both services can access the internet
    i.e. have access to the external world yet being on their own networks can't see each other. This helps in creating
    application components with segregation of traffic.
    
    Here's another example where some services only have access to internal (virtual) networks while others to both.
    This allows easy setup of sophisticated network setups:
    
    ```yaml
    version: "3.7"

    networks:
    frontend:
    backend:
      internal: true

    services:
    web:
      image: alpine
      command: ["tail", "-f", "/dev/null"]
      ports:
        - "8080:80"
      networks:
        - frontend

    app:
      image: alpine
      command: ["tail", "-f", "/dev/null"]
      networks:
        - frontend
        - backend

    db:
      image: alpine
      command: ["tail", "-f", "/dev/null"]
      networks:
        - backend
    ```
   
    Note: Command `tail -f /dev/null` is simply a never ending command.
   
    4. If no network is indicated for a service, Docker Compose creates a default one and attaches the services to it.
    
    5. Docker Compose, as with volumes, can also make use of external networks too. In the example below, the default
    itself is overridden:
    
    ```yaml
    version: "3.7"

    networks:
      default:
        external:
          name: my_net

    services:
      web:
        image: alpine
        command: ["tail", "-f", "/dev/null"]
      app:
        image: alpine
        command: ["tail", "-f", "/dev/null"]
    ```
    
    6. Docker Compose takes into account the folder name also if the docker compose file is within the folder. This
    allows firing up different configs simultaneously and still avoiding namespace conflicts.
    
    7. Since each container service gets its own IPv4 address, the default capacity is for 256 containers. This can
    however be changed as in the example below (allows 65k containers) since we are setting **16** bit address range
    rather than **8** bit (2^8 == 256  and 2^16 == 65536). IPAM stands for IP Address Management:
    
    ```yaml
    version: "3.7"

    networks:
      big_net:
        ipam:
          driver: default
          config:
            - subnet: 10.1.0.0/16

    services:
      web:
        image: alpine
        command: ["tail", "-f", "/dev/null"]
        networks:
          - big_net
    ```

8. The full list of options available under the `services` key has over 40 options:

    ```yaml
    version: “3.7”
    services:
      my_service: # name of the service
        
        # Container Name options:
        container_name: …  # specific container name. If not provided service name is taken as default.
        hostname: …
        domainname: …
        
        # Image related options:
        image: …
        build: …
        
        # Start-up Command options:
        entrypoint: …
        command: …
        
        # Volumes related options:
        volumes: …
        tmpfs: …
        
        # Network related options:
        networks: …
        ports: …
        network_mode: …
        dns: …
        dns_search: …
        extra_hosts: …
        expose: …
        
        # Environment options:
        environment: …
        env_file: …
        working_dir: …
        user: …
        devices: …
        stdin_open: …
        tty: …
        
        # Control options:
        privileged: …
        depends_on: …
        restart: …
        stop_signal: …
        stop_grace_period: …
        logging: …
        
        # Container linking options:
        links: …  # I think this is deprecated now - Shabie
        external_links: …
        
        # Labels options:
        labels: …
        
        # Other options
        cap_add: …
        cap_drop: …
        security_opt: …
        cgroup_parent: ...
        init: …
        pid: …
        sysctls: …
        ulimits: …
        userns_mode: …
        ipc: …
        shm_size: …
    ```
    
    1. So the `image` tag is the most obvious one. Docker compose has no way to pass private registry login credentials
    so any private image will can only be accessed if `docker login` has been done beforehand.
    
    2. Docker compose can also build the image! The option used is `build:` together with `ìmage:`. Although building
    them may not be such a good idea.
    
    3. `container_name` if defined is how the service becomes accessible.
    
    4. `hostname` is the hostname (by default the container name). Can be checked using `hostname --short` in container
    bash.
    
    5. `domainname` defines the domain on which it is defined. `hostname`.`domainname` is what you get if you do
    `hostname --long` in bash in such a container.
    
    6. `entrypoint` and `command` don't need special intro. Here are two forms (Exec and Shell) in YAML format:
    
    ```yaml
    version: "3.7"

    services:
      app1:
        image: pythonincontainers/django-polls:nginx
        entrypoint: ["python", "manage.py"]
        command:
          - runserver
          - "0:8000"
      app2:
        image: pythonincontainers/django-polls:nginx
        command: uwsgi uwsgi.ini
    ```
   
    7. Volumes can be defined in services in **2 ways** i.e. the short and the long-form.
    
    Examples of **short form**:
    
    ```yaml
    version: "3.7"
    volumes:
      my_vol:

    services:
      app1:
        image: alpine
        command: ["tail", "-f", "/dev/null"]
        volumes:
          - "my_vol:/data"
          - "/anon"
          - "./volumes.yml:/files/config.yml"
          - "./external_net1:/files/external_net1:ro"
    ```
    
    So one persistent volume has been defined called `my_vol`. Under the `volumes` option of `services`, the 4 options
    can be understood as follow:
        
        * First one is a mount of the persistent volume onto the `/data` folder. If the folder is not available in the
        container, it is created.
        * Second one is a mountpoint and Docker Compose binds an anonymous volume that will get removed with the
        container.
        * The 3rd option bind-mounts a file
        * The 4th option bind-mounts a file but only with the **read-only** option.
        
    Examples of the **long form**:
    
    ```yaml
    version: "3.7"
    volumes:
      db_vol:

    services:
      app2:
        image: postgres:11.3
        volumes:
          - type: volume
            source: db_vol
            target: /var/lib/postgresql/data
            volume:
              nocopy: true
          - type: bind
            source: ./
            target: /app/examples
            read_only: true
          - type: tmpfs
            target: /scratch1
            tmpfs:
              size: 100m
        tmpfs:
          - /scratch2
    ```
   
    There is one persistent volume defined called `db_vol`. There are a total of 4 volume mounts happening in app2 in
    total:
    
        * First one is the persistent volume mount of volume `db_vol` on the mount point `/var/lib/postgresql/data` in
        the container. A sub-option `no-copy: true` means don't copy files from the container's mountpoint onto the 
        mounted volume at the time of volume creation. By default it is false. See the StackOverflow answer 
        [here](https://stackoverflow.com/a/38288382/7996306).
        * Second one is the bind mount of root folder (i.e. where docker compose yaml is located) to the target and
        set the option read-only to true. By default read-only is false.
        * Third is the `tmpfs` which stands for temporary file-system. It is in-memory storage. Fast indeed but not
        persistent. Size limit set to 100 MB.
        * Fourth option shows how `tmpfs` can be directly used as an option instead of it being under the `volumes:`
        option of the service.
        
    8. The entire range of network options are covered in the YAML below. Comments added for clarity:
    
    ```yaml
    version: "3.7"

    # two networks have been declared
    networks:
      my_net:   # one of them is a "regular" one (with 8-bit subnet mask)
      big_net:  # this one is more customized and uses 16 bit subnet mask
        ipam:
          driver: default
          config:
            - subnet: 10.1.0.0/16

    services:
      app1:
        image: alpine
        command: ["tail", "-f", "/dev/null"]
        networks:
          big_net:  # connected to big_net
            ipv4_address: 10.1.23.45  # an IPv4 address explicitly dedicated to it
          my_net:   # connected to my_net. IPv4 here case will be given by docker engine. So this service will have 2 IPs.
        ports:
          - 8080:80       # port mapping
          - 8443:443/tcp  # port mapping with protocol
        extra_hosts:
          - "secret-host:192.168.1.179"  # adds this to the /etc/hosts for hostnames not resolvable with Docker's DNS service

      db:
        image: postgres:11.3
        networks:
          big_net:    # connected to big_net
            aliases:  # alias simply means the service container is accessible by multiple names
              - postgres  
              - db_server
            ipv4_address: 10.1.0.10   # gets a dedicated IPv4
        expose:
          - 5432  # analogous to EXPOSE in dockerfile
        dns:
          # both IPs below are Google's DNS servers. How they work? Watch [this](www.youtube.com/watch?v=mpQZVYPuDGU)
          - 8.8.8.8  # this is handy if we want to explicitly want the service to lookup in specific DNS servers... This
          - 8.8.4.4  # of course applies to external addresses bec. among containers, docker's own DNS service works.
        environment:
          - POSTGRES_USER=pguser
          - POSTGRES_PASSWORD=pgpass
          - POSTGRES_DB=pgdb

      monitor:
        image: alpine
        command: ["tail", "-f", "/dev/null"]
        network_mode: "service:db"  # this one gets the complete network stack of db including the same IP address!

      controller:
        image: alpine
        command: ["tail", "-f", "/dev/null"]
        network_mode: host  # this one gets the complete network stack of the host (VERY DANGEROUS OPTION)
    ```
   
    9. Environment variables can be set directly or through a file:
    
    ```yaml
    services:
      flask_app:
        image: pythonincontainers/flask-hello
        ports:
          - 5000:5000
        command: ["flask", "run"]
        environment:
          - "FLASK_APP=hello-flask"
          - "FLASK_RUN_HOST=0.0.0.0"
          - "FLASK_RUN_PORT=5000"
          - "FLASK_DEBUG=true"
          - "FLASK_ENV"

      postgres:
        image: postgres:11.3
        env_file:
          - postgres.env
    ```

9. Docker object names can be broken down into:

    Project Name + Service Name where Project Name is folder name by default (i.e. many examples have `compose-file`
    because it is the folder name of the project).
    
10. Docker-compose can be used to build images too. Not ideally done in production where time is critical since you
want images to fire up as soon as possible.

11. Here's an example of Docker-Compose being used for building images:

    ```yaml
    # test-build.yaml
    version: "3.7"

    services:
      full:
        image: shabie/flask-hello:3.7.3
        ports:
          - 5001:5000
            build:                              # is ignored if image exists in cache. To force add --build after "up"
          context: ./simple-flask               # path used as context. Can be absolute or relative to compose file loc.
          dockerfile: Dockerfile-universal      # Dockerfile within the context. If standard name, this can be skipped.
          args:
            - ImageTag=3.7.3                    # argument to pass to Dockerfile
          labels:
            com.pythoninconrainers.app: simple-flask   # labels. If skipped you get <foldername><servicename>:latest
            com.pythoninconrainers.image.base: full

      slim:
        image: shabie/flask-hello:3.7.3-slim
        ports:
          - 5002:5000
        build:
          context: ./simple-flask
          dockerfile: Dockerfile-universal
          args:
            - ImageTag=3.7.3-slim
          labels:
            com.pythoninconrainers.app: simple-flask
            com.pythoninconrainers.image.base: slim

      alpine:
        image: shabie/flask-hello:3.7.3-alpine
        ports:
          - 5003:5000
        build:
          context: ./simple-flask
          dockerfile: Dockerfile-universal
          args:
            - ImageTag=3.7.3-alpine
          labels:
            com.pythoninconrainers.app: simple-flask
            com.pythoninconrainers.image.base: alpine
    ```
    
    `docker-compose -f test-build.yaml up -d` builds the image showing warnings that the image was built because was
    not found. Next time you wanna force a re-build, add --build option to the command.
    
    `docker-compose -f test-build.yaml down --rmi all` deletes all the images created as a result of the up command.
    
12. If you are just interested in building images but not in running the service we can do this:

    `docker-compose test-build.yaml build --parallel` this does not include `up` only build so the images are built.
    The additional flag of `--parallel` means images are built in parallel.
    
    `docker-compose test-build.yaml build alpine` only build the image mentioned under the service `alpine`.
    
    `docker-compose -f test-build.yaml push` pushes the built images to registry (does not build them!).
    
13. The `--parallel` for building images isn't always a good idea specially if sequential building is what is needed.
   
14. Docker Compose has a `ps` command to see information about what (is or might run) once we run the docker-compose
file:

    `docker-compose -f django-polls-deploy.yml ps --services`
    
    prints the name of the services that will start or have started:
    
    ```
    db
    app1
    proxy
    ```
    
    We can also do this:
    
    `docker-compose -f django-polls-deploy.yml ps db`
    
    This shows everything about the db service but only if it has been started:
    
    ```
             Name                       Command               State    Ports  
    --------------------------------------------------------------------------
    compose-lifecycle_db_1   docker-entrypoint.sh postg ...   Up      5432/tcp
    ```
    
    Do this without the name of the `db` you get this:
    
    ```
              Name                         Command               State               Ports             
    ---------------------------------------------------------------------------------------------------
    compose-lifecycle_app1_1    uwsgi uwsgi-nginx.ini            Up      8000/tcp                      
    compose-lifecycle_db_1      docker-entrypoint.sh postg ...   Up      5432/tcp                      
    compose-lifecycle_proxy_1   nginx -g daemon off;             Up      80/tcp, 0.0.0.0:8000->8000/tcp
    ```
    
    A service can be paused or un-paused like this:
    
    * `docker-compose -f django-polls-deploy.yml pause db`
    * `docker-compose -f django-polls-deploy.yml unpause db`
    
    Skip the service name and it pauses all services.
    
    Similarly a service can be stopped, started or restarted (restart is stop and start in one). The only change is
    that the `pause` keyword is replaced wit `stop`, `start` and `restart`.
    
    The difference between pause and stop is that pause simply suspends the processes in the container and the full
    state is maintained in memory so it can simply resume immediately. Stop on the other hand gracefully shuts down
    the processes and after a timeout kills them.
    
    Even logs can be checked by replace `pause` with `logs`.
    
    There are two more notable sub-commands: `exec` and `run`.
    
    Exec expects a running container (status up) and executes the command in the container.
    
    Run on the other hand, fires up a new container and runs the command in it. A good use of this is to run the
    one-time commands.
    
    Take for example the db initialization commands. These can be run as `run` in temporary app1 containers:
    
    * `docker-compose-f django-polls-deploy.yml run --rm app1 python manage.py migrate`
    * `docker-compose-f django-polls-deploy.yml run --rm app1 python manage.py loaddata initial_data.json`
    * `docker-compose-f django-polls-deploy.yml run --rm app1 python manage.py createsuperuser` # interactive command
    
15. 
    
    
