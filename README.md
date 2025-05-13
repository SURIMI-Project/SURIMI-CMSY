# SURIMI CMSY++ model
This is the CMSY++ repo.
It holds the source code of the SURIMI CMSY model

After that, the 'proto' subdirectory will be filled with the contents of the SURIMI-protocol Git repo.

## How to re-generate the python proxy files from the protobuf files

In the subdirectory \surimi\v1\ a collection of python files exist. These files are generated from the protobuf files of the proto submodule. Follow the procedure below to re-generate them when the protobuf files change.
```bash
C:\Users\<user>\source\repos\SURIMI-CMSY> python -m grpc_tools.protoc -Iproto --python_out=. --grpc_python_out=. --pyi_out=. proto/surimi/v1/*.proto
```

## How to create a docker image, run it and push it

Create a docker image from the Dockerfile in the root of the repository. The image will be tagged with the name 'cmsy' and the tag 'latest'. The image will be created in the current directory.
### Create
Start Docker Desktop and make sure it is running. Then run the following command in the command line:

```bash
C:\Users\<user>\source\repos\SURIMI-CMSY>docker build -f Dockerfile . -t cmsy:latest
```
### Run
To run it, execute the following command. You can then connect Postman to http://localhost:12360 and send messages to the container

```bash
C:\Users\<user>\source\repos\SURIMI-CMSY>docker run -p 12360:50201 cmsy:latest
```

### Push
After the image is created, you can push it to a docker registry. The following command will push the image to the docker hub. Make sure you are logged in to the docker hub before running this command.
As an example the rikkert242/cmsy image is used. You can change this to your own docker hub username and image name.
```bash
C:\Users\<user>\source\repos\SURIMI-CMSY>docker push rikkert242/cmsy:latest
```


# SURIMI


The European Union’s (EU) Mission ‘Restore our Ocean and Waters’ by 2030, aims to preserve ocean health and biodiversity while also promoting a sustainable blue economy. In support of this goal, the EU is developing the European Digital Twin of the Ocean (EU DTO), a virtual model of the ocean that integrates vast amounts of data to provide a comprehensive, real-time understanding of the complex and dynamic ocean system.

SURIMI is a 3-year project (2024-2027) that will feed into the EU DTO. SURIMI’s mission is to build partnerships with stakeholders from industry, science, policy, and society to develop nine socio-ecological models for integration into the EU DTO. With access to ecological and fisheries data alongside economic and social data, SURIMI will use Large Language Models to improve the EU DTO’s ability to support informed decision-making and policy development in marine management strategy evaluation analyses in European waters.


## Links

- [Project website](www.surimi-project.eu)
- [Twitter](https://x.com/surimi_project)
- [LinkedIn](https://www.linkedin.com/company/surimi-project/)