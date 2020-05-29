# Section 2

1. `docker image pull python` : pulls the latest version of python

2. `docker container create --tty --interactive python`
	* `--tty`  basically makes the container start look like a terminal connection session. Use with `--interactive` flag.
	* `--interactive` interact with the container.
	* The first two options are used together like `-it` (their short hand versions)

3. `docker ps -a` or `docker container ps -a` or the **newest** `docker container ls -a` are the same.

4. The command executed in 3. shows all containers (without -a flag only active are shown). `STATUS` col. can have following values:
    * created
    * running or up
    * paused
    * exited
    * restarting
    * removing
    * dead

5. Docker names can be changed with `docker container rename <OLD_AUTO_NAME> <NEW_NAME>`

6. The command `docker container start <CONTAINER_NAME_OR_ID` has an `-i` flag but no `-t` flag.
The reason behind this is that once the container has been created, `start` command only starts it.
The `--tty` option must be defined at the creation time (tty literally stands for **teletypewriter** 
which was a name of device allowing you to type text and send it away in the same time)

    Explanation:

    >Docker `start` command will start any stopped container. 
    If you used docker `create` command to create a container, you can start it with the `start` command. 
    Docker `run` command is a combination of `create` and `start` as it creates a new container and starts it immediately.

7. Here are some docker command abbreviations:
    * `docker pull` == `docker image pull` 
    * `docker create` == `docker container create`
    * `docker start` == `docker container start`
    * `docker ps` == `docker container ps`
    * `docker rm` == `docker container rm`
    * `docker run` == `docker create; docker start` (two commands in one. see the last point #6)
    * `docker rmi` == `docker image rm`

8. So when doing development with docker, there are 3 options to transfer code to the Python container:
    * `git push` (to github) + `git clone` the repo inside the container. 
	   Reasonable solution for remote container (in cloud for example)
    * `docker cp` to copy files from host to inside the container (the command can do the other way around too).
    * mount the host folder using **docker volumes**. This is called the **bind mount** method.

9. `docker run -v <HOST_FOLDER_PATH>:<CONTAINER_FOLDER_PATH>`
    * `-v` or `--volume` mounts the host system's folder to the container
    * paths should be absolute not relative

    Examples:
    `docker run -it -v ${PWD}:/app python`
    `docker run -d -v ${PWD}:/data python`  (-d is for detach i.e. runs it in the background freeing the current screen)

10. It so happens that containers started above for example, start in the python interactive shell. If the shell is exited,
the container exits (i.e. stops). According to the official documentation, this is because **an exited container is 
a normal state for a container, when the main process running in it has exited.**

11. This means that scripts can be executed inside a container as follows (at the end of which the container will exit):

    `docker run -it --name baby_python -v ${PWD}:/app python python /app/myfirst.py`  (executes the myfirst.py)
    `docker start -i baby_python` (executing cmd above already saves the starting cmd i.e. `python /app/myfirst.py` into the 
container metadata so it is not needed next time.

    IMPORTANT NOTE:
    `docker run` by default attaches stdout and stderr so even skipping this flag `-it` shows the print out of python script.
    `docker start` by default attaches nothing so `-i` or `-a` flags are needed where they stand for interactive and attach resp.

12. A container image basically consists of 2 things:
    * filesystem - intialize content on the container's root disk
    * metadata - what and how to run when container starts

13. The start program definition (i.e. command that executes when the container is started) is divided into 2 parts:
    * Entrypoint - command that is **not ignored** when a container is starts with command line parameters
    * Command - command that wil be ignored if custom command line parameters are passed when starting a container
    * While entrypoint is not ignored, it can also be overridden using the `--entrypoint` flag (also creation time)

    For example, consider the following settings for some image:
    `ENTRYPOINT["echo", "one"]`
    `CMD["two", "three"]`

    If the container above is run (these are creation time things so I mean `run` **not** `start`), it executes the command
    `echo one two three`. However, if the container above is run with custom parameters like:

    `docker run -it <SOME_IMAGE_NAME> five six`

    this will execute:
    `echo one five six`

    So the `CMD` part of the parameters get overwritten.

14. `docker inspect` has a flag `--format` that can be used to see the JSON in a focused way. Here are the outputs for some images:

    * `docker inspect --format "ENTRYPOINT={{.Config.Entrypoint}} CMD={{.Config.Cmd}}" pythonincontainers/entrypoint:latest`
    
        outputs
    
        `ENTRYPOINT=[echo one] CMD=[two three]`

    * `docker inspect --format "ENTRYPOINT={{.Config.Entrypoint}} CMD={{.Config.Cmd}}" python`

        outputs
    
        `ENTRYPOINT=[] CMD=[python3]`

    * `docker inspect --format "ENTRYPOINT={{.Config.Entrypoint}} CMD={{.Config.Cmd}}" hello-world:latest`

        outputs
    
        `ENTRYPOINT=[] CMD=[/hello]`

15. `docker logs [--since <TIME>] <CONTAINER_NAME>` returns logs of stdout and stderr for a container (useful esp. those
running in detached mode i.e. in background). Here are some other options:
    * `-t` or `--timestamp` adds a timestamp
    * `--tail 3` shows the last 3 log lines
    * `-f` or `--follow` follows the log

16. `docker attach <CONTAINER_NAME>` is a small helper command that attaches the stdin, stdout and stderr to the terminal.
    * One thing is that once you're attached, doing `Ctrl+c` will close the main process, hence the app and kill the container
    * So the right way to detach is `Ctrl+p` followed by `Ctrl+q`

17. Docker by default creates the container with `--sig-proxy true` means certain control characters (like `Ctrl+c`) are
interpreted as signals. **`Ctrl+c` generates SIGINT which is interpreted by many apps a request to quit.**

18. Docker has a really cool feature of running an ad-hoc command inside a **running** container called `exec`. 
    For example, `docker exec <CONTAINER_NAME> ps -ef` returns all the processes inside the container. Another example,
    `docker exec -it <CONTAINER_NAME> bash` runs a bash terminal within the container.

19. Docker container can use up all of the system resources (CPU and RAM). For windows and mac os, the resources are limited
by the linux VM resources running on them however for Linux it really can take over the full system's resources. Hence,
to prevent that, the docker container can be run with parameters that limit the resources it is allowed to use. Examples:

    `docker run --memory 200m ...`  200mb of RAM
    
    `docker run -m 200m ...` 	200mb of RAM (basically showing the shorthand)
    
    `docker run -m 200m --memory-swap 300m` 200mb of RAM and 100mb of swap (offloading RAM to disk to free up RAM and re-reading it later) 
    
    `docker run -m 200m --memory-swap 200m` 200mb of RAM and **0mb** of swap (memory-swap is the total value of swap and memory so
    if it is the same, then no memory left for swap)

    **Note:** Not setting the flag means the swap memory is 2x memory. Explicitly setting it to `-1` means unlimited swap memory.

20. `docker stats` shows you the resource usage statistics of running containers.

21. Each container gets its own network stack. Under the default setting, all containers are connected to the same Virtual Network
Bridge and can communicate with each other using their internal IP addresses.

22. Docker allows the creation of **Virtual Network** and containers can be attached to it. Docker allows DNS name resolution
based on the container name (i.e. names act like URLs). It can be created as follows:

    `docker network create my-net`

    The container attachment looks like this:

    `docker run -d --network my-net <IMAGE_NAME>`  no -p flag since we're not interested in accessing this container directly from host.

    The DNS is dynamic i.e. containers created after a particular container also become visible/accessible to older ones too.

23. Other than make all containers join a network, another way of making the communicate with each other is called **Container
Linking**.

    `docker run --rm -it --link simple-flask:webserver <IMAGE_NAME>` 

    This adds `simple-flask` (i.e. the name) as well as its alias `webserver` is added to the `/etc/hosts` along with the internal
IP address automatically.

    This option `--link` is nearly identical to the option `--add-host` that looks like this:

    `docker run -it --add-host simple-flask:172.17.0.2 <IMAGE_NAME>`

    In this case also the value is added to the `/etc/hosts/` but the internal IP address must be found out first.

    KEY DIFFERENCE: linking carries over the env. variables over to the container it is being linked to but not in case `--add-host`.
    The env. variables all start with prefix `<ALIAS>_` (in this case `WEBSERVER_...`)

    NOTE: Container Linking has been marked as legacy feature so it will disappear in the future.

24. **Docker environment variables** can be set with `--env` or `-e` flag like this:

    `docker run -d --name postgres --network my-net --env "POSTGRES_PASSWORD=mysecret" postgres`

25. Side point: the command above starts the DB engine including the server. PgAdmin4 is an admin
tool to manage such postgres servers.

26. Networking is a core capability of docker containers.
    
    * Dockers are connected to the internet through the NAT (Network Address Translation).
    A NAT is used for assigning IP Addresses with a single host.
    
    This basically means that each docker container has a private IP address visible only locally.
    To the outside world, the host still has a *singular* IP address.
    
    * This means that docker containers can establish TCP connections to internet hosts.
    
    * The other way round i.e. if internet clients' want a TCP connection *to* the docker containers, this is
    directly not possible since publicly the clients see only one IP address (that of the host).
    
    * The way to address this issue (of establishing incoming connections to multiple containers running on a single 
    host), a port is exposed by the container that is then mapped on to the host's port. 
    This is called **Port Forwarding**.
    
    So any (internet) network node (client) with Host IP visibility can establish TCP connection to this mapped port
    and effectively access the docker container.
    
    * The default bridge network does not provide container name resolution (DNS resolution) i.e. no mapping
    of container names to IP Addresses. User-defined networks do.
    
27. **`docker network ls`**  - command to list all the available docker networks. Below is the one such output.
    The only one defined by the user is `my-net`. The other three are there by default. 

    | NETWORK ID   | NAME   | DRIVER | SCOPE    |
    |:-------------|:-------|:-------|:---------|
    |0e0df8d7fdba  | bridge | bridge | local    |
    |d70b60b019ab  | host   | host   | local    |
    |02b443b069d9  | my-net | bridge | local    |
    |77a99ff9e6b2  | none   | nan    | local    |
    
    * A network connected to `host` has *no network isolation*. All its published ports are directly visible in the
    host system. This is not really used in production.

28. `docker network create` allows us to create user-defined networks.

    * Docker uses the concept of **drivers** to extend its network capabilities. Several such drivers are available
    built-in, others can be install as network plug-ins.
    
    * `bridge` is the default network driver
    
    * `macvlan` creates a network where containers look like separate physical devices with their own MAC addresses.
    Supporting hardware setup is needed (so-called promiscuous mode). Not very commonly used.
    
    *`overlay` is very important. It allows for creation of network across several docker runtimes (or several hosts).
    It has the scope of a **swarm** rather than individual hosts (or to be more precise individual docker engines).
    With `docker machine` several docker runtimes can be run on a single host. These simulate a swarm on a single host
    as well and would do well with the `overlay` driver.
    
29. `docker container ps --filter network=<NETWORK_NAME>` Docker containers connected to a single network can be listed 
with this command. The command is useful if docker doesn't let you remove a network because of attached containers.

30. `docker network connect <NETWORK_NAME> <CONTAINER_NAME>` to connect a container to another network. The containers
of this network become visible to this newly joined container.

    To disconnect, `docker network disconnect <NETWORK_NAME> <CONTAINER_NAME>`
    
31. `docker network create --internal <NETWORK_NAME>` creates a network that can let containers joining it be visible
to each other but has no internet connectivity. This is useful if a potentially suspicious image is being run.

