# Section 1 Notes

Section 1 notes are very informal and brief. Proper notes begin from section 2.

1. `docker run -it -rm -p 5001:5000`
	* `it` - Takes you straight inside the container. These are 2 tags  `-i` (for interactive) and `-t` (for tty).
	   Well it doesn't really take you *inside* but allows for execution of commands that take input from the terminal
	   to be executed.
	* `rm` - Automatically remove the container when it exits
	* `-p 5001:5000` - Publish port. Binds container's port 5000 to host's 5001

2. docker adds a thin writeable layer to each container based on an image.
So let's say we have 2 containers using the same base image. One of the containers
actually writes a log file to its filesystem. This gets written into this thin
writeable layer. Later when this particular container is deleted, only the thin
layer is deleted and the read-only parts of the image **(shared between all containers
that use this image)** remains intact.

    This also highlights one of the differences of **image container** and **container runtime**.

3. Images can be built manually:
    1. run a base linux image in interactive shell mode
	2. install python, pip, packages etc.
	3. copy application source code into the container
	4. test and verify
	5. **freeze** the container **to create a new image**
	6. tag the image 

4. Images built like in 3. can get complicated and you won't remember all steps
you did. This is where tools enabling automated container image builds come in with
`docker build` together with the *Dockerfile* declarative scripting being the most
common one.

5. After the image is built, it is still residing in your development system.
It needs to be shipped to an **image registry** to make it available to be pulled
into a *destination runtime system*. Dockerhub is the most popular example of such
a registry.

6. Container best practices involve keeping each one simple and small to serve just
a single purpose.

7. On windows and mac, the docker engine (or simply docker) runs inside a linux VM.

8. Docker desktop is a family of tools that docker offers incl. swarm, machine,
compose etc.

9. Docker is for nerds. It is a command line tool. Some GUIs exist but not really
the focus for docker.

10. Each container gets a **unique IP address** assigned dynamically by Container
Runtime.

11. However by default, the containers running on the host are **not visible** to
the host i.e. the IP addresses of the containers are not reachable.

12. So if a container is to be accessed from the host, we have to **explicitly expose**
one or more of the container's network ports and **map** them to the selected host
network ports. This is called **port forwarding**.

    More importantly, the IP addresses of these containers are largely unhelpful because
while the machine may look (to the outside world) as if it has a **same** IP address
(because it does), a whole range of different *ports* (and not *IP addresses*) on the host machine can be mapped 
onto individual containers.

13. Difference between `RUN` and `CMD` keywords of Dockerfile is that `RUN` is used to
execute a command as a part of building the image. `CMD` commands are to be executed
when the container is started i.e. at container runtime. So `CMD` just updates the
meta data of the image. It makes no "real" change to the image itself.

14. Interestingly, the build process of the image takes place in a temporary container
itself.

15. `docker build -t myimage:1.0 .`
	* `-t` flag is for tagging the image
	* `.` sets the **image context** to current directory

    This above TAGS the image. Then there is an option of naming the runtime container
    instance which is different from tag. For example,

    `docker run -it --name mycontainerinstance myimage`

    starts a container instance called `mycontainerinstance` that can be viewed from
    `docker ps -a`.

16. The two commands below stop and remove ALL containers (running and stopped).

    `docker stop $(docker ps -a -q)`

    `docker rm $(docker ps -a -q)`
