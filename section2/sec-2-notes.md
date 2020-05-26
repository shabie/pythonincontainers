# Section 2

1. `docker image pull python` : pulls the latest version of python

2. `docker container create --tty --interactive python`
	a. `--tty`  basically makes the container start look like a terminal connection session. Use with `--interactive` flag.
	b. `--interactive` interact with the container.
	c. The first two options are used together like `-it` (their short hand versions)

3. `docker ps -a` or `docker container ps -a` or the **newest** `docker container ls -a` are the same.

4. The command executed in 3. shows all containers (without -a flag only active are shown). `STATUS` col. can have following values:
	a. created
	b. running
	c. paused
	d. exited
	e. restarting
	f. removing
	g. dead

5. Docker names can be changed with `docker container rename <OLD_NAME> <NEW_NAME>`

6. The command `docker container start <CONTAINER_NAME_OR_ID` has an `-i` flag but no `-t` flag.
The reason behind this is that once the container has been created, `start` command only starts it.
The `--tty` option must be defined at the creation time (tty literally stands for **teletypewriter** 
which was a name of device allowing you to type text and send it away in the same time)

Explanation:

>Docker `start` command will start any stopped container. 
>If you used docker `create` command to create a container, you can start it with the `start` command. 
>Docker `run` command is a combination of `create` and `start` as it creates a new container and starts it immediately.

7. Here are some docker command abbreviations:
	a. `docker pull` == `docker image pull` 
	b. `docker create` == `docker container create`
	c. `docker start` == `docker container start`
	d. `docker ps` == `docker container ps`
	e. `docker rm` == `docker container rm`
	f. `docker run` == `docker create; docker start` (two commands in one. see the last point #6)
	g. `docker rmi` == `docker image rm`

8. So when doing development with docker, there are 3 options to transfer code to the Python container:
	a. `git push` (to github) + `git clone` the repo inside the container. 
	   Reasonable solution for remote container (in cloud for example)
	b. `docker cp` to copy files from host to inside the container (the command can do the other way around too).
	c. mount the host folder using **docker volumes**. This is called the **bind mount** method.

9. `docker run -v <HOST_FOLDER_PATH>:<CONTAINER_FOLDER_PATH>`
	a. `-v` or `--volume` mounts the host system's folder to the container
	b. paths should be absolute not relative

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
	a. filesystem - intialize content on the container's root disk
	b. metadata - what and how to run when container starts

13. The start program definition (i.e. command that executes when the container is started) is divided into 2 parts:
	a. Entrypoint - command that is **not ignored** when a container is starts with command line parameters
	b. Command - command that wil be ignored if custom command line parameters are passed when starting a container
	c. While entrypoint is not ignored, it can also be overridden using the `--entrypoint` flag (also creation time)

For example, consider the following settings for some image:
`ENTRYPOINT["echo", "one"]`
`CMD["two", "three"]`

If the container above is run (these are creation time things so I mean run **not** start), it executes the command
`echo one two three`. However, if the container above is run with custom parameters like:

`docker run -it <SOME_IMAGE_NAME> five six`

this will execute:
`echo one five six`

So the `CMD` part of the parameters get overwritten.

14. `docker inspect` has a flag `--format` that can be used to see the JSON in a focused way. Here are the outputs for some images:

`docker inspect --format "ENTRYPOINT={{.Config.Entrypoint}} CMD={{.Config.Cmd}}" pythonincontainers/entrypoint:latest`
outputs
`ENTRYPOINT=[echo one] CMD=[two three]`

`docker inspect --format "ENTRYPOINT={{.Config.Entrypoint}} CMD={{.Config.Cmd}}" python`
outputs
`ENTRYPOINT=[] CMD=[python3]`

`docker inspect --format "ENTRYPOINT={{.Config.Entrypoint}} CMD={{.Config.Cmd}}" hello-world:latest`
outputs
`ENTRYPOINT=[] CMD=[/hello]`

15. `docker logs [--since <TIME>] <CONTAINER_NAME>` returns logs of stdout and stderr for a container (useful esp. those
running in detached mode i.e. in background). Here are some other options:
	a. `-t` or `--timestamp` adds a timestamp
	b. `--tail 3` shows the last 3 log lines
	c. `-f` or `--follow` follows the log

16. `docker attach <CONTAINER_NAME>` is a small helper command that attaches the stdin, stdout and stderr to the terminal.
	a. One thing is that once you're attached, doing Ctrl+c will close the main process, hence the app and kill the container
	b. So the right way to detach is Ctrl+p, Ctrl+q

17. Docker by default creates the container with `--sig-proxy true` means certain control characters (like Ctrl+c) are interpreted
as signals. **Ctrl+c generates SIGINT which is interpreted by many apps a request to quit.**

18. Docker has a really cool feature of running an ad-hoc command inside a **running** container called `exec`. For example,
`docker exec <CONTAINER_NAME> ps -ef` returns all the processes inside the container. Another example,
`docker exec -it <CONTAINER_NAME> bash` runs a bash terminal within the container.


19. Docker container can use up all of the system resources (CPU and RAM). For windows and mac os, the resources are limited
by the linux VM resources running on them however for Linux it really can take over the full system's resources. Hence,
to prevent that, the docker container can be run with parameters that limit the resources it is allowed to use. Examples:

`docker run --memory 200m ...`  200mb of RAM
`docker run -m 200m ...` 	200mb of RAM (basically showing the shorthand)
`docker run -m 200m --memory-swap 300m` 200mb of RAM and 100mb of swap (offloading RAM to disk to free up RAM and re-reading it later) 
`docker run -m 200m --memory-swap 200m` 200mb of RAM and **0mb** of swap (memory-swap is the total value of swap and memory so
if it is the same, then no memory left for swap)

Note: Not setting the flag means the swap memory is 2x memory. Explicitly setting it to -1 means unlimited swap memory.

20. `docker stats` shows you the resource usage statistics of running containers.

