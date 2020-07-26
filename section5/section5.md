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
file. The Docker-compose YAML example below will be used for a few examples:

    ```yaml
    version: "3.7"
    services:
      db:
    # Postgres DB Container Version 11.3
        image: postgres:11.4
        networks:
          - polls_net
        volumes:
          - polls_vol:/var/lib/postgresql/data
        env_file:
          - project-files/deployment.env
        command:
          - 'postgres'
          - '-c'
          - 'wal_level=replica'  # wal -> Write Ahead Log -> changes are 1st written in a log before being written to DB
          - '-c'
          - 'archive_mode=on'
      app1:
        image: pythonincontainers/django-polls:nginx
        networks:
          - polls_net
        env_file:
          - project-files/deployment.env
      proxy:
        image: pythonincontainers/mynginx:latest
        networks:
          - polls_net
        ports:
          - "8000:8000"
    networks:
      polls_net:
    volumes:
      polls_vol:
    ```

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
    
    * `docker-compose -f django-polls-deploy.yml run --rm app1 python manage.py migrate`
    * `docker-compose -f django-polls-deploy.yml run --rm app1 python manage.py loaddata initial_data.json`
    * `docker-compose -f django-polls-deploy.yml run --rm app1 python manage.py createsuperuser` # interactive command
    
15. If we wanted to update the version of postgres in the YAML above, we could simply change the version from say 11.3
to 11.4 and do a `docker-compose -f django-polls-depoly up -d` to only update the one service that has changed.

    Docker-compose compares the state of the file running setup to the new docker-compose and stops and restarts
    the services where changes occurred. This means `up` can simply be called again without `down`. Even the data
    remains unharmed because we are using a volume to store it.
    
16. One way to "remember" which commits were the ones where the YAML was changed, we can use git tags. So in the commit
where I make the change to 11.4, I can check that version out later if I have tagged correctly using:
    
    `git checkout [-f] 11.4`  # -f is to force overwrite changes I may have made locally

17. `docker-compose -f django-polls-deploy.yml up -d --remove-orphans` this will remove orphan containers i.e. containers
that are not needed in the current config (say a 4th container where as the current YAML file defines 3).

18. Services are restarted if things change in a docker-compose YAML file (say the postgres version update). If we
follow best practices, they have minimal impact on availability.

19. Docker-compose can be run with multiple docker-compose files. A use-case for such a functionality is that it allows
the operations to be kept separate to the actual services. Here's an example of DB initialization using a second compose
YAML file (notice how it uses the same polls_net but does not define it).

    ```yaml
    version: "3.7"
    volumes:
      polls_clone:
        name: polls_clone  # vol name won't have folder name (called "stack name" in docs) prefix if explicitly defined
    services:
    # Initialization Service
    # please run with:
    # docker-compose -f django-polls-deploy.yml -f django-polls-ops.yml run --rm init
      init:
        image: pythonincontainers/django-polls:nginx
        networks:
          - polls_net
        env_file:
          - project-files/deployment.env
        # the 3 commands we need to initialize
        command: ["/bin/bash", "-c",
                  "python manage.py migrate;
                   python manage.py loaddata initial_data.json;
                   python manage.py createsuperuser"]
        tty: true
    # Database Cloning Service
    # Performs full, on-line Backup of "db" Service onto "polls_clone" Volume
    # Removes previous backup before taking fresh one
    # please run with:
    # docker-compose -f django-polls-deploy.yml -f django-polls-ops.yml run --rm db-clone
      db-clone:
        image: postgres:11.4
        volumes:
          - polls_clone:/clone
        entrypoint: ["/bin/bash", "-c",
                  "rm -rf /clone/*;
                   pg_basebackup -h localhost -U pollsuser -D /clone"]
        network_mode: "service:db"  # attaches this service to network stack of DB service container (same localhost)
    ```

    Then we can run things in two steps:
    
    1. `docker-compose -f django-polls-deploy-yml up -d` : This step is needed to run the 2nd step.
    2. `docker-compose -f django-polls-deploy.yml -f ops.yml run --rm init`
    
20. Docker-compose basically merges compose files if more than one are passed. The ones in the last one overwrite
settings in the earlier ones if identically named services are defined in it. For example, in the example below we
start a db server with a PostgreSQL 11.4 although the first one defines the 11.3:

    `docker-compose -f django-polls-deploy.yml -f psql-11.4.yml up -d`
    
21. Here's a way to do a database clone for test purposes (a hot clone i.e. the db server is available for read/write
the entire time). The YAML file above contains the db-clone service already.

    The command that gets executed is this:
    
    `rm -rf /clone/*; pg_basebackup -h localhost -U pollsuser -D /clone`
    
    It first clears the contents of the folder and then uses the postgres command `pg_basebackup`. The `-h` flag asks
    the postgres engine to enter the hot-backup mode. In this mode, it stops writing data to its data files but keeps
    logging all changes to WAL (write ahead log) file.
    
    After postgres enters this mode, `pg_basebackup` copies all files in the folder where data files are located (in our
    case that would be `/var/lib/postgresql/data` since that is where we mount the volume. See the 2 YAMLs above.) to
    the target folder which is `/clone`.
    
    After the copying is completed, the DB engine quits hot backup mode and closes current WAL file (which BTW also
    gets backed up.)
    
    DB Engine applies all changes from the WAL to the data files (i.e. the database) to get proper state.
    
    This creates an actual clone of a database. This procedure can be used for cases when the application cannot be
    stopped very frequently.
    
22. Let's perform the backup described above. The command to use would be this:

    `docker-compose -f django-polls-deploy.yml -f ops.yml run --rm db-clone`
    
    Even the the services from `django-polls-deploy.yml` were already running when we executed this, the ops file
    needs the context in order to work hence must be mentioned. Only running the ops file like this:
    
    `docker-compose -f ops.yml run --rm db-clone`
    
    returns the error:
    
    `ERROR: Service 'db-clone' uses the network stack of service 'db' which is undefined.`
    
23. The backup can then be tested to really work in a separate container. Here's a separate YAML file to do it. It can
be thought of as a YAML to run our "test" setup using real data (see the volumes section). This YAML file is in a
separate folder which allows easy naming of identically named services (see output of `docker container ls` later):

    ```yaml
    version: "3.7"

    services:
      db:
        image: postgres:11.3
        networks:
          - polls_net
        volumes:
          - polls_vol:/var/lib/postgresql/data
        env_file:
          - deployment.env

      app1:
        image: pythonincontainers/django-polls:nginx
        networks:
          - polls_net
        env_file:
          - deployment.env

      proxy:
        image: pythonincontainers/mynginx:latest
        networks:
          - polls_net
        ports:
          - "8001:8000"

    networks:
      polls_net:

    volumes:
      polls_vol:
        external:  # external option indicates to docker-compose to expect this resource to be available
          name: polls_clone
    ```
    
    If I do `docker container ls` I see this:
    
    ```
    CONTAINER ID        IMAGE                                   COMMAND                  CREATED              STATUS              PORTS                            NAMES
    6a681de0cb66        postgres:11.3                           "docker-entrypoint.s…"   About a minute ago   Up About a minute   5432/tcp                         test-env_db_1
    4b8ffa24b8f8        pythonincontainers/django-polls:nginx   "uwsgi uwsgi-nginx.i…"   About a minute ago   Up About a minute   8000/tcp                         test-env_app1_1
    e2323fd4309e        pythonincontainers/mynginx:latest       "nginx -g 'daemon of…"   About a minute ago   Up About a minute   80/tcp, 0.0.0.0:8001->8000/tcp   test-env_proxy_1
    7d3523b70d45        postgres:11.4                           "docker-entrypoint.s…"   22 hours ago         Up 22 hours         5432/tcp                         compose-lifecycle_db_1
    9eb560f38fdd        pythonincontainers/mynginx:latest       "nginx -g 'daemon of…"   22 hours ago         Up 22 hours         80/tcp, 0.0.0.0:8000->8000/tcp   compose-lifecycle_proxy_1
    5c57e6161853        pythonincontainers/django-polls:nginx   "uwsgi uwsgi-nginx.i…"   22 hours ago         Up 22 hours         8000/tcp                         compose-lifecycle_app1_1
    ```
    
    The backup works as we can see the questions on localhost:8000 as well as localhost:8001
    
24. As a last point let's try to use the backup to start a service with Postgres 12 (the backup was created with 11):

    `docker-compose -f test_env/deploy-clone.yml -f psql-12beta3.yml up -d`
    
    The second YAML file simply overwites the postgres version with the newer one. It contains only this:
    
    ```yaml
    version: "3.7"

    services:
      db:
        image: postgres:12-beta3
    ```
    
    It fails because we are using a different version. This saves us from a disastrous upgrade directly in production.
    We would need another upgrade procedure.
    
    Lets see the logs with this `docker-compose -f test-env/deploy-clone.yml logs db`:
    
    ```shell
    db_1     | 2020-07-15 20:00:54.895 UTC [1] FATAL:  database files are incompatible with server
    db_1     | 2020-07-15 20:00:54.895 UTC [1] DETAIL:  The data directory was initialized by PostgreSQL version 11, which is not compatible with this version 12beta3 (Debian 12~beta3-1.pgdg100+1).
    ```
    
25. What if we had 3/30/300 computers (and hence 3 docker hosts) to run our application? How could we on one hand, take
full advantage of the additional compute power and on the other make sure that we create redundancies in our system
such that a failure of one host is not the failure of the whole system?

    Answer: Container Orchestration - in our case Docker Swarm
    
26. **Container Orchestration is a class of tools that helps to manage large-scale container deployments across a 
cluster of container engine hosts.**

27. Docker Swarm:
    * It is part of the docker engine. This means every docker machine (i.e. a real or virtual machine running its own
    docker engine) can work as swarm node.
    * Docker engine must be switched to swarm mode which can be deactivated at any moment. By default it is not.
    * Swarm cluster is a group of docker engines
    * Smallest swarm can be just one node
    * Nodes can be added later to the swarm cluster
    * No clear guidance on the upper limit of the nodes but should work with several thousand nodes
    * The nodes must be able to communicate with each other using their IP Addresses only over a low-latency network
    * It is technically possible to setup a swarm cluster across AWS or Azure's regions. However, high network latency
    between regions may cause cluster instability and render it unusable.
    * Docker swarm has two types of nodes:
        1. Manager
        2. Worker

28. Manager nodes keep information about cluster state like:
    1. List of all nodes with their types or functions
    2. Statuses of all nodes:
        - if they are healthy and can accept workloads
        - have been paused for maintenance
        - are being drained i.e. nodes are being "emptied" to pause the service or shut it down.
    3. List of all swarm services running in the cluster (one service may have 5 nodes due to 5 replication factor)
    with their desired state and current status
    4. List of all cluster-wide networks and their DNS services
    5. Information about cluster ingress network and port mappings of swarm services.
    6. Configuration and secrets used by swarm services.
    7. There must be at least one manager node in a cluster.
    8. Manager node tasks:
        * Deploy and manage swarm services and service stacks (stack meaning groups of services)
        * Deploy and manager overlay networks. Overlay networks span across cluster nodes enabling easy service
        discovery and communication amongst containers
        *  Perform all other cluster-related operations
        
    >Data Ingress. While data egress describes the outbound traffic originating from within a network, data ingress,
    in contrast, refers to the reverse: traffic that originates outside the network that is traveling into the 
    network.
      
    We will be practicing using 3-4 nodes. The nodes will be created on the same host using VMs.
    
29. Availability of manager nodes:
    * Manager nodes coordinate replication of all manager data between them
    * There should be an odd number of managers to make their consensus algorithm work optimally
    * Hence, the minimum number of nodes needed to maintain high availability is 3
    * If there are 5 manager nodes, the maximum loss allowed is 2
    * Docker recommends a maximum of 7 manager nodes
    * If a manager is lost, a new node can be added to the cluster as a new manager. It quickly replicates data from
    other managers

30. Swarm worker nodes:
    * run the swarm services
    * if a worker node is lost, managers get services to the desired state by restarting lost containers on other nodes

31. Running workload on swarm:
    * Even though `docker run` can be used to run containers on swarm clusters, swarm cluster is unaware of any such
    container and does not take any care of such containers. They are not swam citizens.
    * The point above applies for containers started as a result of `docker-compose`
    * The only way to run and manage containers as swarm objects is by starting them as swarm services only
    * The services can be started in two ways:
        - use `docker service` command
        - deploy services using compose file with `docker stack`
    * Swarm stack extends the concept of compose of multi-node services. Extends because docker-compose starts
    everything on one node but swarm starts it on a multi-node cluster
    * Example: We can launch a service which creates one container on every node of the cluster. This is called the
    global deployment mode. If a new node is added to the cluster, the service container is started automatically on
    it by the service controller.

32. Docker swarm networks:
    * docker swarm can create virtual networks connecting containers running on different nodes
    * Muti-node networks are the core feature of docker swarm. These types of networks are called "overlay" networks.
    * There is a driver also called overlay used to create... overlay networks. It is a standard part of docker engine
    software
    * The KEY feature of overlay networks is its simplicity
    * They are very easy to create and just work!
    * Overlay networks are created either manually or as a part of swarm stack services deployment
    * When we create an overlay network on a manager node, it becomes available for all nodes on the cluster
    * It is not necessarily visible on every node with `docker network ls` but it is there
    * 3rd party plugins in exist like WeaveNet etc. that have some nice features in addition to the standard
    functionality

33. Swarm Ingress network
    * docker swarm has a default cluster-wide ingress network
    * Main goal of this network is to expose ports of the services on every node of the cluster **regardless** if the
    service container actually runs on the node or not
    * Idea: we can add an external load-balancer and configure it to proxy requests to all container nodes without
    caring how particular services are deployed inside cluster. Question: But doesn't that mean that it will be
    handled simultaneously by all replicas running? Explanation will follow later.
    
    To proxy a request means to basically direct the request to a server that then makes a request on behalf of that
    original request. To the server it seems like it originated from the proxy server itself.
    
    [Reverse Proxy vs Load Balancer - Difference](nginx.com/resources/glossary/reverse-proxy-vs-load-balancer/)
    
34. Volumes in Swarm:
    * swarm services can use persistent volumes
    * swarm cluster has no special arrangements for cluster-wide storage
    * volumes are created on nodes where the container is scheduled to implement swarm service
    * the last point means that if the local disk was used to store the volume, loss of node means loss of data since
    the persistent volumes are lost
    * swarm may restart nodes and recreate persistent volumes on other nodes according to restart policies. These are,
    however, going to be new volumes
    * A high availability storage backend can be deployed to prevent data loss using wide array of 3rd party plugins
    that make this possible preventing data loss
    * Another option to prevent data loss due to node loss is to data replication on an application component level
    * Finally, another option is database replication (master - slave nodes I guess)

35. A swarm cluster can be provisioned using VMs. Let's create one:

    `docker-machine create -d <driver> swarm-mgr1`
    `docker-machine create -d <driver> swarm-wrk1`
    `docker-machine create -d <driver> swarm-wrk2`
    
    The driver can be the virtualbox driver (on linux) and hyperv on windows.
    
    It takes a while to create all 3 VMs. To test them, we can run an ssh command on all 3 of them:
    
    `docker-machine ssh swarm-mgr1 docker --version`
    
    Doing `docker-machine ls` returns this:
    
    ```shell
    NAME         ACTIVE   DRIVER       STATE     URL                         SWARM   DOCKER      ERRORS
    swarm-mgr1   -        virtualbox   Running   tcp://192.168.99.100:2376           v19.03.12   
    swarm-wrk1   -        virtualbox   Running   tcp://192.168.99.101:2376           v19.03.12   
    swarm-wrk2   -        virtualbox   Running   tcp://192.168.99.102:2376           v19.03.12   
    ```
    
36. Swarm cluster must be initialized on one of participating nodes which is going to become a manager node. Then all
nodes join the cluster as managers or worker nodes.

37. Let's initialize a cluster on the machine called `swarm-mgr1`:

    **`docker-machine ssh swarm-mgr1 docker swarm init --advertise-addr $(docker-machine ip swarm-mgr1)`**
    
    The response looks like this:
    
    ```shell
    Swarm initialized: current node (c9cfunq2lcdipb2v4fjj74vcm) is now a manager.

    To add a worker to this swarm, run the following command:

        docker swarm join --token SWMTKN-1-0rmf7ni4q5x28wypil0zsdsdl75y3cz4fvis8f3tm9zz-6vamzbbkds88fxfm4minfgoho 192.168.99.104:2377

    To add a manager to this swarm, run 'docker swarm join-token manager' and follow the instructions.
    ```
    
38. Why was this flag `--advertise-addr` necessary? Because the docker-machine has different addresses on 2
different interfaces (as a matter of fact this is the error message itself too :D):

    1. NAT (Network Address Translation) Interface with 10.0.2.15 Address: This gives the machine access to internet
    via development host networking stack. **The machine is not reachable (locally or anywhere) at this IP**.
    2. Host-only Interface with IP Address in `192.168.99.0/24` network (actual IP in this case is 192.168.99.100):
    This IP is assigned to the so-called host network. Each of the 3 machines are connected to this network with a
    unique address (as can be seen above) and can talk to each other as well as the host system.
    
    Question: Why are IPs called interfaces?
    
    Because all network addresses, including IP addresses, are network interfaces. We don't ping a computer, we ping
    its network interface. The word "interface" as the name suggests is the point of interconnection between two
    devices (on a network). Without an interface, the communication between two networks or networked devices is
    not possible.
    
    Below is an interesting blog on the matter. Most interesting is how a web-server is started in a newly created 
    network namespace (defined on the host) which is unreachable from the host through cURL simply because it doesn't
    have any interface to understand the request packet being sent through cURL.
    
    Interfaces were historically pieces of hardware where you plugged in the cable but now can also be written
    in software.
    
    [Brilliant post on what is a network interface really](https://jvns.ca/blog/2017/09/03/network-interfaces/)
    
39. The newly created cluster, as the instructions show, can be joined using an encrypted token and the node address.
Hence, the token should be kept secret. It is a bad idea to put them on github for example.

40. The token can be viewed later using this command (both for joining as manager and worker):

    `docker-machine ssh swarm-mgr1 docker swarm join-token [worker|manager]`
    
    The tokens are valid until we rotate them.
    
41. Let's make the worker machines join the swarm:
    
    `docker-machine ssh swarm-wrk1 docker swarm join --token <TOKEN> 192.168.99.100:2377`
    
42. Let's check if it worked `docker-machine ssh <MACHINE_NAME> docker info | grep Swarm`

    The output looks like (or should look like) this: `Swarm: active` on all 3 nodes.
    
43. The above setup is okay for test or dev but not production. Swarm can use separate physical networks for
management data and for user or workload data. This is one of the required features in production setup.

44. To simplify things we can set the context to manager machine. First check using `docker-machine env swarm-mgr1`
and then execute the instruction. `eval $(docker-machine env swarm-mgr1)`

45. We deploy one utility service to get a visual representation of our services in the cluster. Docker has a name
and image to implement it `dockersamples/visualizer`. The dockerhub page provides the command to be executed:

    ```shell
    docker service create \
    --name=viz \
    --publish=8080:8080/tcp \
    --constraint=node.role==manager \
    --mount=type=bind,src=/var/run/docker.sock,dst=/var/run/docker.sock \
    dockersamples/visualizer:stable
    ```
    
    We can run the command directly since the context is set already and no need to do `docker-machine ssh...`.
    
    It takes a some time since the image is pulled into the machine. This is what can finally be seen at the IP
    address of the docker-machine (The IP can be found using `docker-machine ip swarm-mgr1`:
    
    ![docker swarm visualizer](staticfiles/docker-swarm-visualizer.png)
    
    The swarm can be removed with the following command: `docker-machine rm swarm-mgr1 swarm-wrk1 swarm-wrk2`
    
46. The commands specific to docker swarm are not that many:
    
    * `docker swarm` - manage swarm cluster
    * `docker node` - manage swarm nodes
    * `docker service` - create and manage swarm services
    * `docker stack` - create and manage stacks of services
    * `docker deploy` - short of `docker stack deploy`
    * `docker config` - create and manage cluster-wide service configuration files
    * `docker secrets` - create and manage cluster-wide service secrets
    * `docker network` - create and manage cluster-wide overlay networks (also used normally)
    
    All other normal docker commands, even though they can be executed, operate on a single docker engine (engine is 
    more specific since docker host may be running multiple engines through VMs) and not on the whole cluster.
    
47. Important considerations regarding docker swarm:

    * Images - All commands related to images work on a single node. `docker build` works on a single node and stores
    the image in that node's cache only. Swarm does not provide any special cluster-oriented image management commands.
    
    If images must be made available to more than one node, they must be made available on an image registry like
    Dockerhub, Azure Container Registry etc. Another option is to use local registry setup on a docker-machine.
    
    * Volumes - Docker swarm doesn't have any special support for managing persistent volumes in a cluster.
    
    Volumes are create on a node and are accessible only on this particular node. Swarm has no command to move or copy
    docker volumes between nodes.
    
    The open-source community has developed "swarm-aware" storage plug-ins to fill the gap.
    
    * Networks - Standard bridge type network is accessible on a node only where it is created.
    
    Published nodes can be access on any node in a swarm by using the publishing node-IP address or node-DNS name.
    
    Swarm comes with an overlay network driver to create virtual networks available and accessible on all nodes in the
    cluster.
    
    This means that a standalone container (a container that is not a swarm citizen) can join such a network and can
    communicate with all the services using the network.
    
    * High availability - Swarm services can have redundancies and if a node disappears another is fired up to keep
    the number of nodes of a service the same.
    
48. 