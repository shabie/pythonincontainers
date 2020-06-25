# Section 4

1. How to ship python app image?

    a. Export container into TAR archive using `docker export`. Send it over. Import the container using
       `docker import` with some other parameters needed to import the image into the docker engine cache.
       
    b. `docker save` to save a repositories with multiple tags and images. `docker load` loads all the images. This is
       potentially one way of shipping full set of images in a multi-container application.
    
    c. Use image registries like **`Dockerhub`** or from other cloud providers. `docker push` and `docker pull` are
       two commands associated with this variant.
    
    d. We can also run a local(alized) image registry i.e. on a company level, department level etc.
    
2. Here's an example of how `docker save` can be used:

    ```shell
    shabie:~flask-hello(master)$ docker image ls postgres
    REPOSITORY          TAG                 IMAGE ID            CREATED             SIZE
    postgres            latest              b97bae343e06        13 days ago         313MB
    shabie:~flask-hello(master)$ docker image ls django-polls:uwsgi4nginx 
    REPOSITORY          TAG                 IMAGE ID            CREATED             SIZE
    django-polls        uwsgi4nginx         213f3da1a717        2 days ago          985MB
    shabie:~flask-hello(master)$ docker image ls mynginx
    REPOSITORY          TAG                 IMAGE ID            CREATED             SIZE
    mynginx             lb                  99d7e3d34d23        2 days ago          111MB
    mynginx             ssl                 e294d10b30f5        2 days ago          111MB
    mynginx             latest              b614f3aa8792        2 days ago          111MB
    shabie:~flask-hello(master)$ docker save -o images.tar postgres django-polls:uwsgi4nginx mynginx
    shabie:~flask-hello(master)$ ls -lrth
    total 1,4G
    -rw------- 1 shabie shabie 1,4G Jun 22 21:40 images.tar
    ```
   
   The generated file can now be read in another docker runtime using `docker load -i /tmp/images.tar`
   
   
   
   