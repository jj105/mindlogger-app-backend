This is how I configured the deploy of my rails apps to AWS Elastic Beanstalk through CircleCI 1.0. 

If you are using the Circle CI 2.0, take a look at this [article](https://gist.github.com/ryansimms/808214137d219be649e010a07af44bad) from [ryansimms](https://gist.github.com/ryansimms)

#### Configure Environments Variables

On Project Settings > Environment Variables add this keys:
- AWS_ACCESS_KEY_ID 
- AWS_SECRET_ACCESS_KEY   
The aws user must have the right permissions. This can be hard, maybe, [this](https://gist.github.com/RobertoSchneiders/c9ee659cc5a565642fd9) can help you.

#### Create a bash script to create the eb config file

./setup-eb.sh
```bash
set -x
set -e

mkdir /home/ubuntu/.aws
touch /home/ubuntu/.aws/config
chmod 600 /home/ubuntu/.aws/config
echo "[profile eb-cli]" > /home/ubuntu/.aws/config
echo "aws_access_key_id=$AWS_ACCESS_KEY_ID" >> /home/ubuntu/.aws/config
echo "aws_secret_access_key=$AWS_SECRET_ACCESS_KEY" >> /home/ubuntu/.aws/config
```

#### Configure circle.yml

Add the awsebcli dependency:
```yaml
dependencies:
  pre:
    - sudo apt-get update
    - sudo apt-get install python-dev
    - sudo pip install awsebcli
```

Add the deployment config:
```yaml
deployment:
  production:
    branch: master
    commands:
      - bash ./setup-eb.sh
      - eb deploy
```
* If your deploy user don't have the `elasticbeanstalk:DescribeEvents` permission, the `eb deploy` will run for ever. CircleCI will cancel it after 10 minutes and break the build with timeout. 

#### Create the EB Cli config file

`eb init` will create this file for you. However, if you don't want to run it, you can simply create and configure this file manualy:

./elasticbeanstalk/config.yml
```yaml
branch-defaults:
  master:
    environment: you-environment-name
global:
  application_name: your-application-name
  default_ec2_keyname: ec2-key-pair-name
  default_platform: 64bit Amazon Linux 2015.03 v1.4.3 running Ruby 2.2 (Puma)
  default_region: sa-east-1
  profile: eb-cli
  sc: git
```


