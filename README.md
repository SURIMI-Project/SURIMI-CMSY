# SURIMI CMSY++ model
This is the CMSY++ repo.
It holds the source code of the SURIMI CMSY model

## gRPC interface in Buf Schema Registry
The gRPC interface is descibed by  protobuf files that are stored in https://github.com/Official-EwE/SURIMI-protocol
So there are no proto files in the project!

The proto files are also stored in  https://buf.build/surimi/surimi-protocol

## Watch out! Check that you are using the SDK version v1.70.1!!
You have to use version "v1.10.1" of the grpc/python SDK.
More recent versions give trouble with the protobuf version in combination with Open Telemetry. But only when you create a docker image from it.

To use the interface in this Python project you have to use the generated proxy files. These files are imported as a "pip" package.

When you want to install a new version of the gRPC interface you go to https://buf.build/surimi/surimi-protocol/sdks/main:grpc/python?version=v1.70.1
Copy the line, but without the "python3 -m " part and run in in a terminal.


For example
```bash
PS C:\Users\Rik\source\repos\SURIMI-CMSY> pip install surimi-surimi-protocol-grpc-python==1.70.1.1.20250626155734+d9c7c394022e --extra-index-url https://buf.build/gen/python
```

The layout of the version number is explained in https://buf.build/docs/bsr/generated-sdks/python/?h=python#full-syntax


Remember to also update the requirements file.txt.

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
C:\Users\<user>\source\repos\SURIMI-CMSY>docker run -p 12360:5020 cmsy:latest
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