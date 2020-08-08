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
    
    The driver (`-d`) can be the virtualbox driver (on linux) and hyperv on windows.
    
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
    
    A node can leave the swarm by executing `docker swarm leave` on the worker.
    
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
    
48. The commands to follow will assume `eval $(docker-machine env swarm-mgr1/wrk1/wrk2)` has been done in the terminal.

    To check which machine's engine the terminal is accessing do `docker-machine ls` and check the * in the `ACTIVE`
    column.
    
    Let's run a container on worker 1 (assuming env vars set):
    
    `docker run -d --name hello -p 5000:5000 pythonincontainers/simple-flask`
    
    The container is then accessible on: `192-168.99.101:5000`. It is neither accessible nor visible from other nodes
    since this standalone container is not a member of swarm cluster (I guess) and is not connected to overlay network.
    
49. Let's create an **overlay** network and run containers attached to it on all nodes. `docker network create` has
following options:

    1. `--driver overlay` - this is mandatory if we want an overlay network
    2. `--attachable` - if we want to attach standalone containers to it, we must use this option
    3. `--opt encrypted` - enable encryption of data sent between cluster nodes (AES)
    
    `docker network create --driver overlay --attachable cluster_net`
    
    Executing this on worker1 node gives the following error:
    ```bash
    Error response from daemon: Cannot create a multi-host network from a worker node. Please create the network from a manager node.
    ```
    
    **All swarm related operations must be performed on manager node.**
    
    The network is now available in the list of networks `docker network ls`.

50. We will be implementing the following multi-node setup:

    ![multi node setup](staticfiles/multi-node-setup.png)
    
51. Let's get started. First setup the database on manager node:

    `docker run -d --name db --network cluster_net -e POSTGRES_USER=pollsuser -e POSTGRES_PASSWORD=pollspass -e POSTGRES_DB=pollsdb postgres:11.3`
    
    And check the logs using `docker logs db`. We didn't create a persistent volume but it would have been created
    using an anonymous name by docker engine itself anyways.
    
52. Even though overlay network `cluster_net` is not visible on worker 1, it is there. So let's start the application
server:

    `docker run -d --name app1 --network cluster_net -e "DATABASE_URL=postgresql://pollsuser:pollspass@db/pollsdb" pythonincontainers/django-polls:nginx`
    
    We can check the logs to see it works perfectly. Let's initialize the database:
    
    `docker run -it --rm --network cluster_net -e "DATABASE_URL=postgresql://pollsuser:pollspass@db/pollsdb" pythonincontainers/django-polls:nginx python manage.py migrate`
    
    This works perfectly meaning that this container can access the `db` container running on a different node without
    problems and that too using just the container name `db`. Multi-node container name resolution is one of the coolest
    features of Docker swarm.
    
    We can just create the super user and complete the initialization. We will skip loading initial data:
    
    `docker run -it --rm --network cluster_net -e "DATABASE_URL=postgresql://pollsuser:pollspass@db/pollsdb" pythonincontainers/django-polls:nginx python manage.py createsuperuser`
    
53. Let's run the custom nginx (proxy) server on worker 2:

    `docker run -d --name proxy --network cluster_net -p 8000:8000 pythonincontainers/mynginx:latest`
    
    The website is accessible at the worker 2 node: `192.168.99.102:8000`
    
    Side note: Even though overlay network has container name resolution (DNS), some python modules using DNS caching
    and this can be a problem if the container has restarted on a different node. This affect nginx also. But there
    are settings available to overcome this problem.
    
    Best cleanup by removing containers on the 3 nodes and additionally the volume and network on the manager node
    where the database container was setup.
    
54. Swarm service starts a container or multiple containers as a part of cluster NOT as standalone containers like the
example we saw above.

    A service is created on the manager node.
    
    **We can say that swarm service definition is like a desired state concept** like we learnt when using
    docker-compose. The idea of "desired state concept" goes back to declarative programming or config where the
    desired state is just explicitly declared and the provisioning tool takes care of the "how" part i.e. how to bring
    the system to this state.

55. Launching a swarm service == telling the swarm manager the desired state of the service. This includes:

    * Image this service should run: This means that a service is homogeneous when it is in the desired state. All
    containers implementing the service use the same image. 
    
    A service can be in a rolling update state in which its images are changed to new ones.
    
    * Type of Deployment and number of replicas: Identical containers used to launch a service are called replicas.
    
    * Placement preferences and constraints: Service replicas can be scheduled to run on a subset of swarm cluster nodes
    that have matching preferences or constraints. My comment: May be you want tensorflow containers to run only on
    nodes with dedicated GPUs.
    
    We can schedule a service to have all its replicas on a particular node or only on manager nodes in a given
    datacenter etc.
    
    * Health checks: A service may have a health check mechanism defined as well as how to control health status
    of the container implementing this service.
    
    * Resource Limits and Reservations: Since swarm allows a certain level of automation in the management of services,
    it also enables control of resource usage for a given service in a cluster.
    
    We can, for example, specify the maximum amount of RAM or CPU which a service can use.
    
    Another option is to reserve a certain amount of resources to always be available to containers implementing a
    certain service.
    
    * Restart Policy: Swarm manager may be required to restart containers under specific containers. This is used to
    declare desired behavior.
    
    * Update and Rollback policy: Swarm managers can automate service image update. If and when a new image is available
    the container implementing the given service may be restarted with the newer image. Options to consider:
    
        - how to restart the containers
        - how many at a time
        - what delay between restarts
        - what to do if there is a failure
        - how to roll-back if the new image is broken
        
    * Configs and Secrets: These can be consumed by the containers of the service in swarm.
    
    * Networks: Containers implementing the service should be attached to the given networks.
    
    * Volumes: Containers implementing the service should be attached to the given volumes.
    
    * Other desired properties include: hostname, USERID to run the container, working directory etc.
    
56. All the elements mentioned in the last point jointly define the desired state of the service. 

    1. We pass it to the swarm manager with **`docker service create`**
    2. or put it in a docker-compose file with some extra swarm related options and pass it with `docker stack deploy`
    
57. Assuming the cluster has been initialized (workers have joined it) and we are in the swarm manager context, we can
execute the following:

    `docker service create --detach --name hello --replicas 2 -p 5000:5000 --hostname "hello-{{.Task.Slot}}" pythonincontainers/flask-hostname`
    
    * `docker service create` creates a new swarm service in a cluster
    * `--detach` new service is supposed to run in the background and not send its logs to the terminal window
    * `--name` sets the service name (in this case "hello")
    * `--replicas` sets the service to be run in 'replicated' mode (the default type) with 2 replicas (default is 1).
    * `-p 5000:5000` publishes 5000 of each container implementing this service to port 5000 of the `ingress` network
    (which is an overlay network as can be seen doing `docker network ls`:
    
    ```shell
    NETWORK ID          NAME                DRIVER              SCOPE
    c2bddd2418cb        bridge              bridge              local
    f599fa4123b5        docker_gwbridge     bridge              local
    14ae5bb0bf0b        host                host                local
    0upkld9z57uc        ingress             overlay             swarm
    fdc24cf2cb7e        none                null                local
    ```
    * `--hostname` sets the hostname of each container of the service. In this case it is set to hello +
    sequence number of the container. More on name templates later.
    
    The first time the command it executed it takes a while since each swarm node where containers are scheduled to run
    must pull the image from Dockerhub.
    
58. Services in a cluster can be listed using `docker service ls` which when executed (only possible manager node)
shows the following:

    ```shell
    ID              NAME       MODE          REPLICAS     IMAGE                                      PORTS
    mn2o362xzcjy    hello      replicated    2/2          pythonincontainers/flask-hostname:latest   *:5000->5000/tcp
    ```
    
    Replicas 2/2 means <how many are running> / <how many are desired>
    
59. We can see the basic details of the service by doing `docker service ps <service name>` (service name is "hello"):

    ```shell
    ID             NAME       IMAGE                                      NODE         DESIRED STATE   CURRENT STATE            ERROR   PORTS
    n4fufovvlg7r   hello.1    pythonincontainers/flask-hostname:latest   swarm-mgr1   Running         Running 35 minutes ago                       
    emdmjrbmkul8   hello.2    pythonincontainers/flask-hostname:latest   swarm-wrk2   Running         Running 35 minutes ago                       
    ```

60. Swarm uses **"tasks"** to implement services which is another name for containers that are swarm citizens. A task is 
analogous to a “slot” where the scheduler places a container. Once the container is live, the scheduler recognizes that
the task is in a running state.

61. "hello" service implemented above has 2 tasks each implementing one replica. Each task in turn gets implemented
with exactly one container.

62. The docker containers can be viewed on the corresponding node using the familiar `docker ps` command.

63. How does docker decide what nodes to the run the tasks on? The default scheduling algorithm is spread. The goal
of the algorithm is to evenly allocate containers to all swarm nodes.

64. Swarm service can be inspected with `docker service inspect --pretty <service name>`. The pretty flag makes the
output more YAML like than JSON:

    ```YAML
    ID:             mn2o362xzcjy4t2rg2h00w8wt
    Name:           hello
    Service Mode:   Replicated
     Replicas:      2
    Placement:
    UpdateConfig:
     Parallelism:   1
     On failure:    pause
     Monitoring Period: 5s
     Max failure ratio: 0
     Update order:      stop-first
    RollbackConfig:
     Parallelism:   1
     On failure:    pause
     Monitoring Period: 5s
     Max failure ratio: 0
     Rollback order:    stop-first
    ContainerSpec:
     Image:         pythonincontainers/flask-hostname:latest@sha256:a31ee9ea32c263ed69f53a857ce821c8db3ec584b5d43bc8e0efa1d675335a58
     Init:          false
    Resources:
    Endpoint Mode:  vip
    Ports:
     PublishedPort = 5000
      Protocol = tcp
      TargetPort = 5000
      PublishMode = ingress 
    ```

    One interesting thing is the `Endpoint Mode: vip` where vip stands for virtual IP. This means that the *service*
    itself also gets its own (virtual) IP address besides each implementing container getting its own IP address.
    
    We can also see in the very last line that the `PublishMode` is ingress.
    
65. So going back the question: what is this `Endpoint Mode: vip`? This can be visualized rather simply using the
following diagram:

    ![sawrm service virtual endpoint ip](staticfiles/service-virtual-endpoint-ip.png)
    
    Our hello service has 2 replicas which means there are 2 containers with their own IPs. Containers, however, can
    come and go since they are disposable. If a container (implementing a task) dies or otherwise becomes unhealthy,
    the swarm manager can restart it according to the restart policy.
    
    So the service is kept available regardless of the containers implementing it or the current health status of each.
    
    Hence, the service has a fixed network endpoint i.e. its virtual IP address.
    
    The service discovery returns the endpoint virtual IP each time we lookup the service name. This means we are no
    longer concerned with the individual containers of our service (and hence their IPs).
    
    When a client sends a request to the service endpoint, swarm routes this request to one of the active containers
    (tasks) implementing the service.
    
    To make it concrete -> when we send a request to `hello:5000` the request is sent to port 5000 of one of the
    two service containers. We can try this out by first finding out the IP of the swarm-mgr1 using 
    `docker-machine ip swarm-mgr1` and then making requests to <IP:5000>. We can see from the changing number in the
    response to different containers respond to the request everytime it is refreshed. Question from me: This is the
    IP of the VM (i.d. docker-machine). I still don't know how to see the virtual IP of the swarm service (if it
    exists as a number and not merely as an abstraction).
    
    Swarm uses round robin algorithm to spread requests evenly across all tasks.
    
    Lets update the number of replicas to 5:
    
    `docker service update --replicas 5 hello`
    
    and scale it down again using the same command (replace 5 with 3).
    
66. When do replicas make sense? Allows for the increased parallel handling of requests.
    
67. Swarm can upscale and downscale the number of replicas depending on the number of incoming requests.

68. The application must be architected and coded properly to take advantage of the service model of docker swarm.

69. Essentially, a swarm service is a controller object. An object used to manage state.

70. Tasks monitor the containers they run.

71. To see the "static" virtual IP of the service we can do the following:

    `docker service inspect --format '{{json .Endpoint.VirtualIPs}}' hello | jq '.'`

    Another way is to start a cluster using a manually created overlay network (default ingress is not manually
    attachable) and then joining that network with a linux container to ping the service or do `nslookup <service name>`
    to see the IPs of the service and that of the supporting containers.
    
    The way to start a service with a custom network is to create one and then pass it as flag
    `--network <network name>` to the `docker service create`. See lecture "84. Service Modes and Ingress Routing Mesh"
    for details.
    
    The entire service can be removed using `docker service rm <service name>`
    
72. Docker swarm has another service mode called **global**. In this mode, a service creates exactly one task per
cluster node.

    This kind of setup is useful in following scenarios:
    
    1. Fat containers: May be allowed to use nearly all node's resources
    2. High availability: More nodes means better availability. One example could be a DB engine in each node. Swarm
    doesn't offer good control over its scheduling algorithm and can't really guarantee an even spread of containers
    in the replicated mode.
    3. Control and Monitoring Services: Such should be run globally to have access to docker socket for example.
    Another example is the GUI tool Pertainer which is also deployed in global mode to be able to monitor containers
    in each node of the cluster.
    
    A service in the global mode would look like this:
    
    ![swarm service global mode](staticfiles/swarm-service-global-mode.png)
    
73. Let's start a global service:

    `docker service create --name global --network hello_net --mode global pythonincontainers/flask-hostname`
    
    hello_net was created previously using:
    
    `docker network create --driver overlay --attachable hello_net`
    
    Now we can have a look at the tasks using `docker service ps global`:
    
    ```shell
    ID            NAME                               IMAGE                                      NODE         DESIRED STATE       CURRENT STATE                ERROR               PORTS
    uzqqlan9uh49  global.2gdaqa5r48wrvqrre3ty1vgox   pythonincontainers/flask-hostname:latest   swarm-wrk1   Running             Running about a minute ago                       
    52rgpgqinr3m  global.doywba3lxyyxpl2euoi1rqvlk   pythonincontainers/flask-hostname:latest   swarm-mgr1   Running             Running about a minute ago                       
    zroi28qv9b5c  global.aiewdphpac3yk6i9gto18r592   pythonincontainers/flask-hostname:latest   swarm-wrk2   Running             Running about a minute ago            
    ```
    
    The names are uglier since they have node IDs now instead of task number.
    
    The IDs can be found if we do `docker node ls` and compare the NAME column of the last table with ID column below:
    
    ```shell
    ID                            HOSTNAME     STATUS    AVAILABILITY    MANAGER STATUS      ENGINE VERSION
    doywba3lxyyxpl2euoi1rqvlk *   swarm-mgr1   Ready     Active          Leader              19.03.12
    2gdaqa5r48wrvqrre3ty1vgox     swarm-wrk1   Ready     Active                              19.03.12
    aiewdphpac3yk6i9gto18r592     swarm-wrk2   Ready     Active                              19.03.12
    ```
    
74. Service behavior when a container fails or gets lost is very similar to the replicated mode. The task is recreated
on the same node.

    Similarly, the endpoint is also static (the vip mode) and the load is distributed evenly across the containers.
    
    We can resolve the DNS name "global" to get the IPs of all containers implementing the service.
    
75. Swarm services can publish ports. If service endpoint mode is set to VIP (virtual IP), any traffic sent to the
published port is sent to entrypoint virtual IP (i.e. service's VIP) and gets routed to one of the containers of the
service.

76. Service can publish ports in 2 modes:

    * Ingress
    * Host
    
    Lets have a look at differences.
    
77. Ingress mode:

    * Ingress network spans across all nodes in the swarm
    * Port published in the ingress mode is published to the same target on each node
    * This means that say if port 5000 has been published, this means we can access the service on port 5000 on every
    swarm node (i.e. directly use a worker node's IP with port 5000 will still lead to a valid response that may
    actually be generated from a container in another node since there is no guarantee the same node's container
    will get the chance to process it)
    * Requests are routed to the service VIP (virtual IP) which evenly routes the requests to all containers
    * Side point: When doing `docker service create` the long syntax for port publishing can be used which goes like
    this: `docker service create .... --publish published=5000,target=5000,mode=ingress` (3 params all without spaces).
    * Global mode behaves pretty much like the replicated mode except that there is a container on each node.
    
78. Host mode:

    * The service mesh created by ingress can be bypassed using the host mode.
    * To create (using long syntax): `docker service create ... --publish published=5001,target=5000,mode=host`
    * This means that a request on a swarm node will be served by the container on that node. We avoid extra circulation
    of the request first being routed to the service endpoint that then routes it again to one of the containers.
    * This can be verified by using the IP of the swarm node and calling the published port several times, it will
    always be served by that same node's container (which uses that port of the node in question).
    * This doesn't mean the service is not accessible using its VIP address to other services that may be part of the
    same network. 
    * In fact, replicated service can also have published ports in host mode. This means that if the request is
    coming from a node, then that node better have a container running the service otherwise it is not routed to the
    service endpoint (only services that use the endpoint directly benefit from the VIP endpoint).
    
      Furthermore, this also means a maximum of one container per node can be run despite being on the "replicated" mode
      since there will be a port conflict if 2 containers on the same node try to publish to the same node.

79. So there are 2 ways to deploy multi-container applications in a swarm cluster:
    
    1. service by service manually (very error prone)
    2. all services as a stack
    
80. `docker stack` is used to deploy and manage deployments. Individual services in the deployment are managed using
the `docker service` command.

    Docker stack command can deploy groups of services defined in docker-compose file to a swarm or even kubernetes
    cluster.
    
    The deployment in a kubernetes cluster is an interesting feature. We can try and test the deployment first
    in the swarm cluster and then deploy it in production in a kubernetes cluster.
    
81. Docker stack command **ignores** some docker compose file options. Similarly, it uses some other options that
are ignored by the docker-compose command.

    Here are the differences:
    
    ![compose file options ignored stack vs compose](staticfiles/options-ignored-compose.png)

    For example, stack command doesn't build images defined in compose file

82. Configs and secrets:
    * Both work in a similar way. 
    * They are created with a file or read from standard input
    * Can be text or binary
    * Sent over encrypted connection to swarm managers
    * Stored in Raft log at manager nodes
    * The Raft log is synchronised between all manager nodes
    
    Raft consensus group:
    
    ![raft consensus group](staticfiles/raft-log.png)
    
    An excellent visual description of the raft algorithm can be found [here](http://thesecretlivesofdata.com/raft/).
    
    Highlights of raft visualization:
    1. How a leader node is selected using voting
    2. How in case of even number of nodes, leader is selected by nodes becoming candidates after a random delay to
    break deadlock
    3. If by a very small chance, delay matches up, candidacy delays are reset since two nodes can't both be leaders
    4. How a leader waits for confirmation from follow nodes before committing etc.
    
83. When a service task is about to launch a container using a config, it is retrieved by the docker engine on the
target node over encrypted connection. Then the content of the config is stored in a file at engine storage area and
mounted into container's filesystem at the specified path.

    We can specify UserID and GroupID as access mode for the mounted config file.
    
84. Docker engine doesn't interpret the content of the config file so it can be text or any other text like binary.

85. A mounted config is read-only. Config can be updated and running services can be updated with a new version of the
config.

86. Secrets are handled in a similar way (as mentioned earlier) but with one difference: swarm nodes store encrypted
secret in **memory filesystem only during the lifetime of the containers** granted access to the secret.

    When a container is removed, the secret it used is flushed away from its node's memory.
    
87. Secrets can be mounted as files in the container's filesystem. Configs are mounted at "/" as read-only files.
Secrets are mounted as read-only files too at "/run".

88. Let's look at a docker-compose file defining groups of services (as a stack):

    ```yaml
    # flask_hostname.yml
    version: "3.7"  # this is the docker-compose version NOT python version

    networks:
      hello_net:  # should be accessible under this name for containers & services outside of this deployment
        driver: overlay
        name: hello_net
        attachable: true

    configs:
      nginx_config:
        file: ./flask_lb_nginx.conf
      # my_other_config:
        # external: true # configs can also be declared outside of compose file using `docker config create` cmd

    secrets:  
      my_password:  # each container part of this hello service will be granted access to this secret
        file: ./my_password.txt
      # my_other_password:
        # external: true # secrets can also be defined outside of compose file using `docker secret create`

    services:
      hello:
        image: pythonincontainers/flask-hostname:v1  # node running the task must have access to dockerhub
        networks:
          - hello_net
        secrets:  # mounted in /run/secrets as a file called my_password in the container filesystem
          - source: my_password
            target: my_password  # if path begins with / then it's considered an absolute path else within /run/secrets
            uid: '999'  # user id
            gid: '0'    # group id
            mode: 0440  # user and group both can't write or execute, only read https://chmodcommand.com/chmod-0440/
        # docs: https://docs.docker.com/engine/reference/commandline/service_create/#create-services-using-templates
        hostname: "hello-{{.Task.Slot}}"  # example of named template. can even be used for env. vars. specific to node.
        deploy:
          mode: replicated    # or global
          replicas: 3         # valid for replicated mode
          endpoint_mode: vip  # service virtual IP
          placement:
            constraints:
              - node.role == worker  # deploy only on worker nodes
              ### other options ###
              # - node.hostname
              # - node.id
              # - node.labels
              # - engine.labels
        labels:
          com.example.stack.composefiles: "flask_hostname.yml"

      proxy:
        image: nginx:1.16.0
        networks:
          - hello_net
        configs:
          - source: nginx_config
            target: /etc/nginx/conf.d/hello.conf  # path where the config will be loaded in the container filesystem
        ports:
          - target: 5000
            published: 5000
            mode: ingress
        deploy:
          mode: replicated
          replicas: 1
          endpoint_mode: vip
          placement:
            constraints:
              - node.role == manager
        labels:
          com.example.stack.composefiles: "flask_hostname.yml"
    ```
    
89. A note about the deployment specially with regards to Nginx. The compose file such as the one above is deployed
in a certain order:

    1. First stack command creates configs, secrets and networks
    2. Then services and associated volumes
    3. Services are deployed in random order as well as tasks within the service
    
    Hence there is no guarantee that hello service deploys as the first one and then the proxy.
    
    Another factor influencing the order is the image availability which must be pulled if not available in local
    image cache of the node. Some nodes may pull images faster than others.
    
    This means proxy service may start running before hello service starts.
    
    Nginx in the community edition checks the availability of the upstream system (i.e. the application server) first
    thing after it comes up. This is not relevant to Nginx plus (the paid version).
    
    Hence, if there are no hello service containers up and running by that time, Nginx fails.
    
    Swarm cluster will restart it until it can find the hello container.
    
    To avoid this from happening, we need a workaround. The workaround (though I am not sure what it is doing), looks
    like this:
    
    ```
    # flask_lb_nginx.conf

    server {
    listen      5000;
    server_name _; # special "catch all" Server Name, please substitute with something appropriate
    charset     utf-8;

    client_max_body_size 75M;   # adjust to taste

    resolver 127.0.0.11;

    set $hello http://hello_hello:5000;

    location / {
        proxy_pass $hello;
        }
    }
    ```
    
90. Let's deploy!

    `docker stack deploy -c flask_hostname.yml hello`
    
    where "hello" at the end is an arbitrary name we have chosen for this stack.
    
    The deployment is visible in the visualizer.
    
    ![stack deployment](staticfiles/stack-deployment.png)
    
    The service names are hello_hello and hello_proxy so the pattern is <STACK_NAME>_<SERVICE_NAME>.
    
    ```shell
    shabie:~/projects/containers/section5/swarm-stack(master)$ docker service ls
    ID            NAME          MODE          REPLICAS      IMAGE                                  PORTS
    rm8tehhay1v8  hello_hello   replicated    3/3           pythonincontainers/flask-hostname:v1   
    rcup4z3mvtnj  hello_proxy   replicated    1/1           nginx:1.16.0                           *:5000->5000/tcp
    8igonzav0fcm  viz           replicated    1/1           dockersamples/visualizer:stable        *:8080->8080/tcp
    ```
    
    We can see also the output of `docker stack ls`:
    
    ```
    NAME                SERVICES            ORCHESTRATOR
    hello               2                   Swarm
    ```
    
    Also try `docker stack services hello` returns the same as `docker service ls` but only for one stack named hello.
    
    To list all tasks of a stack we can do `docker stack ps hello`:
    
    ```
    ID            NAME           IMAGE                                  NODE         DESIRED STATE  CURRENT STATE            ERROR               PORTS
    rvaxro6ys07z  hello_proxy.1  nginx:1.16.0                           swarm-mgr1   Running        Running 16 minutes ago                       
    vpzcwrbwxybv  hello_hello.1  pythonincontainers/flask-hostname:v1   swarm-wrk2   Running        Running 16 minutes ago                       
    sc456kbx31xn  hello_hello.2  pythonincontainers/flask-hostname:v1   swarm-wrk2   Running        Running 16 minutes ago                       
    z5zhidmwbkjj  hello_hello.3  pythonincontainers/flask-hostname:v1   swarm-wrk1   Running        Running 16 minutes ago                       
    ```
   
    The command above will also show any failed ro stopped tasks since the deployment started.
    
91. Let's try to access the stack deployment. Since the proxy service publishes the port 5000 in ingress mode,
this means the service is accessible on any node.

    Let's try to access it from worker node 2.
    
    `curl $(docker-machine ip):5000 swarm-wrk2` to get the IP first.
    
    Several calls will rotate the number since requests are forwarded to one of the 3 replicas using the SPREAD
    algorithm.
    
    ```bash
    shabie:~/projects/containers/section5/swarm-stack(master)$ curl $(docker-machine ip swarm-wrk2):5000
    Flask Hello world! I am running on hello-3
    shabie:~/projects/containers/section5/swarm-stack(master)$ curl $(docker-machine ip swarm-wrk2):5000
    Flask Hello world! I am running on hello-2
    shabie:~/projects/containers/section5/swarm-stack(master)$ curl $(docker-machine ip swarm-wrk2):5000
    Flask Hello world! I am running on hello-1
    ```
    
    We can scale up just the hello service of the hello stack using the following command:
    
    `docker service update --replicas 6 hello_hello`
    
    This is possible but should be avoided because the state (i.e. 6 replicas) of the services is not as declared;
    in the compose file.
    
    A stack can be brought back to its declared state in compose file by simply running the deploy command again.
    
    The right way to update the number of replicas would be create a new version of the compose file (or I guess at
    least have a new commit for it).
    
    Let's say we have another version that just has a different number of replicas. What do we do?
    
    We can just do this: `docker stack deploy -c flask_hostname_v2.yml hello` and the services will be updated.
    
    Update of the stack is a subject of application lifecycle in a swarm cluster. More details on this to follow.
    
    Let's bring it down: `docker stack rm hello`
    
92. Let's deploy a stack that has an scalable database cluster with the following YAML:

    ```yaml
    version: "3.7"

    networks:
      galera_net:
        driver: overlay
        name: galera_net
        attachable: true
      proxy_net:
        driver: overlay

    configs:
      proxy_conf:
        file: ./mysite_nginx_in_swarm.conf

    services:

      galera:  # based on https://github.com/matthanley/docker-galera (interesting article included)
        # this implementation includes automated deployment, fail-over & rejoining of recovered galera nodes
        # also this is master-master setup: https://en.wikipedia.org/wiki/Multi-master_replication
        image: pythonincontainers/galera:latest
        env_file:
          - ./db_params.env
        networks:
          - galera_net
        deploy:
          mode: global  # endpoint mode is VirtualIP which is default so not explicitly declared
    # Galera Image requires SERVICE_NAME variable to be set to actual name
    # of 'galera' Service. Value below assumes the Stack is deployed
    # with 'django-polls' Stack Name.
    # Service Name is '<stack_name>_galera'
        environment:
          SERVICE_NAME: django-polls_galera

      app:
        image: pythonincontainers/django-polls:nginx
        networks:
          - galera_net
          - proxy_net
        env_file:
          - ./db_params.env
        deploy:
          mode: replicated
          replicas: 3

      proxy:
        image: pythonincontainers/mynginx:latest
        networks:
          - proxy_net
        ports:
          - target: 8000
            published: 8000
            mode: host
        configs:
          - source: proxy_conf
            target: /etc/nginx/conf.d/mysite_nginx.conf
        deploy:
          mode: global
    ```
    
    To deploy:
    `docker stack deploy -c <yaml-filename> django-polls`
    
    The deployment stack now looks like this:
    
    ![stack deployment db cluster](staticfiles/stack-deployment-db-cluster.png)
    
    The database in django-polls needs initialization so we can do that now by using a standalone container that is
    attached to the galera_net.
    
    `docker run --rm -it --network galera_net -e "DATABASE_URL=mysql://pollsuser:pollspass@galera/pollsdb" pythonincontainers/django-polls:nginx python manage.py migrate`
    
    >A few considerations: the containers need to be in sync before galera can start i.e. all tasks need to have been
    initialized before it becomes available. This means that there are a few moments right after the deployment where
    galera is in the cluster synchronisation phase but the service endpoint may end up sending requests to it that
    don't get served. This takes a few seconds but something to be aware of.
    >
    >The same applies to the restarted task: if a galera task fails and gets recreated, there is a moment where the
    container is already included in the pool of endpoint IDs but its mariaDB engine is still synchronising data
    from the "donor" database. If the app service task gets connected to such a newly started galera task,
    it may lead to an error like "no table found" because the table may not have been created by then.
    >
    >In both the above cases, "health checks" are not an easy fix (I guess because most of it is happening beyond the
    reach of "normal" monitoring services).
    
    Let's complete the initialization:
    
    `docker run --rm -it --network galera_net -e "DATABASE_URL=mysql://pollsuser:pollspass@galera/pollsdb" pythonincontainers/django-polls:nginx python manage.py loaddata initial_data.json`
    `docker run --rm -it --network galera_net -e "DATABASE_URL=mysql://pollsuser:pollspass@galera/pollsdb" pythonincontainers/django-polls:nginx python manage.py createsuperuser`
    
    Let's kill all tasks running on a particular node (called "draining" the node):
    
    `docker node update --availability drain swarm-wrk2`
    
    All tasks disappear and pop-up in other nodes in the visualizer:
    
    ![drain node in a stack](staticfiles/drained-node-in-a-stack.png)
    
    It can be reactivated again using: `docker node update --availability active swarm-wrk2`

    Let's remove the stack to cleanup: `docker stack rm django-polls`
    
93. Let's have a look at key features of docker swarm that impact software architecture and the way we code software
components:

    1. A complex application consists of many small software components which are deployed as groups of services i.e.
    the swarm stack.
    
    2. Such components must be packaged in docker images
    
    3. The images must be shipped to image registries so that the components can be delivered to final deployment
    runtime environment
    
    4. Containers using shared memory to communicate between containers require special attention to guarantee that
    both/all such containers end up on the same node (by default the node is selected randomly) and can share the
    memory segment.
    
    5. Docker swarm has no built-in mechanism to enable container in one node to access data in another container
    on another node.
    
    6. One container can be attached to one or more networks through its network interfaces.
    
    7. Within a container, one network interface is connected to one network and gets its unique IP (for each network).
    
    8. A container can be attached and detached to and from a network while running.
    
    9. Hostname is used inside the container. It may be different from 1) container name and 2) names in DNS records 
    associated to container IP addresses
    
    10. Environment Variables which are injected into containers first process by Docker engine. They are inherited
    by all processes spawned by it.
    
    11. Taking the above into consideration, a running container can be seen as a network server.
    
    12. The best way for a container to communicate with other containers is through an IP network.
    
    13. **If a container dies and gets restarted on another node, it loses access to the persistent volume attached to
    it in its original node. The new container will get a fresh volume. An application must be prepared to deal with
    such a problem.**
    
    14. If a service has one replica, other software components must have "patience" for it built into them. Like
    wait for a while before timeout, number of retries etc.
    
    15. Requests are spread among the service containers. We must consider this when programming the service.
    **Synchronisation** and proper **data transaction management** may be needed to handle parallel request processing.
    
    16. Container names in swarm:
    
    ![container names in swarm](staticfiles/container-names-in-swarm.png)
    
    17. Named templates can be used in hostnames, environment variables and volume options to define target directories.
    
    18. In case of a swarm stack, each service has two DNS records. It is visible under its full service name with stack
    name prefix as well as short service name as defined in compose file.
    
    19. Two service endpoint modes: vip (virtual IP assigned to the service) and dnsrr (DNS round robin).
    
    20. Docker swarm has support only IPv4 addresses (may change later).
    
    21. Docker volumes are simple. They can be created, attached to a container, detached and deleted. **Docker doesn't
    have volume operations like copy, clone, snapshot etc.**. Some plugins (3rd party) add such additional capabilities.
    
    22. Container filesystem is not designed to store large amounts of data or to deliver good write performance. We
    have volumes for that.
    
    23. Containers are meant to be short-lived by design
    
    24. Volumes are like a filesystem that can store files and folders (at least from the container's point of view).
    
    25. All volumes of a docker engine are stored at `/var/lib/docker/volumes`. This path is part of the docker host's
    root disk but a disk or disk volume can be mounted to it.
    
    26. So if we want to take advantage of advanced capabilities like SSD, snapshot etc., the node needs to have the
    required setup.
    
    27. In order to ensure that nodes with advanced volume capabilities are the ones where containers that need
    volumes are created, we can label them as such and define constraints.
    
    28. Removing a stack does not remove volumes. When it is redeployed, the volumes are reused.
    
    29. Multiple replicas running on one node share the named volume (defined in compose file). They must coordinate
    access to the volume in order to avoid data corruption.
    
    30. One common practice is to use persistent nodes in the global deployment mode (each node gets one container),
    add constraints so the "global" doesn't literally mean all nodes, only specific ones that satisfy the constraints.
    Yet another option commonly used in cloud-based nodes is to use dedicated storage solutions like AWS EBS or
    Azure Storage and mount these to the `/var/lib/docker/volume` for extra resiliency.
    
    31. This is how a label can be added: `docker node update --label-add com.example.disk=ssd swarm-wrk3`. This
    can then be used like this in the compose file for let's say the db service:
    
    ```yaml
    ...
    deploy:
      placement:
        constraints:
          - node.labels.com.example.disk == ssd
    ```
    
    32. Volumes must be removed explicitly by hand from each swarm cluster node. There is no one command for this.
    
    33. Don't use bind mounts in a swarm cluster.
    
    34. When the configs and secrets are updated in a running stack, the stack restarts those services using it.
    
    35. Swarm has health-checks (commands to be executed periodically to see how a container is doing). Such a health
    check has following parameters:
    
        - command: It is run like with `docker exec` command. A new process is created inside container to run it.
        Such a test is expected to complete quickly and return an exit code of 0 if it is healthy, 1 if it is
        unhealthy. All other codes are prohibited and may lead to unexpected results.
        - timeout: If command doesn't come back in this time, it is declared a fail. Default value is 30 seconds.
        - interval: Repeat interval
        - start_period: Time it approximately takes for the container to start. Default 0 seconds.
        - retries: number of times test command fails in a row before a container is declared unhealthy
        
    36. When a container becomes unhealthy, its IP is removed from service endpoint set and task is terminated. This
    leads to a new task being scheduled as defined in service restart policy.
    
    37. **HEALTHCHECK** is the keyword used in Dockerfile. Here's an example:
    
    ```shell
    FROM python:3.7.3
    WORKDIR /app
    COPY . .
    RUN pip install -r requirements.txt
    CMD ["python", "swarm-env.py"]
    HEALTHCHECK --interval=10s --timeout=3s --retries=2 \
      CMD curl -f -s http://127.0.0.1:5000/healthcheck || exit 1
    ```
    
    38. Application initialization often needs special attention. For example, the order in which services are deployed
    may be important but is not so simple to define that in docker swarm. Kubernetes has StatefulSets to accomplish
    that: https://kubernetes.io/docs/concepts/workloads/controllers/statefulset/#using-statefulsets

    39. If we don't use health-checks, containers start and immediately get included the service endpoint address pool,
    even if the application component is not ready to accept connections. Service code must be able to handle this.
    
    40. Health-checks shouldn't have circular dependencies i.e. service 1 waits for 2 to be ready but 2 waits for
    3 and 3 for 1. Then they'd all restart after a timeout and this could go on forever. My comment But done right, a
    dependency graph implemented in health checks may enable "ordered" deployment.
    
    41. Application initialization is indeed a complex topic. There may even be a separate controller module needed
    to coordinate a clean start.