# Section 3

1. Very generally it can be said that following are the elements of a python project:

    1. Application code
    2. Libraries and dependencies
    3. Data
    4. Networks, DNS Hostnames and IP Addresses
    5. Configuration Files
    6. Environment Variables
    
2. What is the impact of containerization of a Python project on its lifecycle?

    1. Architecture and Design:
    Nearly any application, regardless of its architecture principles, can be encapsulated in a
    container.
    
    Container can be run like a VM (an anti-pattern but works) but most importantly fits wonderfully
    into a microservices architecture.
    
    2. Project initialization:
    If some kind of a full stack framework (like Django) is used, it is setup before coding can begin.
    
    Over here there are two options:
        
        1. Setup the framework in your coding env. (such that code also runs on your laptop) and then 
        later use the containers for testing, integration and deployment.
        
        2. Setup the framework directory structure that is then mounted on a container (running in
        interactive mode) to run the code even during the active development part.
        
    3. Coding:
    Developing tools (like IDEs) on the host system are used in this phase in most cases.
    
    4. Creating images:
    Host docker runtimes are used to create images most often.
    
    This is not the only way though. Github and Gitlab can be integrated to use web hooks to
    automatically create an image upon `git push` of Python code (in the Dockerhub).
    
    An excellent webhook explanation can be found in the knowledge folder of this repo.
    
    5. Testing & Debugging in development:
    Since containers run on the host system can run a range of software including ready-made database,
    message queues, memory caches etc., a lot can be tested locally before triggering the CI/CD
    pipeline
    
    6. Deployment Planning and Automation:
    Today we can take full advantage of Docker Compose or Kubernetes YAML files to take full
    advantage of the automated deployment.
    
    Deployment scripts are now a key part of an application and are stored along with the source code 
    in a VCS (version control system).
    
    Automated, containerized app deployment pairs well with IaaS to bring full DevOps capability.
    
    7. Integration & Deployment in Testing Environment:
    Deployment automation leads to great simplification in Integration and Deployment in *test*
    environments.
    
    All we need is a Docker Swarm or Kubernetes cluster, offering similar environment to production,
    enable honest and dependable testing of complete application and its deployment.
    
    **Containers are great for blurring the line between Test and Production Environments.**
    
    8. Shipping the App:
    Once the app components are packaged into container images and deployment scripts, it is ready
    to be shipped.
    
    Images go to the registry (Dockerhub, Azure Container Registry etc.) and deployment scripts
    to a suitable repository.
    
    9. Deployment in production:
    There are tools and services available (or can be setup) that make this a breeze.
    
    Tools like orchestration engines like Kubernetes and managed container services (also running
    kubernetes) for the management of containers.
    
    Same deployment script is used for production and testing.

    9. Updating and Upgrading:
    
    First the difference between the two:
    
    > A software update includes bug fixes, and other small improvements, while a software upgrade changes the version 
    of a software.

    If we want to change our application code, we build a **new version** of the image including changed
    code and then recreate and restart the container in production with this new image.
    
    This is a major change in how application are upgraded and updated now.
    
    But this has far reaching consequences. 
    
    E.g.Data stored inside of a container will be lost when a new image version is released. 
    So persistent data volumes must be used and other similar practices.
    
3. Some design principles for a production-grade containerized applications:

    1. There should be one component running in one container (can be a db engine, 
    reverse proxy server etc.) But running a db cluster in one container is NOT ok.
    
    2. Architect apps for horizontal scaling i.e. adding more nodes adds more capacity as opposed
    to upgrading the hardware.
    
    3. Most apps in such a setup are accessed with HTTP/HTTPS nowadays. Load balances and reverse
    proxies take the job of ingesting the request and routing to proper application server.
    
    4. Single node database is enough for development env. but a high availability cluster is preferred
    for test and production.
    
    Switching from a single node to a cluster doesn't require change in the application servers,
    at least for the most popular database engines.
    
    5. Async. message queues enrich the inter-container communication with the possibility of
    decoupling an event of sending a message or a request from one application component and the
    event of receiving a message by another application component.
    
    Such a decoupling provides better separation of components and allows independent scaling
    of container groups implementing each.
    
    6. Service mesh frameworks make it easier to run distributed, containerized apps. Istio is one
    example. Difference between kubernetes and istio is not clear.
    
    7. Design application observability as early as possible in the development.
    
    8. Related points to observability. Pland and implement:
        
        1. Application log management
        2. Performance monitoring
        3. Container platform monitoring
        
    9. Understanding what is going on a distributed, loosely coupled application is a demanding task.
    
    10. Extensive logging is key.
    
    11. Logs must be collected, stored and available for searching and analysis. This is the job of
    an application log management software. 
    
    Elastic Logging (ELK) or Splunk are two examples of such software that can be deployed in
    containers.
    
    Start log management early in development and use the same tools later in production and
    testing.
    
    Public cloud log management tools also provide great experience.
    
    13. Implement good security framework in the containerized application. Good basics:
    
        1. Securing Service Endpoints with data encryption, both external and internal
        2. Have an application firewall
        3. Local trusted registry to protect images from prying eyes
        4. Check public images being used from a security viewpoint
        5. Include security experts from the start
        6. Securely manage all secrets
        
    14. Plan and develop automated application deployment process as early as possible in the
    development cycle.
        
    15. Application initialization is a major task and should be done very early in the development
    process.
    
    16. **Make containers immutable and disposable** Dont run shell commands in containers. Update the
    image and redeploy!
    
    17. Data storage management architecture should be included in application design early.
    
    18. Same goes for data communication/flow architecture and strategy.
    
    19. We can enforce zero trust policy for communication even between app. components.
    
    20. Make small images. Fast and secure.
    
    21. Use well-designed image tagging system.
    
    22. Plan how will upgrades and updates be rolled out.
    
4. How to build an image in a manual way?

    1. Let's start with creating a folder `manual-build` and some flask code inside in a file `hello.py`
    
    2. `env FLASK_APP=hello.py flask run` can be used to run the flask web server at port 5000 (default
    port). But this way the app is accessible only through the container's primary network interface.
    
    3. To bind the app to all interfaces we can set the run host to 0.0.0.0
    
    4. We can do all these settings in a shell script that looks like this:
    
    ```bash
    # start-app.sh
    cd /app
    export FLASK_APP="hello"
    export FLASK_ENV="development"
    export FLASK_RUN_HOST="0.0.0.0"
    flask run
    ```
   
    5. Now let's create a container and do some things manually:
    
        1. `docker create -it --name manual -p 5000:5000 python /bin/sh`
        
        2. `docker start -i manual`
        
        3. `mkdir app`
        
        4. Exit the container and then do `docker cp hello.py manual:/app` to copy file to app folder
        of the container called `manual`
        
        5. Now copy the shell script: `docker cp start-app.sh manual:/app`
        
        6. Start the container again (exiting bash stopped the container) and verify:
        
            `ls -l /app`
        
        7. Set the execution flag on the script: `chmod +x start-app.sh`
        
        8. Install flask in the container: `pip install flask`
        
        9. Start the app: `/app/start-app.sh`
        
        10. Check the output from the browser `localhost:5000`
        
            Here is a demo:
        
            ![manual build steps](staticfiles/manual-build.svg)
        
        11. Now it is time to turn out container into an image. The command for that is
        
            `docker commit <CONTAINER NAME OR ID> <NEW IMAGE NAME:TAG>`
            
            So for us this means:
            
            `docker commit manual manual-image:1.0`
            
        12. Now let's test this container:
        
            `docker rum --rm -it -p 5000:5000 manual-image:1.0`
            
            (bash automatically starts since the image has inherited that from our container)
            
            `# /app/start-app.sh`
            
            and voila! it works!
            
        13. So we had to execute the shell script myself. How to automatically execute it when the
        container starts?
        
            `docker commit --change "CMD /app/start-app.sh" manual manual-image:1.0`
            
            This sets a command to be executed by default. The update can be seen more closely using
            `docker image inspect manual-image:1.0`
            
            and scrolling to this part:
            
            ```
            "Cmd": [
                "/bin/sh",
                "-c",
                "/app/start-app.sh"
            ],
            "Image": "python",
            "Volumes": null,
            "WorkingDir": "",
            "Entrypoint": null,
            "OnBuild": null,
            "Labels": {}
            ```
            
            this shows that the docker `CMD` keyword gets converted to `-c` argument and 
            `/app/start-app.sh` becomes the second part of the argument.
            
5. The Docker Build tool helps with image creation automation. It has two major components:
    
    1. **Dockerfile**: instructions to be followed. Almost like a script.
    2. **Context**: fileystem directory on the host to used as a source of files and subdirs to build
    the new image.
   
   Docker file is expected to be in the context.

6. So the first Dockerfile step by step:

    1. `FROM python` chooses python as the base image
    
    2. `WORKDIR /app` create the dir if it doesnt exist and changes it to the
    curr dir.
    
    3. `COPY hello.py .` and `COPY start-app.sh .` copy files to the `.` i.e. current working directory
    (`/app`) in the container
    
    4. `RUN pip install flask` runs the command as a shell command. 
    
    5. `CMD ["bin/bash", "start-app.sh"]` executes this as the startup command. There can only be one CMD instruction 
    in a Dockerfile. If you list more than one, all but the last one are ignored.
    
    **The main purpose of CMD is to provide defaults for executing the container.**
    
    The **`CMD`** has 3 forms that can be read [here](https://docs.docker.com/engine/reference/builder/#cmd)
    
    6. So this completes the Dockerfile.
    
7. To build the actual image do:

    `docker build -t automated-image:1.0 .`
    
    where `-t` is used to add name and tag and `.` is the context dir.
    
    Here's the demo:
    
    ![docker automated build](staticfiles/docker-build-with-dockerfile.svg)
    
8. As an improvement, we are going to take the `export ...` commands out of the startup shell script
and make it part of the Dockerfile. This has two advantages:

    1. Transparency increases so that it can be seen which env. variables are set
    2. The env. variables are accessible also to the container building the image
    
9. The new Dockerfile looks like this:

    ```docker
    WORKDIR /app
    COPY hello.py .
    RUN pip install flask
    ENV FLASK_APP "hello"
    ENV FLASK_ENV "development"
    ENV FLASK_RUN_HOST "0.0.0.0"
    CMD ["flask", "run"]
    ```

    Now we don't need the startup script anymore. Since we saved this in Dockerfile.env we need this
    command to build the new image:
    
    `docker build -f Dockerfile.env -t automated-image:1.1 .`
    
    where the `-f` flag allows passing a non-default Dockerfile name.
    
10. Dockerfile has a very easy format. Each line is either a command or a comment. Dockerfile allows empty lines. The
comment starts with a `#` symbol (like in Python) and the remaining text is ignored. Notice, this only works at the
beginning of the line.

11. The commands all start with a keyword written in CAPITAL letters.

12. Putting a command before the first FROM, you get an error there is no stage in the context. There is an exception
to this ARG. Will be covered later. ARG parameterizes the Dockerfile.

13. `FROM` defines the base image. Everything is inherited from it incl. volumes, env. vars, filesystem etc.

    When Docker Build encounters a `FROM` command, it creates an intermediate build container based on the base image.
    
    Examples:
    - `FROM python` will assume `latest` tag and building from such a base image may mean a different python because lets
    say a new python version may get released (3.9) for example, and will be given this tag.
    
    - `FROM ubuntu:16.04` will take specifically the version tagged `16.04` and even if the maintainers fix some
    security vulnerabilities in the image, (because that is indicated in the 3rd version number), the ubuntu version
    will remain the same.
    
    - `FROM python@sha256:7e6c00cc553fdce06c1bcfcbf34c73a0f3623a8fc9ce88c8...` accesses a very specific image using
    its image digest.
    
    As for how a digest of an image is calculated: digest equals the SHA256 of the config.json file.
    
    - `FROM docker.elastic.io/elasticsearch/elasticsearch:7.0.0` uses image hosted in `docker.elastic.io` not in 
    Dockerhub.
    
    - `FROM private-registry.mycompany.com:5000/my-python-3` takes the image from a private registry
    
    After all the commands in the Dockerfile are executed, the lat intermediate build container is saved to a local
    image cache and named according to the `-t` flag.
    
    A small concrete example of a Dockerfile:
    
    `FROM python:3.7.4` one reason to "duplicate" a base image is to freeze it for later.
    
    **Dockerfile can include several lines of `FROM` command**. It is called a multi-stage build.
    
    Finally, you can also start from scratch i.e. use an empty image as the base.
    
14. `WORKDIR` sets the working directory for the rest of the Dockerfile or until the next `WORKDIR` is encountered.

    Before the first time it is used, the "default" working dir is that of the base image and is usually the root
    directory of the filesystem.
    
    Example: `WORKDIR /app` where if `/app` doesn't exist, it will be created. Doing a `WORKDIR subdir` now will set 
    the dir to `/app/subdir`.
    
    The path of `WORKDIR` can be absolute or relative. In case of relative, it is "resolved" first.
    
14. `COPY` is used to copy files from the host filesystem to the filesystem of a newly created image.

    Examples:
    - `COPY hello.py /app/hello.py`
    - `COPY hello.py start-app.sh /app/`
    - `COPY /hello.py /very/long/path/`
    - `COPY *.py sources/`
    - `COPY . /app/`
    - `COPY ["name with spaces.py", "/app"]`
    
    In case of two or more files in a `COPY` command, the destination must be a directory and its name must end with 
    a `/`. See the second example above.
    
    The absolute path of your resources refers to an absolute path within the build context, not an absolute path on 
    the host. That is why the 3rd example refers to the same `hello.py` as the first two. This means if you want to
    copy files into the image filesystem from elsewhere in your host, they must first be copied into the context folder.
    
    Wildcards like `*` for zero or more characters and `?` for zero or 1 characters work. Wildcard substitution works
    using the GO language `filepath.Match` fucntion.
    
    `COPY` will also create the directory if it is not available (and all the subdirectories). If the last character
    is slash, this means it is a directory and the source and destination file names remain the same. Skipping the slash
    means the file gets renamed to the text after the last slash.
    
    `COPY hello.py /path/to/dir` will copy hello.py to dir `/path/to` and rename the python script to to `dir`.
    
    `.` is equivalent to `/` so `COPY . /app` is equal to `COPY / /app`.
    
    Finally we can pass a list of argument with each path in quotes.
    
    If we would like certain unnecessary files like Dockerfile itself to not be copied we can use the
    **`.dockerignore`** file.
    
    Here is a sample `.dockerignore`:
    
    ```docker
    Dockerfile*
    *.pyc
    !important.pyc
    #this is a comment
    ```
    
    So any file or folder beginning with `Dockerfile` is ignored. So is every file ending with `.pyc` except 
    `important.pyc`. The last line is a comment.
    
    If the files to be copied are fewer than exceptions we can do this:
    
    ```docker
    *
    !mysite
    !mysite_nginx.conf
    ```
    
    This excludes everything except one folder `mysite` and one config file `mysite_nginx.conf`.
    
    `COPY` command can be used with the option `--chown=`. This sets the destination file or directory owner to
    specified User ID and Group ID.
    
    Examples:
    - `COPY --chown=web:web html/ /usr/local/html/`
    - `COPY --chown=root . .`
    - `COPY --chown=100:100 hello.py /app/`
 
    What each means:
    1. `html` folder copied. Each file within the copied folder has "web" as the owner and "web" as the group.
    2. entire context is copied. Everything belongs to root.
    3. `hello.py` is copied and owned by user with ID 100 and a group with ID 100.
    
    The user IDs and user groups are maintained using `/etc/passwd` and `/etc/group` and if these don't exist, the
    build aborts with an error.
    
15. `ADD` is very similar to `COPY` with the exception of one: it can two more types of sources

    1. a local TAR file -> gets extracted at the destination dir
    2. a URL pointing to a remote file. Example:
    `ADD https://raw.githubusercontent.com/shabie/flask-hello/flask-hello.py /app`
    
    Other than this, ADD works like COPY but docker recommendation is for COPY since the word is more transparent.
    
16. A side point. Paths other than the current folder can also be used as context. Such paths can both be relative
or absolute. Dockerfile must be part of the context. Hell, even a url can be used:

    `docker build -t flask-hello https://github.com/pythonincontainers/flask-hello.git`
    
    The context can also be a TAR Archive, which gets uncompressed before being used as context with Docker Build.

17. `RUN` is used to execute commands in the **intermediate container** not the final one. It has two forms:

    1. `RUN command arg1 arg2`
    2. `RUN ["command", "arg1", "arg2"]`
    
    The first one runs the command with a shell. Shell msut be available already. `/bin/sh -c` for linux images
    and `cmd /S /C` for windows images.
    
    The second one is of the form `docker exec`. It takes a JSON array with the first array element being the executable
    command and the others being the arguments.
    
    `RUN` only takes non-interactive commands. Attempting to take user input leads to build failure.
    
    The shell form provides a lot of flexibility. Here are some example of redirects we can take advantage of:
    
    ```
    FROM python
    RUN echo "This is multiline" > /tmp/file
    RUN echo "message" >> /tmp/file
    RUN more /tmp/file
    ```
    
    The build output snippet will look like this:
    
    ```shell
    Step 2/4 : RUN echo "This is multiline" > /tmp/file
     ---> Running in ba930fb526a3
    Removing intermediate container ba930fb526a3
     ---> 7e0515e6dbcb
    Step 3/4 : RUN echo "message" >> /tmp/file
     ---> Running in 3ac3d51d1a06
    Removing intermediate container 3ac3d51d1a06
     ---> 105457f45b97
    Step 4/4 : RUN more /tmp/file
     ---> Running in 2537188affc4
    ::::::::::::::
    /tmp/file
    ::::::::::::::
    This is multiline
    message
    ```
    
    Here's another one:
    ```
    FROM python
    RUN find / -name "python*" | wc -l
    ```
    
    This is how to output looks like:
    
    ```
    shabie:~/Projects/containers/section3/dockerfile-run(master)$ docker build -t pip -f Dockerfile.pipe .
    Sending build context to Docker daemon  3.072kB
    Step 1/2 : FROM python
     ---> 659f826fabf4
    Step 2/2 : RUN find / -name "python*" | wc -l
     ---> Running in e47ec334b082
    148
    Removing intermediate container e47ec334b082
     ---> e9d88af938a0
    Successfully built e9d88af938a0
    Successfully tagged pip:latest
    ```
    
    A fine point is that pipe command works in such a way that commands before the last pipe are executed in a separate
    shell process, and the last one in the current shell. Build continues if the last command i.e. the command executed
    in the current shell exits with error 0 even if the prior commands in the piped chain fail.
    
    Bash allows error propagation but standard shell does not. So if you wanna set bash instead of standard shell, here
    is the line to add in Dockerfile:
    
    **`SHELL ["/bin/bash", "-c"]`**
    
    Hell, we can even do this in a Dockerfile i.e. set python as default executor of RUN:
    
    ```
    FROM python
    SHELL ["/usr/local/bin/python", "-c"]
    RUN print("Hello at build time")
    ```
    
    So the output snippet:
    
    ```
    Step 2/3 : SHELL ["/usr/local/bin/python", "-c"]
     ---> Running in 318b073a9ba7
    Removing intermediate container 318b073a9ba7
     ---> 0392b8a938b8
    Step 3/3 : RUN print("Hello at build time")
     ---> Running in d984a320c3ac
    Hello at build time
    ```
   
    One thing to remember: each RUN is executed in a different intermediate container. A consequence of this is that
    this won't work as expected:
    
    ```
    FROM python
    RUN export VAR=foo
    RUN echo $VAR
    ```
    
    This won't work because the VAR environment variable was set in another container not accessible to the shell
    executing the echo part. (It is a different story if the env. vars. were set using ENV).
    
    Shell variables like `$VAR` etc. are only to be used in the shell form. JSON array form does not resolve them.
    
    Note: Running background processes of shell don't work well during build. Because they spawn new processes for which
    docker build doesn't wait.
    
    `RUN` is used to install software or download data and config files from external servers. This is its most common
    **usage pattern**.
    
    ```
    FROM python
    RUN apt-get update && apt-get install -y default-mysql-client
    RUN mysql --version
    RUN pip install Django mysqlcleint
    ```
    
18. A word on image layers. Every line of `COPY`, `ADD` and `RUN` leads to a new layer of filesystem which the docker
build also saves in its image cache.

    Why store it in cache? So it can be used again when it is being rebuilt. Re-building the exact container, lines
    like these can be seen:
    
    ```
   Step 2/3 : SHELL ["/usr/local/bin/python", "-c"]
     ---> Using cache
     ---> 0392b8a938b8
    Step 3/3 : RUN print("Hello at build time")
     ---> Using cache
     ---> c80b8d3364e9
    Successfully built c80b8d3364e9
    ```
    
    So it is recommended to pack group all logical RUN commands into one. Here is an example:
    
   ```
    FROM python
    RUN apt-get update && apt-get install -y default-mysql-client
    RUN pip install Django mysqlcleint pandas numpy
    ``` 
   
    So the side effect is that when no linux installations are changed, the cached image will be reused. Same goes
    for python libraries. If the libraries are the same, this step completes very quickly when re-building the image
    in the future. Of course we can use the `requirements.txt` to the same effect.
    
19. Now we discuss modification of new image metadata. Let's start with `ENV` command.

    Image Metadata contains the list of environment variables. They are available to all subsequent Dockerfile commands
    as well as obviously the container(s) based on the final image of that Dockerfile.
    
    `ENV` can be defined in two ways:
    
    1. `ENV name value`
    2. `ENV name1=value1 name2=value2 ...`
    
    `ENV` also allows variable substitution. Here's a classic example of appending path:
    
    `ENV PATH $PATH:/app`
    
    Since paths in `PATH` are separated by `:`, it takes the old value of `PATH` variables and appends `:/app` to it.
    
    The downside of the `ENV PATH $PATH:/app` is that if `PATH` is empty, `:/app` gets appended which is incorrect.
    
    Solution to this? Use BASH brace syntax with 2 modifiers (the only 2 allowed) since they are supported by Docker 
    Interpreter.
    
    Q. What is brace syntax?
    
    `echo a{d,c,b}e` outputs `ade ace abe`. This is brace syntax.
    
    Q. What are modifiers and which ones are supported?
    
    * `${parameter:-word}`
      If parameter is unset or null, the expansion of word is substituted. Otherwise, the value of parameter is 
      substituted.
     
    * `${parameter:+word}`
      If parameter is null or unset, nothing is substituted, otherwise the expansion of word is substituted.
    
    Here are two examples:
    
    1. `ENV PATH "${PATH}${PATH:-/bin}:/app"` this renders `PATH` to `/bin:/app` if PATH is empty or unset.
    2. `ENV PATH "${PATH}${PATH:+:}/app"` this renders `PATH` to `/app` if PATH is empty or unset.
    
    Environment variables cannot be unset in Dockerfile. They can be set to empty string `ENV EMPTY ""`. Unset or
    empty string are for most practical purposes equivalent.
    
    Env. vars can be altered or set when running a container using the `--env` or `-e` flag and then using `var=value`
    format. Several variables setting means using `-e` flag several times.
    
19. Linux base images lack user authentication system. This means commands in containers are executed with superuser
privileges by default. This applies to the build process as well. All commands are executed with superuser powers
as well. 

    Some need root access like `RUN apt-get install ...` but others don't.
    
    `USER` command changes the user to the provided User ID. This setting then applies to all subsequent commands as
    well as the start command. Let's try this. Here's a Dockerfile:
    
    ```
    FROM python
    RUN groupadd mysqlgrp && useradd -g mysqlgrp mysql
    USER mysql
    RUN id
    ```
    
    The 2nd command first adds a group called `mysqlgrp` and then adds the user `mysql` to the group. The `-g` flag just
    passes the name of the group that must already exist. Building the image outputs this:
    
    ```
    Step 4/4 : RUN id
    ---> Running in 9e518458c7be
    uid=1000(mysql) gid=1000(mysqlgrp) groups=1000(mysqlgrp)
    ```
    
    We can even later run a container based on the image to see the output of command `id`:
    
    ```shell
    shabie:~$ docker run --rm user id
    uid=1000(mysql) gid=1000(mysqlgrp) groups=1000(mysqlgrp)
    ```
    
    Finally, `USER mysql:root` changes the group of the ID from `mysql` to now `root`.
    
20. `LABEL` -> container can have arbitrary number of labels. Labels themselves are not mandatory.

    Example dockerfile with multiple labels:
    ```
    FROM python
    LABEL maintainer=shabie@whatever.com
    LABEL com.mycompany.version="0.7"
    LABEL com.mycompany.production="true"
    ```
    
    The labels can be seen through `docker inspect` and can also be used as filter as follows:
    
    * `docker images --filter "label=com.mycompany.production"` which just uses a part of it    
    * `docker images --filter "label=com.mycompany.production=true"` which uses all of it